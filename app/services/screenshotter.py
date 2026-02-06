"""
ScreenshotOne API wrapper.
Captures screenshots of business websites for AI analysis.

Real mode: Uses ScreenshotOne API (GET https://api.screenshotone.com/take)
Mock mode: Creates a placeholder screenshot image.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import httpx
from app.config import get_settings

SCREENSHOTS_DIR = Path(__file__).parent.parent / "static" / "screenshots"


async def capture_screenshot(lead_id: int, website_url: str) -> str | None:
    """
    Capture a screenshot of the given website URL.
    Returns the relative path to the saved screenshot, or None on failure.
    """
    settings = get_settings()
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if settings.mock_mode or not settings.screenshotone_access_key:
        return _mock_screenshot(lead_id, website_url)

    return await _real_screenshot(lead_id, website_url)


async def _real_screenshot(lead_id: int, website_url: str) -> str | None:
    """Capture via ScreenshotOne API."""
    settings = get_settings()

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://api.screenshotone.com/take",
                params={
                    "access_key": settings.screenshotone_access_key,
                    "url": website_url,
                    "viewport_width": 1280,
                    "viewport_height": 800,
                    "format": "png",
                    "full_page": "false",
                    "delay": 3,
                },
            )
            response.raise_for_status()

        filepath = SCREENSHOTS_DIR / f"{lead_id}.png"
        filepath.write_bytes(response.content)
        return f"/static/screenshots/{lead_id}.png"

    except Exception as e:
        print(f"Screenshot failed for lead {lead_id}: {e}")
        return None


def _mock_screenshot(lead_id: int, website_url: str) -> str:
    """Create a placeholder screenshot image for development."""
    img = Image.new("RGB", (1280, 800), color=(240, 240, 245))
    draw = ImageDraw.Draw(img)

    # Draw a simple mock website layout
    # Header bar
    draw.rectangle([0, 0, 1280, 80], fill=(51, 51, 51))
    draw.text((40, 25), f"Mock: {website_url or 'No website'}", fill=(255, 255, 255))

    # Nav bar
    draw.rectangle([0, 80, 1280, 120], fill=(70, 70, 70))

    # Content area
    draw.rectangle([40, 150, 800, 350], fill=(220, 220, 230))
    draw.text((60, 200), "Hero Section - Outdated Design", fill=(100, 100, 100))

    # Sidebar
    draw.rectangle([840, 150, 1240, 500], fill=(230, 230, 235))
    draw.text((860, 180), "Sidebar Content", fill=(120, 120, 120))

    # Footer
    draw.rectangle([0, 720, 1280, 800], fill=(51, 51, 51))
    draw.text((40, 745), "Footer - Missing Contact Info", fill=(180, 180, 180))

    # Watermark
    draw.text((400, 400), f"MOCK SCREENSHOT (Lead #{lead_id})", fill=(200, 200, 210))

    filepath = SCREENSHOTS_DIR / f"{lead_id}.png"
    img.save(filepath)
    return f"/static/screenshots/{lead_id}.png"
