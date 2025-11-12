"""
Scoring Service - ML model for viral prediction.
Implements LightGBM baseline with calibration.
"""

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import lightgbm as lgb
import mlflow
import mlflow.lightgbm
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, precision_recall_curve
from sklearn.model_selection import train_test_split

from src.core.config import settings


class ScoringModel:
    """Base scoring model interface."""

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Predict scores."""
        raise NotImplementedError

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        """Predict probabilities."""
        raise NotImplementedError


class LightGBMModel(ScoringModel):
    """LightGBM-based scoring model."""

    def __init__(self):
        self.logger = logger.bind(model="lightgbm")
        self.model: Optional[lgb.Booster] = None
        self.calibrator: Optional[CalibratedClassifierCV] = None
        self.feature_names: List[str] = []

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        calibrate: bool = True,
        log_mlflow: bool = True,
    ) -> Dict[str, float]:
        """Train the model."""
        self.logger.info(f"Training on {len(X)} samples with {X.shape[1]} features")

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Create datasets
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

        # Parameters
        params = {
            "objective": "binary",
            "metric": ["binary_logloss", "auc"],
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.9,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
            "max_depth": 7,
            "min_child_samples": 20,
        }

        # Train
        self.logger.info("Training LightGBM model...")
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[train_data, val_data],
            valid_names=["train", "valid"],
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(50)],
        )

        self.feature_names = X.columns.tolist()

        # Calibrate
        if calibrate:
            self.logger.info("Calibrating model...")
            self._calibrate(X_val, y_val)

        # Evaluate
        metrics = self.evaluate(X_val, y_val)

        # Log to MLflow
        if log_mlflow:
            self._log_to_mlflow(params, metrics)

        return metrics

    def _calibrate(self, X_val: pd.DataFrame, y_val: pd.Series) -> None:
        """Calibrate model probabilities."""
        from sklearn.base import BaseEstimator, ClassifierMixin
        import numpy as np

        class LGBMWrapper(BaseEstimator, ClassifierMixin):
            def __init__(self, booster):
                self.booster = booster
                self.classes_ = np.array([0, 1])  # Binary classification

            def fit(self, X, y):
                """Dummy fit - model already trained."""
                self.classes_ = np.unique(y)
                return self

            def predict_proba(self, X):
                preds = self.booster.predict(X)
                return np.vstack([1 - preds, preds]).T

        wrapper = LGBMWrapper(self.model)

        if settings.model_calibration == "isotonic":
            self.calibrator = CalibratedClassifierCV(
                wrapper, method="isotonic", cv="prefit"
            )
        else:
            self.calibrator = CalibratedClassifierCV(
                wrapper, method="sigmoid", cv="prefit"
            )

        self.calibrator.fit(X_val, y_val)
        self.logger.info("Calibration complete")

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        """Predict probabilities with calibration."""
        if self.model is None:
            raise ValueError("Model not trained")

        if self.calibrator:
            proba = self.calibrator.predict_proba(features)[:, 1]
        else:
            proba = self.model.predict(features)

        return proba

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Predict binary class."""
        proba = self.predict_proba(features)
        return (proba >= settings.model_threshold).astype(int)

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Evaluate model performance."""
        y_pred_proba = self.predict_proba(X)
        y_pred = self.predict(X)

        metrics = {
            "auc": roc_auc_score(y, y_pred_proba),
            "accuracy": (y_pred == y).mean(),
            "precision": ((y_pred == 1) & (y == 1)).sum() / max((y_pred == 1).sum(), 1),
            "recall": ((y_pred == 1) & (y == 1)).sum() / max((y == 1).sum(), 1),
        }

        self.logger.info(f"Metrics: {metrics}")
        return metrics

    def _log_to_mlflow(self, params: Dict[str, Any], metrics: Dict[str, float]) -> None:
        """Log model to MLflow."""
        try:
            mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
            mlflow.set_experiment(settings.mlflow_experiment_name)

            with mlflow.start_run():
                # Log parameters
                mlflow.log_params(params)

                # Log metrics
                mlflow.log_metrics(metrics)

                # Log model
                mlflow.lightgbm.log_model(self.model, "model")

                self.logger.info("Logged to MLflow")

        except Exception as e:
            self.logger.warning(f"Failed to log to MLflow: {e}")

    def save(self, path: Path) -> None:
        """Save model to disk."""
        model_data = {
            "model": self.model,
            "calibrator": self.calibrator,
            "feature_names": self.feature_names,
        }

        with open(path, "wb") as f:
            pickle.dump(model_data, f)

        self.logger.info(f"Model saved to {path}")

    def load(self, path: Path) -> None:
        """Load model from disk."""
        with open(path, "rb") as f:
            model_data = pickle.load(f)

        self.model = model_data["model"]
        self.calibrator = model_data.get("calibrator")
        self.feature_names = model_data["feature_names"]

        self.logger.info(f"Model loaded from {path}")


class ScoringService:
    """Main scoring service."""

    def __init__(self):
        self.logger = logger.bind(service="scoring")
        self.model: Optional[ScoringModel] = None
        self._load_or_create_model()

    def _load_or_create_model(self) -> None:
        """Load existing model or create new one."""
        # Priority 1: Try ensemble model (BEST performance)
        ensemble_path = settings.models_path / "ensemble_model.pkl"
        
        if ensemble_path.exists():
            self.logger.info(f"🏆 Loading ENSEMBLE model from {ensemble_path}")
            try:
                from src.services.scoring.advanced_ensemble import EnsembleVotingModel
                self.model = EnsembleVotingModel()
                self.model.load(ensemble_path)
                self.logger.info("✅ Ensemble model loaded successfully")
                return
            except Exception as e:
                self.logger.warning(f"Failed to load ensemble: {e}, falling back to baseline")
        
        # Priority 2: Baseline LightGBM
        model_path = settings.models_path / "baseline_model.pkl"

        if model_path.exists():
            self.logger.info(f"Loading baseline model from {model_path}")
            self.model = LightGBMModel()
            self.model.load(model_path)
        else:
            self.logger.info("Creating new baseline model")
            self.model = LightGBMModel()

    def score(self, features: pd.DataFrame) -> pd.DataFrame:
        """Score features and return predictions."""
        # Check if model is trained (supports both baseline and ensemble)
        model_trained = False
        if self.model is not None:
            # Ensemble model: check .is_trained attribute
            if hasattr(self.model, "is_trained"):
                model_trained = self.model.is_trained
            # Baseline model: check .model attribute
            elif hasattr(self.model, "model"):
                model_trained = self.model.model is not None
        
        if not model_trained:
            self.logger.warning("Model not trained, returning default scores")
            return pd.DataFrame({
                "p_breakout_24h": [0.5] * len(features),
                "predicted_views_24h": [1000] * len(features),
            })

        # PHASE 1 FIX (P2): Preprocess features to filter non-numeric columns
        from src.services.scoring.preprocessor import get_preprocessor
        
        preprocessor = get_preprocessor(allowed_prefixes=["emb_", "temporal_"])
        features_processed = preprocessor.preprocess(
            features, 
            training_columns=self.model.feature_names,
            validate=True
        )
        
        # Get probabilities
        probas = self.model.predict_proba(features_processed)

        # Estimate views (simple heuristic for now)
        predicted_views = probas * 100000  # Scale to realistic view counts

        results = pd.DataFrame({
            "p_breakout_24h": probas,
            "predicted_views_24h": predicted_views.astype(int),
        })

        return results

    def train_model(self, features_path: Path, labels_path: Path) -> Dict[str, float]:
        """Train model on labeled data."""
        self.logger.info("Training model...")

        # Load data
        X = pd.read_parquet(features_path)
        labels_df = pd.read_parquet(labels_path)

        # Extract target
        y = labels_df["is_breakout"]

        # Train
        model = LightGBMModel()
        metrics = model.train(X, y)

        # Save
        model_path = settings.models_path / "baseline_model.pkl"
        model.save(model_path)

        # Update current model
        self.model = model

        return metrics


# Singleton
_scoring_service: Optional[ScoringService] = None


def get_scoring_service() -> ScoringService:
    """Get or create scoring service instance."""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service
