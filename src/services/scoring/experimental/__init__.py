"""
Experimental ML Models - NOT FOR PRODUCTION

⚠️ These models are experimental and not used in the production pipeline.
See README.md for details.

For production viral prediction, use:
    from src.services.scoring.advanced_ensemble import EnsembleVotingModel
"""

# Conditional imports to avoid heavy dependencies if not needed
try:
    from .ensemble_models import TabNetClassifier, AutoMLClassifier, StackedEnsembleClassifier
    __all__ = ['TabNetClassifier', 'AutoMLClassifier', 'StackedEnsembleClassifier']
except ImportError as e:
    # Missing torch, optuna, or shap
    import warnings
    warnings.warn(
        f"Experimental models not available: {e}. "
        "Install with: pip install torch optuna shap",
        ImportWarning
    )
    __all__ = []
