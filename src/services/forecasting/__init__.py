"""
Forecasting Service - Multi-horizon LSTM predictions.
Phase 2D - Advanced ML Pipeline.
"""

from typing import Optional
from .lstm_forecaster import LSTMForecaster

__all__ = ['LSTMForecaster', 'get_forecaster']

_forecaster_instance: Optional[LSTMForecaster] = None


def get_forecaster() -> LSTMForecaster:
    """Get or create LSTM forecaster singleton."""
    global _forecaster_instance
    if _forecaster_instance is None:
        _forecaster_instance = LSTMForecaster()
    return _forecaster_instance
