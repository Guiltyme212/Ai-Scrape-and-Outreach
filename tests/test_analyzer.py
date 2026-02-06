"""Tests for the analyzer service."""

import pytest
from app.services.analyzer import _mock_analyze


def test_mock_analyze_returns_score():
    result = _mock_analyze("Test Business", "plumber", "Amsterdam")
    assert "score" in result
    assert 1 <= result["score"] <= 100


def test_mock_analyze_returns_issues():
    result = _mock_analyze("Test Business", "plumber", "Amsterdam")
    assert "issues" in result
    assert isinstance(result["issues"], list)
    assert len(result["issues"]) >= 3


def test_mock_analyze_returns_summary():
    result = _mock_analyze("Test Business", "plumber", "Amsterdam")
    assert "summary" in result
    assert "Test Business" in result["summary"]


def test_mock_analyze_returns_priorities():
    result = _mock_analyze("Test Business", "plumber", "Amsterdam")
    assert "redesign_priorities" in result
    assert isinstance(result["redesign_priorities"], list)
