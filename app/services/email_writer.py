"""
Claude API email writer.
Generates personalized cold emails in Dutch for each lead.

Real mode: Uses Anthropic Claude API
Mock mode: Returns realistic mock email content.
"""

import json
import random
import anthropic
from app.config import get_settings

EMAIL_PROMPT = """You are writing a cold outreach email in Dutch for a web design agency.

Target: {business_name}, a {business_type} in {city}
Their current website: {website_url}
Website score: {site_score}/100
Key issues: {issues}
Preview redesign URL: {preview_url}

Write a SHORT (max 150 words), personalized cold email in Dutch that:
1. Opens with something specific about THEIR business (not generic)
2. Mentions 1-2 specific issues with their current site (be tactful, not insulting)
3. Links to the preview redesign you already built for them
4. Ends with a soft CTA: "Wil je even kijken? Ik hoor graag wat je ervan vindt."
5. Feels human, not salesy. Like a helpful neighbor, not a pushy vendor.

Tone: Casual-professional Dutch. No "Geachte", use "Hoi {{business_name}}"
Subject line: Short, curiosity-driven, personalized

Return ONLY a JSON object (no markdown, no extra text):
{{
    "subject": "...",
    "body": "..."
}}"""


MOCK_EMAILS = [
    {
        "subject": "Ik heb iets voor {name} gebouwd",
        "body": "Hoi {name},\n\nIk kwam jullie website tegen en viel me op dat het design wat gedateerd oogt en de contactgegevens lastig te vinden zijn op mobiel.\n\nUit nieuwsgierigheid heb ik een modern alternatief in elkaar gezet — speciaal voor jullie:\n{preview}\n\nGeen verplichtingen, gewoon even kijken. Wil je even kijken? Ik hoor graag wat je ervan vindt.\n\nGroet,\nLeadPilot Team",
    },
    {
        "subject": "Een nieuw jasje voor {name}?",
        "body": "Hoi {name},\n\nToen ik jullie website bekeek viel me op dat deze niet optimaal werkt op telefoons en de laadtijd wat lang is.\n\nIk heb alvast een voorbeeld gemaakt van hoe het eruitzien kan:\n{preview}\n\nHet is vrijblijvend — ik ben benieuwd naar jullie reactie. Wil je even kijken? Ik hoor graag wat je ervan vindt.\n\nVriendelijke groet,\nLeadPilot Team",
    },
    {
        "subject": "Jullie website kan zoveel meer doen",
        "body": "Hoi {name},\n\nAls {type} in {city} doen jullie duidelijk goed werk — dat zie ik aan de reviews. Maar eerlijk gezegd doet jullie website dat niet helemaal recht.\n\nIk heb een gratis redesign-voorbeeld voor jullie gemaakt:\n{preview}\n\nWil je even kijken? Ik hoor graag wat je ervan vindt.\n\nGroeten,\nLeadPilot Team",
    },
]


async def write_email(
    business_name: str,
    business_type: str,
    city: str,
    website_url: str | None,
    site_score: int | None,
    issues: list[str] | None,
    preview_url: str | None,
) -> dict:
    """
    Generate a personalized cold email for the lead.
    Returns dict with subject and body.
    """
    settings = get_settings()

    if settings.mock_mode or not settings.anthropic_api_key:
        return _mock_email(business_name, business_type, city, preview_url)

    return await _real_email(
        business_name, business_type, city,
        website_url, site_score, issues, preview_url,
    )


async def _real_email(
    business_name: str,
    business_type: str,
    city: str,
    website_url: str | None,
    site_score: int | None,
    issues: list[str] | None,
    preview_url: str | None,
) -> dict:
    """Generate email via Claude API."""
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = EMAIL_PROMPT.format(
        business_name=business_name,
        business_type=business_type,
        city=city,
        website_url=website_url or "No website",
        site_score=site_score or "N/A",
        issues=", ".join(issues) if issues else "No analysis available",
        preview_url=preview_url or "Not yet generated",
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        result_text = response.content[0].text
        return json.loads(result_text)

    except Exception as e:
        print(f"Email writing failed for {business_name}: {e}")
        return {
            "subject": f"Re: {business_name}",
            "body": f"Email generation failed: {e}",
        }


def _mock_email(
    business_name: str,
    business_type: str,
    city: str,
    preview_url: str | None,
) -> dict:
    """Return realistic mock email content."""
    template = random.choice(MOCK_EMAILS)
    preview = preview_url or "https://preview.example.com"

    return {
        "subject": template["subject"].format(name=business_name),
        "body": template["body"].format(
            name=business_name,
            type=business_type,
            city=city,
            preview=preview,
        ),
    }
