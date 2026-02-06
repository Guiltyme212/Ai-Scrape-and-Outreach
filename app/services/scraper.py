"""
Outscraper Google Maps API wrapper.
Scrapes business listings and filters for those with bad/missing websites.

Real mode: Uses Outscraper API (POST https://api.app.outscraper.com/maps/search-v3)
Mock mode: Returns realistic fake data for development.
"""

import json
import random
import httpx
from app.config import get_settings

# Realistic Dutch business data for mock mode
MOCK_BUSINESSES = [
    {"name": "Van der Berg Loodgietersbedrijf", "type": "plumber", "city": "Amsterdam", "phone": "+31 20 123 4567", "website": "http://vandenbergloodgieter.nl", "rating": 4.2, "reviews": 23},
    {"name": "Bakkerij De Gouden Korst", "type": "bakery", "city": "Amsterdam", "phone": "+31 20 234 5678", "website": "http://degoudenkorst.nl", "rating": 4.7, "reviews": 89},
    {"name": "Kapper Studio Mooi", "type": "hair_salon", "city": "Rotterdam", "phone": "+31 10 345 6789", "website": None, "rating": 3.9, "reviews": 12},
    {"name": "Tandarts Praktijk Jansen", "type": "dentist", "city": "Utrecht", "phone": "+31 30 456 7890", "website": "http://tandartsjansen.nl", "rating": 4.1, "reviews": 45},
    {"name": "Schildersbedrijf Kleurrijk", "type": "painter", "city": "Den Haag", "phone": "+31 70 567 8901", "website": "http://kleurrijkschilders.nl", "rating": 3.5, "reviews": 8},
    {"name": "Restaurant De Smakelijke Hoek", "type": "restaurant", "city": "Amsterdam", "phone": "+31 20 678 9012", "website": "http://desmakelijkehoek.nl", "rating": 4.4, "reviews": 156},
    {"name": "Fietsenmaker Pedaal", "type": "bike_repair", "city": "Utrecht", "phone": "+31 30 789 0123", "website": None, "rating": 4.6, "reviews": 34},
    {"name": "Schoonmaakbedrijf Fris", "type": "cleaning", "city": "Rotterdam", "phone": "+31 10 890 1234", "website": "http://frischoonmaak.nl", "rating": 3.2, "reviews": 5},
    {"name": "Elektricien Vonk", "type": "electrician", "city": "Amsterdam", "phone": "+31 20 901 2345", "website": "http://vonkelektro.nl", "rating": 4.0, "reviews": 19},
    {"name": "Bloemist Het Boeket", "type": "florist", "city": "Den Haag", "phone": "+31 70 012 3456", "website": None, "rating": 4.8, "reviews": 67},
    {"name": "Garage Snelle Wielen", "type": "auto_repair", "city": "Rotterdam", "phone": "+31 10 111 2222", "website": "http://snellewielen.nl", "rating": 3.8, "reviews": 28},
    {"name": "Dierenarts De Dierenvriend", "type": "veterinarian", "city": "Utrecht", "phone": "+31 30 222 3333", "website": "http://dedierenvriend.nl", "rating": 4.5, "reviews": 72},
    {"name": "Timmerman Houtwerk", "type": "carpenter", "city": "Amsterdam", "phone": "+31 20 333 4444", "website": None, "rating": 4.3, "reviews": 15},
    {"name": "Advocaat De Recht", "type": "lawyer", "city": "Den Haag", "phone": "+31 70 444 5555", "website": "http://derecht-advocaten.nl", "rating": 3.7, "reviews": 11},
    {"name": "Fysiotherapie Gezond Bewegen", "type": "physiotherapy", "city": "Rotterdam", "phone": "+31 10 555 6666", "website": "http://gezondbewegen-fysio.nl", "rating": 4.6, "reviews": 93},
]


async def scrape_businesses(
    niche: str, location: str, limit: int = 20
) -> list[dict]:
    """
    Scrape businesses from Google Maps.
    Returns list of dicts with business data.
    """
    settings = get_settings()

    if settings.mock_mode or not settings.outscraper_api_key:
        return _mock_scrape(niche, location, limit)

    return await _real_scrape(niche, location, limit)


async def _real_scrape(niche: str, location: str, limit: int) -> list[dict]:
    """Scrape via Outscraper API."""
    settings = get_settings()

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(
            "https://api.app.outscraper.com/maps/search-v3",
            params={
                "query": f"{niche} {location}",
                "limit": limit,
                "language": "nl",
                "region": "NL",
            },
            headers={"X-API-KEY": settings.outscraper_api_key},
        )
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("data", [[]])[0] if data.get("data") else []:
        results.append({
            "business_name": item.get("name", ""),
            "business_type": niche,
            "address": item.get("full_address", ""),
            "city": location.split(",")[0].strip(),
            "phone": item.get("phone", None),
            "email": item.get("email", None),
            "website_url": item.get("site", None),
            "google_maps_url": item.get("google_maps_url", ""),
            "rating": item.get("rating", None),
            "reviews_count": item.get("reviews", None),
        })

    return results


def _mock_scrape(niche: str, location: str, limit: int) -> list[dict]:
    """Return mock business data for development."""
    city = location.split(",")[0].strip()
    results = []

    for biz in MOCK_BUSINESSES[:limit]:
        results.append({
            "business_name": biz["name"],
            "business_type": biz["type"],
            "address": f"Voorbeeldstraat {random.randint(1, 200)}, {city}",
            "city": city,
            "phone": biz["phone"],
            "email": None,
            "website_url": biz["website"],
            "google_maps_url": f"https://maps.google.com/?cid={random.randint(10**15, 10**16)}",
            "rating": biz["rating"],
            "reviews_count": biz["reviews"],
        })

    return results
