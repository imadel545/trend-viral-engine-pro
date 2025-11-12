"""
⭐ CANONICAL ENSEMBLE MODEL - PRODUCTION

This is the OFFICIAL ensemble model used in production for viral trend prediction.

🚀 PRODUCTION STATUS:
- Used by: src/services/scoring/service.py (line 232)
- Trained by: scripts/training/train_ensemble.py
- Validated by: scripts/validation/validate_model.py
- Model file: models/ensemble_model.pkl

🏗️ ARCHITECTURE:
Combines multiple gradient boosting algorithms (LightGBM, XGBoost, CatBoost)
with soft voting strategy for improved performance.

Base Models:
- LightGBM: Fast training, efficient memory usage
- XGBoost: Robust to overfitting, good regularization
- CatBoost: Handles categorical features well, ordered boosting

Ensemble Strategy:
- Soft voting: Weighted average of class probabilities
- Default weights: [1.0, 1.0, 1.0] (uniform)
- Customizable per model importance

📊 CURRENT PERFORMANCE:
- AUC: 1.0 (overfitted on synthetic data - NEEDS REAL DATA)
- Features: 473 dimensions
- Latency: <20ms inference time
- Status: Production-ready architecture, awaiting real data retraining

⚠️ KNOWN ISSUES:
- Overfitted on synthetic trends (1000 samples)
- Feature mismatch: 473 training vs 400 production features
- Needs recalibration on real viral data

🔄 FOR EXPERIMENTAL MODELS:
See: src/services/scoring/experimental/
- TabNetClassifier (deep learning)
- AutoMLClassifier (hyperparameter tuning)
- StackedEnsembleClassifier (multi-layer stacking)

📝 USAGE:
    from src.services.scoring.advanced_ensemble import EnsembleVotingModel
    
    # Training
    model = EnsembleVotingModel()
    model.train(X_train, y_train)
    model.save("models/ensemble_model.pkl")
    
    # Production inference
    model = EnsembleVotingModel()
    model.load("models/ensemble_model.pkl")
    predictions = model.predict_proba(X_new)

📚 SEE ALSO:
- AUDIT_COMPLET_GAFAM.md - Code quality audit
- PLAN_CONSOLIDATION_ENSEMBLE.md - Ensemble consolidation plan
- docs/architecture.md - Full system architecture

Last updated: 6 Novembre 2025
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score

# Gradient boosting libraries
import lightgbm as lgb
import xgboost as xgb
import catboost as cb

# Ensemble methods
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression


class EnsembleVotingModel:
    """
    Voting ensemble combining LightGBM, XGBoost, and CatBoost.
    
    Uses soft voting (weighted averaging of class probabilities) for final prediction.
    Particularly effective when individual models have different strengths/biases.
    """
    
    def __init__(self, weights: Optional[List[float]] = None):
        """
        Initialize ensemble model.
        
        Args:
            weights: Voting weights [lgb_weight, xgb_weight, cb_weight].
                    If None, uses uniform weights [1, 1, 1].
        """
        self.logger = logger.bind(model="ensemble_voting")
        self.weights = weights or [1.0, 1.0, 1.0]
        
        # Individual models
        self.lgb_model: Optional[lgb.Booster] = None
        self.xgb_model: Optional[xgb.Booster] = None
        self.cb_model: Optional[cb.CatBoost] = None
        
        # Metadata
        self.n_features: Optional[int] = None
        self.feature_names: Optional[List[str]] = None
        self.is_trained = False
        
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        random_state: int = 42,
        optimize_weights: bool = False
    ) -> Dict[str, Any]:
        """
        Train all ensemble models.
        
        Args:
            X: Features
            y: Labels
            test_size: Validation split ratio
            random_state: Random seed
            optimize_weights: If True, optimize voting weights on validation set
            
        Returns:
            Metrics dict with per-model and ensemble performance
        """
        self.logger.info(f"Training ensemble on {len(X)} samples with {X.shape[1]} features")
        
        # Store metadata
        self.n_features = X.shape[1]
        self.feature_names = X.columns.tolist()
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        self.logger.info(f"Train: {len(X_train)} samples, Validation: {len(X_val)} samples")
        
        # Train individual models
        metrics = {}
        
        # 1. LightGBM
        self.logger.info("Training LightGBM...")
        self.lgb_model, lgb_metrics = self._train_lightgbm(X_train, y_train, X_val, y_val)
        metrics['lightgbm'] = lgb_metrics
        
        # 2. XGBoost
        self.logger.info("Training XGBoost...")
        self.xgb_model, xgb_metrics = self._train_xgboost(X_train, y_train, X_val, y_val)
        metrics['xgboost'] = xgb_metrics
        
        # 3. CatBoost
        self.logger.info("Training CatBoost...")
        self.cb_model, cb_metrics = self._train_catboost(X_train, y_train, X_val, y_val)
        metrics['catboost'] = cb_metrics
        
        # Optimize weights if requested
        if optimize_weights:
            self.logger.info("Optimizing ensemble weights...")
            self.is_trained = True  # Set before optimization
            self.weights = self._optimize_weights(X_val, y_val)
            self.logger.info(f"Optimized weights: LGB={self.weights[0]:.3f}, XGB={self.weights[1]:.3f}, CB={self.weights[2]:.3f}")
        else:
            self.is_trained = True
        
        # Evaluate ensemble
        self.logger.info("Evaluating ensemble...")
        ensemble_metrics = self._evaluate_ensemble(X_val, y_val)
        metrics['ensemble'] = ensemble_metrics
        
        # Log summary
        self.logger.info("=" * 60)
        self.logger.info("ENSEMBLE TRAINING COMPLETE")
        self.logger.info(f"LightGBM AUC: {lgb_metrics['auc']:.4f}")
        self.logger.info(f"XGBoost  AUC: {xgb_metrics['auc']:.4f}")
        self.logger.info(f"CatBoost AUC: {cb_metrics['auc']:.4f}")
        self.logger.info(f"Ensemble AUC: {ensemble_metrics['auc']:.4f} ✨")
        self.logger.info("=" * 60)
        
        return metrics
    
    def _train_lightgbm(
        self, X_train: pd.DataFrame, y_train: pd.Series,
        X_val: pd.DataFrame, y_val: pd.Series
    ) -> Tuple[lgb.Booster, Dict[str, float]]:
        """Train LightGBM model."""
        train_data = lgb.Dataset(X_train, label=y_train, feature_name=self.feature_names)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
        
        model = lgb.train(
            params,
            train_data,
            valid_sets=[val_data],
            num_boost_round=500,
            callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=0)]
        )
        
        # Evaluate
        y_pred_proba = model.predict(X_val)
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        metrics = {
            'auc': roc_auc_score(y_val, y_pred_proba),
            'accuracy': accuracy_score(y_val, y_pred),
            'precision': precision_score(y_val, y_pred, zero_division=0),
            'recall': recall_score(y_val, y_pred, zero_division=0)
        }
        
        return model, metrics
    
    def _train_xgboost(
        self, X_train: pd.DataFrame, y_train: pd.Series,
        X_val: pd.DataFrame, y_val: pd.Series
    ) -> Tuple[xgb.Booster, Dict[str, float]]:
        """Train XGBoost model."""
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=self.feature_names)
        dval = xgb.DMatrix(X_val, label=y_val, feature_names=self.feature_names)
        
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': 6,
            'eta': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'verbosity': 0
        }
        
        evals = [(dval, 'validation')]
        model = xgb.train(
            params,
            dtrain,
            num_boost_round=500,
            evals=evals,
            early_stopping_rounds=50,
            verbose_eval=False
        )
        
        # Evaluate
        y_pred_proba = model.predict(dval)
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        metrics = {
            'auc': roc_auc_score(y_val, y_pred_proba),
            'accuracy': accuracy_score(y_val, y_pred),
            'precision': precision_score(y_val, y_pred, zero_division=0),
            'recall': recall_score(y_val, y_pred, zero_division=0)
        }
        
        return model, metrics
    
    def _train_catboost(
        self, X_train: pd.DataFrame, y_train: pd.Series,
        X_val: pd.DataFrame, y_val: pd.Series
    ) -> Tuple[cb.CatBoost, Dict[str, float]]:
        """Train CatBoost model."""
        train_pool = cb.Pool(X_train, y_train, feature_names=self.feature_names)
        val_pool = cb.Pool(X_val, y_val, feature_names=self.feature_names)
        
        model = cb.CatBoostClassifier(
            iterations=500,
            learning_rate=0.05,
            depth=6,
            loss_function='Logloss',
            eval_metric='AUC',
            random_seed=42,
            verbose=False,
            early_stopping_rounds=50
        )
        
        model.fit(
            train_pool,
            eval_set=val_pool,
            use_best_model=True,
            verbose=False
        )
        
        # Evaluate
        y_pred_proba = model.predict_proba(X_val)[:, 1]
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        metrics = {
            'auc': roc_auc_score(y_val, y_pred_proba),
            'accuracy': accuracy_score(y_val, y_pred),
            'precision': precision_score(y_val, y_pred, zero_division=0),
            'recall': recall_score(y_val, y_pred, zero_division=0)
        }
        
        return model, metrics
    
    def _optimize_weights(self, X_val: pd.DataFrame, y_val: pd.Series) -> List[float]:
        """
        Optimize voting weights using grid search on validation set.
        
        Args:
            X_val: Validation features
            y_val: Validation labels
            
        Returns:
            Optimized weights [lgb_weight, xgb_weight, cb_weight]
        """
        best_auc = 0.0
        best_weights = [1.0, 1.0, 1.0]
        
        # Get predictions from individual models
        lgb_pred = self.lgb_model.predict(X_val)
        xgb_pred = self.xgb_model.predict(xgb.DMatrix(X_val, feature_names=self.feature_names))
        cb_pred = self.cb_model.predict_proba(X_val)[:, 1]
        
        # Grid search over weight combinations
        for w1 in np.arange(0.5, 1.5, 0.1):
            for w2 in np.arange(0.5, 1.5, 0.1):
                for w3 in np.arange(0.5, 1.5, 0.1):
                    # Weighted average
                    ensemble_pred = (w1 * lgb_pred + w2 * xgb_pred + w3 * cb_pred) / (w1 + w2 + w3)
                    auc = roc_auc_score(y_val, ensemble_pred)
                    
                    if auc > best_auc:
                        best_auc = auc
                        best_weights = [w1, w2, w3]
        
        return best_weights
    
    def _evaluate_ensemble(self, X_val: pd.DataFrame, y_val: pd.Series) -> Dict[str, float]:
        """Evaluate ensemble predictions."""
        y_pred_proba = self.predict_proba(X_val)
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        return {
            'auc': roc_auc_score(y_val, y_pred_proba),
            'accuracy': accuracy_score(y_val, y_pred),
            'precision': precision_score(y_val, y_pred, zero_division=0),
            'recall': recall_score(y_val, y_pred, zero_division=0)
        }
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class probabilities with ensemble voting.
        
        Args:
            X: Features
            
        Returns:
            Probability of class 1 (breakout)
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        # Get predictions from each model
        lgb_pred = self.lgb_model.predict(X)
        xgb_pred = self.xgb_model.predict(xgb.DMatrix(X, feature_names=self.feature_names))
        # Fix CatBoost: use predict() with prediction_type instead of predict_proba()
        cb_pred = self.cb_model.predict(X, prediction_type='Probability')[:, 1]
        
        # Weighted average
        w1, w2, w3 = self.weights
        ensemble_pred = (w1 * lgb_pred + w2 * xgb_pred + w3 * cb_pred) / (w1 + w2 + w3)
        
        return ensemble_pred
    
    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Predict class labels."""
        proba = self.predict_proba(X)
        return (proba > threshold).astype(int)
    
    def save(self, output_path: Path):
        """Save ensemble model."""
        import pickle
        
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        # Save LightGBM
        lgb_path = output_path.with_suffix('.lgb.txt')
        self.lgb_model.save_model(str(lgb_path))
        
        # Save XGBoost
        xgb_path = output_path.with_suffix('.xgb.json')
        self.xgb_model.save_model(str(xgb_path))
        
        # Save CatBoost
        cb_path = output_path.with_suffix('.cb.bin')
        self.cb_model.save_model(str(cb_path))
        
        # Save metadata
        metadata = {
            'weights': self.weights,
            'n_features': self.n_features,
            'feature_names': self.feature_names,
            'lgb_path': str(lgb_path),
            'xgb_path': str(xgb_path),
            'cb_path': str(cb_path)
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        self.logger.info(f"Ensemble model saved to {output_path}")
    
    def load(self, model_path: Path):
        """Load ensemble model."""
        import pickle
        
        # Load metadata
        with open(model_path, 'rb') as f:
            metadata = pickle.load(f)
        
        self.weights = metadata['weights']
        self.n_features = metadata['n_features']
        self.feature_names = metadata['feature_names']
        
        # Load individual models
        self.lgb_model = lgb.Booster(model_file=metadata['lgb_path'])
        self.xgb_model = xgb.Booster()
        self.xgb_model.load_model(metadata['xgb_path'])
        self.cb_model = cb.CatBoost()
        self.cb_model.load_model(metadata['cb_path'])
        
        self.is_trained = True
        self.logger.info(f"Ensemble model loaded from {model_path}")
