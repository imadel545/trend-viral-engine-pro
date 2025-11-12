"""
Tests for ScoringService.
"""

import pytest
import pandas as pd
import numpy as np

from src.services.scoring.service import LightGBMModel, ScoringService


def test_scoring_service_initialization():
    """Test scoring service initialization."""
    service = ScoringService()

    assert service.model is not None


def test_scoring_service_score_without_model(sample_dataframe):
    """Test scoring without trained model (should return defaults)."""
    service = ScoringService()

    # Reset model to force default behavior
    service.model.model = None

    scores = service.score(sample_dataframe)

    assert "p_breakout_24h" in scores.columns
    assert "predicted_views_24h" in scores.columns
    assert len(scores) == len(sample_dataframe)


def test_lightgbm_model_predict_proba():
    """Test LightGBM probability prediction."""
    model = LightGBMModel()

    # Create dummy data
    X = pd.DataFrame(np.random.rand(10, 5), columns=[f"feat_{i}" for i in range(5)])
    y = pd.Series([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])

    # Train minimal model
    model.train(X, y, calibrate=False, log_mlflow=False)

    # Predict
    probas = model.predict_proba(X)

    assert len(probas) == len(X)
    assert all(0 <= p <= 1 for p in probas)
