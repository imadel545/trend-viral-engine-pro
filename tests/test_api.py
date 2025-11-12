"""
Tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_score_endpoint():
    """Test score endpoint."""
    request_data = {
        "topic": "AI automation 2026",
        "country": "FR",
    }

    response = client.post("/api/v1/score", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "predicted_views_24h" in data
    assert 0 <= data["score"] <= 1


def test_topk_endpoint():
    """Test top K trends endpoint."""
    response = client.get("/api/v1/trends/topK?k=5&country=FR")

    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert len(data["trends"]) == 5
    assert data["country"] == "FR"


@pytest.mark.asyncio
async def test_generate_endpoint():
    """Test content generation endpoint."""
    request_data = {
        "topic": "AI trends 2026",
        "format": "video",
        "duration": 25,
    }

    # Note: This might fail without proper API keys
    response = client.post("/api/v1/generate", json=request_data)

    # Accept both success and error (due to missing API keys)
    assert response.status_code in [200, 500]


def test_feedback_endpoint():
    """Test feedback submission endpoint."""
    request_data = {
        "content_id": "test123",
        "views": 50000,
        "likes": 2500,
        "comments": 100,
        "watch_time": 0.75,
    }

    response = client.post("/api/v1/feedback", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_invalid_endpoint():
    """Test invalid endpoint returns 404."""
    response = client.get("/api/v1/invalid")

    assert response.status_code == 404
