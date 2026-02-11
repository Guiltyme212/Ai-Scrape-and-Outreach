"""Preview site generator — Claude creates a full single-page HTML website."""

from anthropic import Anthropic

from leadpilot.config import settings

client = Anthropic(api_key=settings.anthropic_api_key)

GENERATOR_PROMPT = """You are an elite web designer. Create a COMPLETE, stunning, modern single-page website for this business.

Business details:
- Name: {business_name}
- Type: {business_type}
- Description: {description}
- Services: {services}
- Contact info: {contact_info}

Issues with their current website:
{issues}

Requirements:
- Return ONLY the complete HTML code, nothing else. No explanations, no markdown.
- Use Tailwind CSS via CDN: <script src="https://cdn.tailwindcss.com"></script>
- Use Google Fonts for beautiful typography
- Modern, clean, professional design with smooth gradients
- Fully responsive (mobile-first)
- Sections: Hero with CTA, Services/Features, About, Contact, Footer
- Use the REAL business data throughout (name, services, description)
- Add appropriate icons using Heroicons or simple SVG icons
- Color scheme should feel professional and match the business type
- Add subtle animations (CSS transitions, hover effects)
- The page should look like a €3000+ custom website
- All text should be in Dutch
- Include a "Gemaakt door Boostly" (Made by Boostly) badge in the footer with a link placeholder

Start your response with <!DOCTYPE html> and end with </html>. Nothing else."""


def generate_preview(
    business_name: str,
    business_type: str,
    description: str,
    services: list[str],
    contact_info: dict,
    issues: list[str],
) -> str:
    """Generate a complete HTML preview site using Claude.

    Returns: HTML string ready to deploy.
    """
    prompt = GENERATOR_PROMPT.format(
        business_name=business_name,
        business_type=business_type,
        description=description,
        services=", ".join(services) if services else "Niet gespecificeerd",
        contact_info=_format_contact(contact_info),
        issues="\n".join(f"- {issue}" for issue in issues) if issues else "- Verouderd ontwerp",
    )

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    html = response.content[0].text

    # Strip any markdown wrapping if present
    if html.startswith("```"):
        lines = html.split("\n")
        html = "\n".join(lines[1:-1])

    # Ensure we have valid HTML
    if not html.strip().startswith("<!DOCTYPE") and not html.strip().startswith("<html"):
        start = html.find("<!DOCTYPE")
        if start == -1:
            start = html.find("<html")
        if start != -1:
            html = html[start:]

    return html


def _format_contact(info: dict) -> str:
    """Format contact info dict into readable string."""
    parts = []
    if info.get("phone"):
        parts.append(f"Telefoon: {info['phone']}")
    if info.get("address"):
        parts.append(f"Adres: {info['address']}")
    if info.get("email"):
        parts.append(f"Email: {info['email']}")
    return ", ".join(parts) if parts else "Niet beschikbaar"
