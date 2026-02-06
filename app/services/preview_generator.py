"""
Lovable Build-with-URL API wrapper.
Generates redesign preview websites for leads.

Real mode: Uses Lovable API (endpoint TBD — needs research)
Mock mode: Returns a mock preview URL.

NOTE: The Lovable API may have limitations. This service is built with a clean
interface so it can be swapped for another provider (Framer, raw HTML by Claude, etc).
"""

import random
import string
import httpx
from app.config import get_settings


def _generate_slug(business_name: str) -> str:
    """Generate a URL-friendly slug from business name."""
    slug = business_name.lower()
    slug = slug.replace(" ", "-")
    # Remove non-alphanumeric chars except hyphens
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    slug = slug.strip("-")
    return slug[:50]  # Cap length


def _build_prompt(
    business_name: str,
    business_type: str,
    city: str,
    phone: str | None,
    issues: list[str],
    priorities: list[str],
) -> str:
    """Generate the prompt to send to Lovable for site generation."""
    phone_cta = f'"Bel ons: {phone}"' if phone else '"Neem contact op"'

    return f"""Create a modern, mobile-first website for {business_name}, a {business_type} in {city}, Netherlands.

Requirements:
- Hero section with business name and a clear {phone_cta} call-to-action button
- Services section highlighting typical {business_type} services
- About section with trust signals (years of experience, service area)
- Contact section with phone, address, and a simple contact form
- Footer with business hours and service area
- Color scheme: professional, clean (use blues/whites for trust)
- Language: Dutch
- Mobile-first responsive design
- Fast-loading, minimal JavaScript

Style: Modern, clean, professional. NOT generic template-looking.
Think: what would make a {business_type} owner say "wow, this is exactly what I need"
"""


async def generate_preview(
    lead_id: int,
    business_name: str,
    business_type: str,
    city: str,
    phone: str | None,
    issues: list[str] | None = None,
    priorities: list[str] | None = None,
) -> dict:
    """
    Generate a preview website for the lead.
    Returns dict with preview_url, preview_prompt, preview_status.
    """
    settings = get_settings()
    prompt = _build_prompt(
        business_name, business_type, city, phone,
        issues or [], priorities or [],
    )

    if settings.mock_mode or not settings.lovable_api_key:
        return _mock_generate(lead_id, business_name, prompt)

    return await _real_generate(lead_id, business_name, prompt)


async def _real_generate(lead_id: int, business_name: str, prompt: str) -> dict:
    """
    Generate via Lovable API.
    NOTE: This is a placeholder — actual API endpoints need to be verified.
    """
    settings = get_settings()
    slug = _generate_slug(business_name)

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.lovable.dev/v1/projects",
                headers={
                    "Authorization": f"Bearer {settings.lovable_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": prompt,
                    "title": business_name,
                },
            )
            response.raise_for_status()
            data = response.json()

        return {
            "preview_url": data.get("url", f"https://{slug}.{settings.preview_domain}"),
            "preview_prompt": prompt,
            "preview_status": "ready",
        }

    except Exception as e:
        print(f"Preview generation failed for lead {lead_id}: {e}")
        return {
            "preview_url": None,
            "preview_prompt": prompt,
            "preview_status": "failed",
        }


def _mock_generate(lead_id: int, business_name: str, prompt: str) -> dict:
    """Return mock preview data for development."""
    settings = get_settings()
    slug = _generate_slug(business_name)
    mock_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))

    return {
        "preview_url": f"https://{slug}-{mock_id}.{settings.preview_domain}",
        "preview_prompt": prompt,
        "preview_status": "ready",
    }
