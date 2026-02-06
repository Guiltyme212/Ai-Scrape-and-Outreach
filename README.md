# LeadPilot — AI-Powered Outreach Pipeline

Automated outreach pipeline that finds businesses with bad websites, analyzes them with AI, generates redesign previews, and sends personalized cold emails.

## Pipeline

```
SCRAPE → FILTER → ANALYZE → GENERATE PREVIEW → PERSONALIZE EMAIL → SEND → TRACK
```

1. **Scrape** business listings from Google Maps (Outscraper API)
2. **Filter** for businesses with bad/missing websites
3. **Analyze** current website with Claude AI (screenshot scoring)
4. **Generate Preview** redesign via Lovable API
5. **Personalize** cold email per lead via Claude AI
6. **Send** emails via Instantly.ai
7. **Track** opens, clicks, replies in dashboard

## Tech Stack

- **Backend**: Python 3.12+ / FastAPI
- **Frontend**: Jinja2 + HTMX + Pico CSS
- **Database**: SQLite via SQLAlchemy
- **Task Queue**: APScheduler
- **APIs**: Outscraper, ScreenshotOne, Anthropic Claude, Lovable, Instantly.ai

## Quick Start

```bash
# Clone and install
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
uvicorn app.main:app --reload
```

Open http://localhost:8000 to see the dashboard.

## Project Structure

```
app/
├── main.py              # FastAPI app + routes
├── config.py            # Pydantic Settings
├── database.py          # SQLAlchemy setup
├── models/              # Lead + Campaign models
├── services/            # API integrations + pipeline
├── templates/           # Jinja2 HTML templates
├── static/              # CSS + screenshots
└── scheduler.py         # APScheduler batch jobs
```

## License

Private — All rights reserved.
