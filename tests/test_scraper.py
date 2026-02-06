"""Tests for the scraper service."""

import pytest
from app.services.scraper import _mock_scrape


def test_mock_scrape_returns_results():
    results = _mock_scrape("plumber", "Amsterdam, Netherlands", 10)
    assert len(results) == 10
    assert all("business_name" in r for r in results)
    assert all("city" in r for r in results)


def test_mock_scrape_respects_limit():
    results = _mock_scrape("plumber", "Amsterdam", 5)
    assert len(results) == 5


def test_mock_scrape_has_required_fields():
    results = _mock_scrape("dentist", "Rotterdam", 1)
    lead = results[0]
    required_fields = [
        "business_name", "business_type", "address", "city",
        "phone", "website_url", "google_maps_url", "rating", "reviews_count",
    ]
    for field in required_fields:
        assert field in lead, f"Missing field: {field}"
