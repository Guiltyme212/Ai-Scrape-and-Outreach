"""Netlify deployer — deploy a single HTML file as a static site."""

import io
import re
import zipfile
import httpx

from leadpilot.config import settings

NETLIFY_API = "https://api.netlify.com/api/v1"


def _slugify(name: str) -> str:
    """Convert a business name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    slug = slug.strip("-")[:40]
    return f"preview-{slug}" if slug else "preview-site"


def _create_zip(html_content: str) -> bytes:
    """Create an in-memory zip file containing index.html."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.html", html_content)
    return buffer.getvalue()


def deploy_to_netlify(html_content: str, business_name: str) -> str:
    """Deploy an HTML file to Netlify and return the live URL.

    Creates a new site with a slug derived from the business name,
    uploads the HTML as a zip, and returns the URL.
    """
    slug = _slugify(business_name)
    zip_data = _create_zip(html_content)

    headers = {
        "Authorization": f"Bearer {settings.netlify_api_token}",
    }

    # Create a new site
    create_resp = httpx.post(
        f"{NETLIFY_API}/sites",
        headers={**headers, "Content-Type": "application/json"},
        json={"name": slug},
        timeout=30,
    )

    if create_resp.status_code == 422:
        # Name taken — append a short suffix
        import time
        slug = f"{slug}-{int(time.time()) % 10000}"
        create_resp = httpx.post(
            f"{NETLIFY_API}/sites",
            headers={**headers, "Content-Type": "application/json"},
            json={"name": slug},
            timeout=30,
        )

    create_resp.raise_for_status()
    site_id = create_resp.json()["id"]
    site_url = create_resp.json()["ssl_url"]

    # Deploy the zip
    deploy_resp = httpx.post(
        f"{NETLIFY_API}/sites/{site_id}/deploys",
        headers={**headers, "Content-Type": "application/zip"},
        content=zip_data,
        timeout=60,
    )
    deploy_resp.raise_for_status()

    return site_url
