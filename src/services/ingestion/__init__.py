"""Ingestion service package."""

from src.services.ingestion.service import (
    DataSource,
    GoogleTrendsSource,
    IngestionService,
    RedditSource,
    TikTokSource,
    get_ingestion_service,
)

__all__ = [
    "DataSource",
    "GoogleTrendsSource",
    "RedditSource",
    "TikTokSource",
    "IngestionService",
    "get_ingestion_service",
]
