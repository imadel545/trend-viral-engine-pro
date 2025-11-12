"""
Tests for GeneratorService.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.generator import ScriptGenerator, CaptionGenerator


@pytest.mark.asyncio
async def test_script_generator_fallback(sample_topic_data):
    """Test script generator fallback when API fails."""
    generator = ScriptGenerator()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=Exception("API Error")
        )

        script = await generator.generate(sample_topic_data["topic"])

        assert "hook" in script
        assert "payoff" in script
        assert "cta" in script
        assert "caption" in script


@pytest.mark.asyncio
async def test_script_generator_success(sample_topic_data):
    """Test successful script generation."""
    generator = ScriptGenerator()

    mock_response = {
        "choices": [{
            "message": {
                "content": '{"hook": "Test hook", "payoff": "Test payoff", "cta": "Test CTA", "caption": "#test"}'
            }
        }]
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_post = AsyncMock()
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json = AsyncMock(return_value=mock_response)

        mock_client.return_value.__aenter__.return_value.post = mock_post

        script = await generator.generate(sample_topic_data["topic"])

        assert script["hook"] == "Test hook"
        assert script["payoff"] == "Test payoff"


def test_caption_generator(sample_script, sample_topic_data):
    """Test caption generation."""
    generator = CaptionGenerator()

    caption = generator.generate(sample_script, sample_topic_data["topic"])

    assert isinstance(caption, str)
    assert len(caption) > 0


def test_caption_generator_without_script(sample_topic_data):
    """Test caption generation without script."""
    generator = CaptionGenerator()

    caption = generator.generate({}, sample_topic_data["topic"])

    assert sample_topic_data["topic"] in caption or "#" in caption
