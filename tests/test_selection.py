"""
Tests for SelectionService.
"""

import pytest
import pandas as pd

from src.services.selection import SelectionService, TopKScoreStrategy, DiversityStrategy


def test_topk_strategy():
    """Test top K selection strategy."""
    strategy = TopKScoreStrategy()

    df = pd.DataFrame({
        "topic": ["A", "B", "C", "D", "E"],
        "p_breakout_24h": [0.9, 0.7, 0.8, 0.6, 0.95],
        "predicted_views_24h": [10000, 7000, 8000, 6000, 12000],
    })

    selected = strategy.select(df, k=3)

    assert len(selected) == 3
    assert selected.iloc[0]["topic"] == "E"  # Highest score
    assert selected["p_breakout_24h"].is_monotonic_decreasing


def test_diversity_strategy():
    """Test diversity selection strategy."""
    strategy = DiversityStrategy(diversity_weight=0.3)

    df = pd.DataFrame({
        "topic": ["A", "B", "C", "D", "E"],
        "p_breakout_24h": [0.9, 0.7, 0.8, 0.6, 0.95],
        "predicted_views_24h": [10000, 7000, 8000, 6000, 12000],
    })

    selected = strategy.select(df, k=3)

    assert len(selected) == 3


def test_selection_service_top_k():
    """Test selection service top K method."""
    service = SelectionService()

    df = pd.DataFrame({
        "topic": ["A", "B", "C"],
        "p_breakout_24h": [0.9, 0.7, 0.8],
        "predicted_views_24h": [10000, 7000, 8000],
        "country": ["FR", "FR", "US"],
    })

    selected = service.select_top_k(df, k=2, strategy="topk")

    assert len(selected) == 2


def test_selection_service_country_filter():
    """Test country filtering in selection."""
    service = SelectionService()

    df = pd.DataFrame({
        "topic": ["A", "B", "C"],
        "p_breakout_24h": [0.9, 0.7, 0.8],
        "predicted_views_24h": [10000, 7000, 8000],
        "country": ["FR", "US", "FR"],
    })

    selected = service.select_top_k(df, k=10, country="FR")

    assert len(selected) == 2
    assert all(selected["country"] == "FR")
