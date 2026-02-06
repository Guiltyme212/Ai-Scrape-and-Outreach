"""
Claude API website analyzer.
Sends a screenshot to Claude and gets a design score + issues list.

Real mode: Uses Anthropic Claude API with vision
Mock mode: Returns realistic mock analysis data.
"""

import base64
import json
import random
from pathlib import Path
import anthropic
from app.config import get_settings

SCREENSHOTS_DIR = Path(__file__).parent.parent / "static" / "screenshots"

ANALYSIS_PROMPT = """You are a web design expert analyzing a small business website.
Look at this screenshot of {business_name} ({business_type} in {city}).

Score the website 1-100 on these criteria:
- Mobile readiness (does it look like it would work on mobile?)
- Visual design (modern vs outdated)
- Clear call-to-action (phone number, contact form visible?)
- Loading speed indicators (heavy images, cluttered layout?)
- Trust signals (reviews, certifications, about section?)
- SEO basics (clear headings, readable text?)

Return ONLY a JSON object (no markdown, no extra text):
{{
    "score": 35,
    "issues": [
        "Issue 1",
        "Issue 2"
    ],
    "summary": "Brief summary of the website quality",
    "redesign_priorities": ["priority 1", "priority 2"]
}}"""


MOCK_ISSUES = [
    "Outdated design from early 2010s",
    "No visible phone number above the fold",
    "No mobile-responsive layout",
    "Missing call-to-action button",
    "No Google reviews or trust signals shown",
    "Slow-loading due to unoptimized images",
    "Missing SSL certificate (no HTTPS)",
    "No clear service descriptions",
    "Cluttered navigation menu",
    "Missing business hours",
    "No contact form visible",
    "Broken image links detected",
    "Text too small to read on mobile",
    "No social media links",
    "Generic stock photos only",
]

MOCK_PRIORITIES = [
    "mobile-first layout",
    "prominent phone CTA",
    "modern clean design",
    "trust signals",
    "clear service descriptions",
    "fast loading speed",
    "SEO-friendly structure",
    "professional photography",
]


async def analyze_website(
    lead_id: int,
    business_name: str,
    business_type: str,
    city: str,
    screenshot_path: str | None,
) -> dict:
    """
    Analyze a website screenshot with Claude AI.
    Returns dict with score, issues, summary, redesign_priorities.
    """
    settings = get_settings()

    if settings.mock_mode or not settings.anthropic_api_key:
        return _mock_analyze(business_name, business_type, city)

    return await _real_analyze(lead_id, business_name, business_type, city, screenshot_path)


async def _real_analyze(
    lead_id: int,
    business_name: str,
    business_type: str,
    city: str,
    screenshot_path: str | None,
) -> dict:
    """Analyze via Claude API with vision."""
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = ANALYSIS_PROMPT.format(
        business_name=business_name,
        business_type=business_type,
        city=city,
    )

    messages_content = []

    # Add screenshot if available
    if screenshot_path:
        img_path = SCREENSHOTS_DIR / f"{lead_id}.png"
        if img_path.exists():
            img_data = base64.b64encode(img_path.read_bytes()).decode("utf-8")
            messages_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_data,
                },
            })

    messages_content.append({"type": "text", "text": prompt})

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": messages_content}],
        )

        result_text = response.content[0].text
        return json.loads(result_text)

    except Exception as e:
        print(f"Analysis failed for lead {lead_id}: {e}")
        return {
            "score": None,
            "issues": [],
            "summary": f"Analysis failed: {e}",
            "redesign_priorities": [],
        }


def _mock_analyze(business_name: str, business_type: str, city: str) -> dict:
    """Return realistic mock analysis data."""
    score = random.randint(15, 55)
    num_issues = random.randint(3, 6)
    issues = random.sample(MOCK_ISSUES, num_issues)
    priorities = random.sample(MOCK_PRIORITIES, min(4, len(MOCK_PRIORITIES)))

    summary = (
        f"The {business_type} website for {business_name} in {city} scores {score}/100. "
        f"It has a {'severely ' if score < 30 else ''}outdated design that likely "
        f"{'loses significant customers' if score < 30 else 'could be improved'} on mobile. "
        f"Key issues include {issues[0].lower()} and {issues[1].lower()}."
    )

    return {
        "score": score,
        "issues": issues,
        "summary": summary,
        "redesign_priorities": priorities,
    }
