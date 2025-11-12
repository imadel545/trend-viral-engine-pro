"""
Tests for FeatureService.
"""

import pytest
import pandas as pd

from src.services.features import TemporalFeatureExtractor, EmbeddingFeatureExtractor


def test_temporal_feature_extractor(sample_dataframe):
    """Test temporal feature extraction."""
    extractor = TemporalFeatureExtractor()

    result = extractor.extract(sample_dataframe)

    assert "hour" in result.columns
    assert "day_of_week" in result.columns
    assert "is_weekend" in result.columns


def test_embedding_feature_extractor(sample_dataframe):
    """Test embedding feature extraction."""
    extractor = EmbeddingFeatureExtractor()

    result = extractor.extract(sample_dataframe)

    # Should have embedding columns
    emb_cols = [col for col in result.columns if col.startswith("emb_")]
    assert len(emb_cols) > 0


def test_feature_extractor_empty_dataframe():
    """Test feature extraction with empty DataFrame."""
    extractor = TemporalFeatureExtractor()

    empty_df = pd.DataFrame()
    result = extractor.extract(empty_df)

    assert len(result) == 0
