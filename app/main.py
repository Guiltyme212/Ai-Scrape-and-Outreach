"""
LeadPilot — FastAPI application with routes and template rendering.
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import get_settings
from app.database import get_db, init_db
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.services import pipeline, email_sender
from app.scheduler import init_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    init_db()
    init_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="LeadPilot", lifespan=lifespan)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# ── Jinja2 filters ──────────────────────────────────────────────────
def json_loads_filter(value):
    """Parse JSON string in templates."""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


templates.env.filters["from_json"] = json_loads_filter


# ── Landing Page ─────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    """Public landing page."""
    return templates.TemplateResponse("landing.html", {"request": request})


# ── Dashboard ────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    campaign_id: int | None = None,
    status: str | None = None,
    score_max: int | None = None,
):
    """Main dashboard with leads table and stats."""
    settings = get_settings()

    # Query leads with optional filters
    query = db.query(Lead)
    if campaign_id:
        query = query.filter(Lead.campaign_id == campaign_id)
    if status:
        query = query.filter(Lead.status == status)
    if score_max is not None:
        query = query.filter(Lead.site_score <= score_max)

    leads = query.order_by(Lead.created_at.desc()).all()
    campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).all()

    # Compute stats
    total_leads = db.query(func.count(Lead.id)).scalar()
    total_analyzed = db.query(func.count(Lead.id)).filter(Lead.site_score.isnot(None)).scalar()
    total_previews = db.query(func.count(Lead.id)).filter(Lead.preview_status == "ready").scalar()
    total_sent = db.query(func.count(Lead.id)).filter(Lead.email_status == "sent").scalar()
    total_replied = db.query(func.count(Lead.id)).filter(Lead.email_status == "replied").scalar()
    total_closed = db.query(func.count(Lead.id)).filter(Lead.status == "closed").scalar()

    stats = {
        "total_leads": total_leads,
        "total_analyzed": total_analyzed,
        "total_previews": total_previews,
        "total_sent": total_sent,
        "total_replied": total_replied,
        "total_closed": total_closed,
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "leads": leads,
        "campaigns": campaigns,
        "stats": stats,
        "settings": settings,
        "filters": {
            "campaign_id": campaign_id,
            "status": status,
            "score_max": score_max,
        },
    })


# ── Lead Detail ──────────────────────────────────────────────────────

@app.get("/leads/{lead_id}", response_class=HTMLResponse)
async def lead_detail(request: Request, lead_id: int, db: Session = Depends(get_db)):
    """Single lead detail view."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return HTMLResponse("<h1>Lead not found</h1>", status_code=404)

    issues = []
    if lead.site_issues:
        try:
            issues = json.loads(lead.site_issues)
        except json.JSONDecodeError:
            issues = []

    return templates.TemplateResponse("lead_detail.html", {
        "request": request,
        "lead": lead,
        "issues": issues,
    })


# ── Settings ─────────────────────────────────────────────────────────

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page with API key status and config."""
    settings = get_settings()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": settings,
        "api_status": settings.api_status(),
    })


# ── API Routes ───────────────────────────────────────────────────────

@app.post("/api/pipeline/run")
async def run_pipeline_route(
    niche: str = Form(None),
    location: str = Form(None),
    limit: int = Form(20),
    db: Session = Depends(get_db),
):
    """Trigger the pipeline via dashboard button."""
    settings = get_settings()
    niche = niche or settings.default_niche
    location = location or settings.default_location

    stats = await pipeline.run_pipeline(db, niche, location, limit)
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/api/leads/{lead_id}/reprocess")
async def reprocess_lead(lead_id: int, db: Session = Depends(get_db)):
    """Re-run pipeline on a single lead."""
    result = await pipeline.process_single_lead(db, lead_id)
    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)


@app.post("/api/leads/{lead_id}/send")
async def send_lead_email(lead_id: int, db: Session = Depends(get_db)):
    """Send the drafted email for a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead or not lead.email_body:
        return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)

    to_email = lead.email or "test@example.com"  # fallback for mock mode
    result = await email_sender.send_email(to_email, lead.email_subject, lead.email_body, lead.id)

    if result.get("status") == "sent":
        lead.email_status = "sent"
        from datetime import datetime
        lead.email_sent_at = datetime.utcnow()
        lead.status = "sent"
        db.commit()

    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)


@app.post("/api/leads/{lead_id}/update-email")
async def update_lead_email(
    lead_id: int,
    subject: str = Form(...),
    body: str = Form(...),
    db: Session = Depends(get_db),
):
    """Update the email draft for a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if lead:
        lead.email_subject = subject
        lead.email_body = body
        db.commit()
    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)


@app.post("/api/batch/send")
async def batch_send(db: Session = Depends(get_db)):
    """Send all approved/drafted emails."""
    leads = db.query(Lead).filter(
        Lead.email_status == "draft",
        Lead.email_body.isnot(None),
    ).all()

    sent_count = 0
    for lead in leads:
        to_email = lead.email or "test@example.com"
        result = await email_sender.send_email(to_email, lead.email_subject, lead.email_body, lead.id)
        if result.get("status") == "sent":
            lead.email_status = "sent"
            from datetime import datetime
            lead.email_sent_at = datetime.utcnow()
            lead.status = "sent"
            sent_count += 1

    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)
