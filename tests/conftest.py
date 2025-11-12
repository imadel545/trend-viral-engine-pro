"""
Pytest configuration and fixtures.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock
from src.core.config import Settings


@pytest.fixture
def tmp_data_dirs(tmp_path):
    """Create isolated temporary data directories for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create subdirectories
    (data_dir / "raw").mkdir()
    (data_dir / "features").mkdir()
    (data_dir / "labels").mkdir()
    (data_dir / "feedback").mkdir()
    
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    return {
        "data": data_dir,
        "raw": data_dir / "raw",
        "features": data_dir / "features",
        "labels": data_dir / "labels",
        "feedback": data_dir / "feedback",
        "models": models_dir,
        "outputs": outputs_dir,
        "logs": logs_dir,
    }


@pytest.fixture
def mock_settings(tmp_data_dirs, monkeypatch):
    """Mock settings with isolated test directories."""
    # Create a test settings instance
    test_settings = Settings(
        environment="test",
        debug=True,
        log_level="DEBUG",
        model_retrain_threshold=2,  # Low threshold for testing
    )
    
    # Override paths with tmp directories
    monkeypatch.setattr(test_settings, "data_path", tmp_data_dirs["data"])
    monkeypatch.setattr(test_settings, "data_raw_path", tmp_data_dirs["raw"])
    monkeypatch.setattr(test_settings, "data_features_path", tmp_data_dirs["features"])
    monkeypatch.setattr(test_settings, "data_labels_path", tmp_data_dirs["labels"])
    monkeypatch.setattr(test_settings, "data_feedback_path", tmp_data_dirs["feedback"])
    monkeypatch.setattr(test_settings, "models_path", tmp_data_dirs["models"])
    monkeypatch.setattr(test_settings, "outputs_path", tmp_data_dirs["outputs"])
    monkeypatch.setattr(test_settings, "logs_path", tmp_data_dirs["logs"])
    
    # Patch global settings
    import src.core.config
    monkeypatch.setattr(src.core.config, "settings", test_settings)
    
    return test_settings


@pytest.fixture
def sample_topic_data():
    """Sample topic data for testing."""
    return {
        "topic": "AI automation 2026",
        "hashtags": ["#ai", "#automation", "#tech"],
        "country": "FR",
        "views": 50000,
        "likes": 2500,
    }


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    return pd.DataFrame([
        {
            "topic": "AI trends",
            "country": "FR",
            "views": 10000,
            "timestamp": "2025-11-02T10:00:00",
        },
        {
            "topic": "Tech innovation",
            "country": "US",
            "views": 25000,
            "timestamp": "2025-11-02T11:00:00",
        },
    ])


@pytest.fixture
def sample_script():
    """Sample script for testing."""
    return {
        "hook": "🔥 Découvre cette nouvelle tendance AI !",
        "payoff": "L'intelligence artificielle change tout. Voici ce que tu dois savoir maintenant.",
        "cta": "💡 Like si tu veux en savoir plus !",
        "caption": "#ai #tendance #viral #pourtoi",
    }


@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "features").mkdir()
    (data_dir / "labels").mkdir()
    (data_dir / "feedback").mkdir()
    return data_dir


@pytest.fixture
def mock_settings(temp_data_dir, monkeypatch):
    """Mock settings for testing."""
    from src.core.config import Settings

    test_settings = Settings(
        data_raw_path=temp_data_dir / "raw",
        data_features_path=temp_data_dir / "features",
        data_labels_path=temp_data_dir / "labels",
        data_feedback_path=temp_data_dir / "feedback",
        groq_api_key="test-key",
        environment="test",
    )

    monkeypatch.setattr("src.core.config.settings", test_settings)
    return test_settings
