"""
Scoring Service - Viral Trend Prediction

This module provides the canonical scoring service for predicting viral trends.

⭐ PRODUCTION MODEL:
- EnsembleVotingModel: LightGBM + XGBoost + CatBoost with soft voting
- Location: advanced_ensemble.py
- Model file: models/ensemble_model.pkl
- Fallback: LightGBM baseline (models/baseline_model.pkl)

🧪 EXPERIMENTAL MODELS:
- TabNetClassifier, AutoMLClassifier, StackedEnsembleClassifier
- Location: experimental/ensemble_models.py
- Status: Research only, not production-ready

📝 USAGE:
    from src.services.scoring import get_scoring_service, EnsembleVotingModel
    
    # Get scoring service (singleton)
    service = get_scoring_service()
    scores = service.score(features_df)
    
    # Direct model usage
    model = EnsembleVotingModel()
    model.load("models/ensemble_model.pkl")
    predictions = model.predict_proba(X)

📦 EXPORTS:
- get_scoring_service() - Singleton service factory (MAIN ENTRY POINT)
- EnsembleVotingModel - Production ensemble model

For experimental models, import explicitly:
    from src.services.scoring.experimental import TabNetClassifier

Last updated: 6 Novembre 2025
"""

from .service import get_scoring_service, LightGBMModel
from .advanced_ensemble import EnsembleVotingModel

__all__ = [
    'get_scoring_service',
    'EnsembleVotingModel',
    'LightGBMModel',
]
