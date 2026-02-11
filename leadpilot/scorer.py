"""Website scorer — fetches a site, extracts info, and scores it with Claude."""

import json
import httpx
from bs4 import BeautifulSoup
from anthropic import Anthropic

from leadpilot.config import settings

client = Anthropic(api_key=settings.anthropic_api_key)

SCORE_PROMPT = """You are a web design expert evaluating a small business website.

Analyze the following website data and provide:
1. A quality score from 1-100 (consider: visual design, mobile-friendliness, modernity, load speed indicators, content quality, professionalism)
2. A list of specific issues found
3. Extracted business information

Website URL: {url}
Page title: {title}
Meta description: {meta_description}
Page content (first 3000 chars):
{content}

Respond ONLY with valid JSON in this exact format:
{{
    "score": <integer 1-100>,
    "issues": ["issue 1", "issue 2", ...],
    "extracted": {{
        "business_name": "<name or empty string>",
        "business_type": "<type of business or empty string>",
        "services": ["service 1", "service 2"],
        "phone": "<phone or empty string>",
        "address": "<address or empty string>"
    }}
}}"""


def _fetch_website(url: str) -> dict:
    """Fetch a website and extract key information."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    response = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"]

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text_content = soup.get_text(separator=" ", strip=True)[:3000]

    return {
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "content": text_content,
    }


def score_website(url: str) -> dict:
    """Fetch a website and score it using Claude AI.

    Returns: {"score": int, "issues": list[str], "extracted": dict}
    """
    site_data = _fetch_website(url)

    prompt = SCORE_PROMPT.format(**site_data)

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    result_text = response.content[0].text

    # Parse JSON from response (handle markdown code blocks)
    if "```" in result_text:
        result_text = result_text.split("```")[1]
        if result_text.startswith("json"):
            result_text = result_text[4:]
        result_text = result_text.strip()

    return json.loads(result_text)
