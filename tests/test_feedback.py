"""
Tests for FeedbackService.
"""

import pytest
import json
from pathlib import Path

from src.services.feedback import FeedbackCollector, LabelGenerator, RetrainingTrigger


def test_feedback_collector_record(mock_settings):
    """Test feedback recording."""
    collector = FeedbackCollector()

    filepath = collector.record_feedback(
        content_id="test123",
        views=50000,
        likes=2500,
        comments=100,
        watch_time=0.75,
        shares=50,
    )

    assert filepath.exists()

    # Load and verify
    with open(filepath) as f:
        data = json.load(f)

    assert data["content_id"] == "test123"
    assert data["views"] == 50000
    assert data["engagement_rate"] > 0


def test_label_generator_no_feedback(mock_settings):
    """Test label generator with no feedback."""
    # Clean up any existing feedback files from previous tests
    import shutil
    feedback_path = mock_settings.data_feedback_path
    if feedback_path.exists():
        for f in feedback_path.glob("*.json"):
            f.unlink()
    
    generator = LabelGenerator()
    result = generator.generate_labels()

    assert result is None


def test_label_generator_with_feedback(mock_settings):
    """Test label generator with feedback."""
    # Create some feedback files
    collector = FeedbackCollector()
    collector.record_feedback("test1", 10000, 500, 50, 0.6, 10)
    collector.record_feedback("test2", 50000, 2500, 100, 0.8, 50)

    generator = LabelGenerator()
    labels_path = generator.generate_labels()

    assert labels_path is not None
    assert labels_path.exists()


def test_retraining_trigger_threshold(mock_settings, monkeypatch):
    """Test retraining trigger threshold."""
    # Set low threshold for testing
    monkeypatch.setattr("src.core.config.settings.model_retrain_threshold", 2)

    # Create feedback
    collector = FeedbackCollector()
    collector.record_feedback("test1", 10000, 500)
    collector.record_feedback("test2", 20000, 1000)

    trigger = RetrainingTrigger()

    assert trigger.should_retrain() is True


@pytest.mark.asyncio
async def test_feedback_service_submit(mock_settings):
    """Test feedback service submission."""
    from src.services.feedback import get_feedback_service

    service = get_feedback_service()

    result = service.submit_feedback(
        content_id="test123",
        views=50000,
        likes=2500,
    )

    assert "feedback_saved" in result
    assert "should_retrain" in result
