"""Email drafter — Claude generates personalised Dutch cold emails."""

import json
from anthropic import Anthropic

from leadpilot.config import settings

client = Anthropic(api_key=settings.anthropic_api_key)

EMAIL_PROMPT = """Je bent een koude e-mail specialist voor een Nederlands webdesign bureau genaamd "Boostly".

Schrijf een persoonlijke koude e-mail in het Nederlands voor dit bedrijf:

Bedrijfsnaam: {business_name}
Type bedrijf: {business_type}
Huidige website score: {score}/100
Problemen gevonden:
{issues}

Preview URL (nieuw ontwerp dat we GRATIS voor hen hebben gemaakt): {preview_url}

Regels:
- Schrijf in vloeiend, natuurlijk Nederlands (geen Google Translate-stijl)
- Wees vriendelijk, professioneel, en NIET pusherig
- Kort en krachtig — max 150 woorden
- Begin met een persoonlijke opening die laat zien dat je hun website hebt bekeken
- Noem 1-2 specifieke problemen die je hebt gevonden
- Presenteer de preview als een cadeau: "We hebben alvast een gratis voorbeeld gemaakt"
- Eindig met een zachte call-to-action (geen druk, geen haast)
- Onderteken met: "Met vriendelijke groet,\nHet Boostly Team"
- Onderwerpregel moet pakkend maar professioneel zijn

Antwoord ALLEEN met geldige JSON in dit formaat:
{{
    "subject": "<onderwerpregel>",
    "body": "<volledige e-mail tekst>"
}}"""


def draft_email(
    business_name: str,
    business_type: str,
    score: int,
    issues: list[str],
    preview_url: str,
) -> dict:
    """Draft a personalised Dutch cold email.

    Returns: {"subject": str, "body": str}
    """
    prompt = EMAIL_PROMPT.format(
        business_name=business_name,
        business_type=business_type,
        score=score,
        issues="\n".join(f"- {issue}" for issue in issues) if issues else "- Verouderd ontwerp",
        preview_url=preview_url,
    )

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    result_text = response.content[0].text

    # Parse JSON from response
    if "```" in result_text:
        result_text = result_text.split("```")[1]
        if result_text.startswith("json"):
            result_text = result_text[4:]
        result_text = result_text.strip()

    return json.loads(result_text)
