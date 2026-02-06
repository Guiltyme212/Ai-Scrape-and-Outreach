"""
Pipeline orchestrator.
Runs the full lead processing pipeline: scrape → screenshot → analyze → preview → email.
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.services import scraper, screenshotter, analyzer, preview_generator, email_writer


async def run_pipeline(
    db: Session,
    niche: str,
    location: str,
    limit: int = 20,
    campaign_name: str | None = None,
) -> dict:
    """
    Run the full pipeline for a given niche and location.
    Returns summary stats.
    """
    stats = {
        "scraped": 0,
        "analyzed": 0,
        "previews_generated": 0,
        "emails_drafted": 0,
        "errors": [],
    }

    # Create campaign
    if not campaign_name:
        campaign_name = f"{niche.title()} {location} {datetime.utcnow().strftime('%b %Y')}"

    campaign = Campaign(
        name=campaign_name,
        niche=niche,
        location=location,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    # Step 1: Scrape businesses
    businesses = await scraper.scrape_businesses(niche, location, limit)
    stats["scraped"] = len(businesses)

    for biz in businesses:
        lead = Lead(
            campaign_id=campaign.id,
            business_name=biz["business_name"],
            business_type=biz["business_type"],
            address=biz["address"],
            city=biz["city"],
            phone=biz["phone"],
            email=biz["email"],
            website_url=biz["website_url"],
            google_maps_url=biz["google_maps_url"],
            rating=biz["rating"],
            reviews_count=biz["reviews_count"],
            status="scraped",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        try:
            await _process_lead(db, lead)

            if lead.site_score is not None:
                stats["analyzed"] += 1
            if lead.preview_status == "ready":
                stats["previews_generated"] += 1
            if lead.email_body:
                stats["emails_drafted"] += 1

        except Exception as e:
            error_msg = f"Lead {lead.id} ({lead.business_name}): {e}"
            stats["errors"].append(error_msg)
            lead.status = f"error"
            db.commit()
            print(f"Pipeline error: {error_msg}")
            continue

    # Update campaign stats
    campaign.total_scraped = stats["scraped"]
    campaign.total_qualified = stats["analyzed"]
    db.commit()

    return stats


async def process_single_lead(db: Session, lead_id: int) -> dict:
    """Process a single lead through the pipeline (for retry/manual trigger)."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return {"error": "Lead not found"}

    try:
        await _process_lead(db, lead)
        return {"status": "ok", "lead_id": lead.id, "lead_status": lead.status}
    except Exception as e:
        return {"error": str(e), "lead_id": lead.id}


async def _process_lead(db: Session, lead: Lead):
    """Process a single lead through all pipeline steps."""
    min_score = 50  # from config, but kept simple here

    # Step 2: Screenshot (only if they have a website)
    if lead.website_url:
        screenshot_path = await screenshotter.capture_screenshot(lead.id, lead.website_url)
        lead.screenshot_url = screenshot_path
        db.commit()

        # Step 3: Analyze
        analysis = await analyzer.analyze_website(
            lead.id, lead.business_name, lead.business_type, lead.city, screenshot_path,
        )
        lead.site_score = analysis.get("score")
        lead.site_issues = json.dumps(analysis.get("issues", []))
        lead.analysis_summary = analysis.get("summary", "")
        lead.status = "analyzed"
        db.commit()

        # Skip leads with good websites
        if lead.site_score and lead.site_score >= min_score:
            return
    else:
        # No website = hot lead, score 0
        lead.site_score = 0
        lead.site_issues = json.dumps(["No website exists"])
        lead.analysis_summary = "This business has no website at all — prime opportunity."
        lead.status = "analyzed"
        db.commit()

    # Step 4: Generate preview
    issues = json.loads(lead.site_issues) if lead.site_issues else []
    preview = await preview_generator.generate_preview(
        lead.id, lead.business_name, lead.business_type, lead.city, lead.phone,
        issues=issues,
    )
    lead.preview_url = preview["preview_url"]
    lead.preview_prompt = preview["preview_prompt"]
    lead.preview_status = preview["preview_status"]
    if lead.preview_status == "ready":
        lead.status = "preview_ready"
    db.commit()

    # Step 5: Write email
    email = await email_writer.write_email(
        lead.business_name, lead.business_type, lead.city,
        lead.website_url, lead.site_score, issues, lead.preview_url,
    )
    lead.email_subject = email["subject"]
    lead.email_body = email["body"]
    lead.email_status = "draft"
    lead.status = "email_drafted"
    db.commit()
