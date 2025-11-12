"""
Tests for IngestionService.
"""

import pytest
import pandas as pd
from unittest.mock import AsyncMock, patch

from src.services.ingestion import GoogleTrendsSource, RedditSource, IngestionService


@pytest.mark.asyncio
async def test_google_trends_source():
    """Test Google Trends data source."""
    source = GoogleTrendsSource()

    with patch("pytrends.request.TrendReq") as mock_trends:
        mock_instance = mock_trends.return_value
        mock_instance.trending_searches.return_value = pd.DataFrame({"0": ["AI", "Tech"]})

        data = await source.collect(regions=["FR"])

        assert len(data) == 2
        assert data[0]["topic"] == "AI"
        assert data[0]["region"] == "FR"


@pytest.mark.asyncio
async def test_reddit_source():
    """Test Reddit data source."""
    source = RedditSource()

    # Mock Reddit API
    with patch("praw.Reddit") as mock_reddit:
        mock_instance = mock_reddit.return_value
        mock_subreddit = mock_instance.subreddit.return_value

        # Mock post
        mock_post = type("Post", (), {
            "id": "abc123",
            "title": "Test Post",
            "score": 100,
            "upvote_ratio": 0.95,
            "num_comments": 50,
            "created_utc": 1698969600,
            "url": "https://reddit.com/test",
            "selftext": "Test content",
        })

        mock_subreddit.hot.return_value = [mock_post]

        data = await source.collect(subreddits=["test"], limit=1)

        assert len(data) == 1
        assert data[0]["title"] == "Test Post"


@pytest.mark.asyncio
async def test_ingestion_service_run_collection():
    """Test ingestion service orchestration."""
    service = IngestionService()

    # Mock the sources
    with patch.object(service.sources["google_trends"], "collect", new_callable=AsyncMock) as mock_collect:
        mock_collect.return_value = [{"topic": "test", "region": "FR"}]

        results = await service.run_collection(sources=["google_trends"])

        assert "google_trends" in results
        mock_collect.assert_called_once()


def test_ingestion_service_initialization():
    """Test ingestion service initialization."""
    service = IngestionService()

    # Should have at least Google Trends if enabled
    assert len(service.sources) > 0
    assert "google_trends" in service.sources
