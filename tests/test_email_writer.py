"""Tests for the email writer service."""

import pytest
from app.services.email_writer import _mock_email


def test_mock_email_returns_subject():
    result = _mock_email("Test Bedrijf", "plumber", "Amsterdam", "https://preview.example.com")
    assert "subject" in result
    assert len(result["subject"]) > 0


def test_mock_email_returns_body():
    result = _mock_email("Test Bedrijf", "plumber", "Amsterdam", "https://preview.example.com")
    assert "body" in result
    assert len(result["body"]) > 0


def test_mock_email_includes_business_name():
    result = _mock_email("Test Bedrijf", "plumber", "Amsterdam", "https://preview.example.com")
    assert "Test Bedrijf" in result["body"]


def test_mock_email_includes_preview_url():
    preview = "https://test-bedrijf.jouwdomein.nl"
    result = _mock_email("Test Bedrijf", "plumber", "Amsterdam", preview)
    assert preview in result["body"]
