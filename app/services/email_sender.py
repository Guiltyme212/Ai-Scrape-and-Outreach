"""
Instantly.ai API wrapper for cold email sending and tracking.

Real mode: Uses Instantly.ai API v2
Mock mode: Simulates email sending with random status updates.
"""

import random
from datetime import datetime
import httpx
from app.config import get_settings

INSTANTLY_BASE_URL = "https://api.instantly.ai/api/v2"


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    lead_id: int,
) -> dict:
    """
    Send an email via Instantly.ai.
    Returns dict with status and metadata.
    """
    settings = get_settings()

    if settings.mock_mode or not settings.instantly_api_key:
        return _mock_send(to_email, subject, lead_id)

    return await _real_send(to_email, subject, body, lead_id)


async def _real_send(
    to_email: str,
    subject: str,
    body: str,
    lead_id: int,
) -> dict:
    """Send via Instantly.ai API."""
    settings = get_settings()

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{INSTANTLY_BASE_URL}/emails/send",
                headers={
                    "Authorization": f"Bearer {settings.instantly_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.instantly_sending_email,
                    "to": to_email,
                    "subject": subject,
                    "body": body,
                },
            )
            response.raise_for_status()
            data = response.json()

        return {
            "status": "sent",
            "email_id": data.get("id"),
            "sent_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        print(f"Email send failed for lead {lead_id}: {e}")
        return {
            "status": "failed",
            "error": str(e),
        }


async def check_email_status(email_id: str) -> dict:
    """Check the status of a sent email (opens, clicks, replies)."""
    settings = get_settings()

    if settings.mock_mode or not settings.instantly_api_key:
        return _mock_status()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{INSTANTLY_BASE_URL}/emails/{email_id}",
                headers={"Authorization": f"Bearer {settings.instantly_api_key}"},
            )
            response.raise_for_status()
            return response.json()

    except Exception as e:
        print(f"Status check failed for email {email_id}: {e}")
        return {"status": "unknown", "error": str(e)}


def _mock_send(to_email: str, subject: str, lead_id: int) -> dict:
    """Simulate email sending."""
    return {
        "status": "sent",
        "email_id": f"mock-{lead_id}-{random.randint(1000, 9999)}",
        "sent_at": datetime.utcnow().isoformat(),
    }


def _mock_status() -> dict:
    """Return random mock email status."""
    statuses = ["sent", "opened", "clicked", "replied"]
    weights = [0.4, 0.3, 0.2, 0.1]
    status = random.choices(statuses, weights=weights, k=1)[0]
    return {"status": status}
