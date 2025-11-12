"""
Ensemble Models - State-of-the-Art ML Models
Implémente les meilleurs modèles d'ensemble et deep tabular au monde.
"""

import pickle
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostClassifier, Pool
from loguru import logger
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss, precision_recall_curve, average_precision_score
from sklearn.model_selection import train_test_split, StratifiedKFold

# Conditional imports
try:
    import optuna
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    warnings.warn("Optuna not available - AutoML disabled")

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    warnings.warn("PyTorch not available - deep learning disabled")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    warnings.warn("SHAP not available - explainability disabled")


class TabNetClassifier:
    """TabNet - Deep learning for tabular data."""
    
    def __init__(
        self,
        n_d: int = 64,
        n_a: int = 64,
        n_steps: int = 5,
        gamma: float = 1.5,
        n_independent: int = 2,
        n_shared: int = 2,
        lambda_sparse: float = 1e-4,
        lr: float = 0.02,
        epochs: int = 100,
        batch_size: int = 256,
    ):
        self.logger = logger.bind(model="tabnet")
        self.n_d = n_d
        self.n_a = n_a
        self.n_steps = n_steps
        self.gamma = gamma
        self.n_independent = n_independent
        self.n_shared = n_shared
        self.lambda_sparse = lambda_sparse
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    def _build_model(self, input_dim: int) -> nn.Module:
        """Build TabNet model."""
        # Simplified TabNet-like architecture
        class SimpleTabNet(nn.Module):
            def __init__(self, input_dim, hidden_dim=128, output_dim=1):
                super().__init__()
                self.fc1 = nn.Linear(input_dim, hidden_dim)
                self.fc2 = nn.Linear(hidden_dim, hidden_dim)
                self.fc3 = nn.Linear(hidden_dim, hidden_dim // 2)
                self.fc4 = nn.Linear(hidden_dim // 2, output_dim)
                self.bn1 = nn.BatchNorm1d(hidden_dim)
                self.bn2 = nn.BatchNorm1d(hidden_dim)
                self.dropout = nn.Dropout(0.2)
                
            def forward(self, x):
                x = F.relu(self.bn1(self.fc1(x)))
                x = self.dropout(x)
                x = F.relu(self.bn2(self.fc2(x)))
                x = self.dropout(x)
                x = F.relu(self.fc3(x))
                x = torch.sigmoid(self.fc4(x))
                return x
        
        return SimpleTabNet(input_dim, self.n_d).to(self.device)
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Train TabNet model."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available")
        
        self.logger.info(f"Training TabNet on {len(X)} samples")
        
        # Prepare data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train.values).to(self.device)
        y_train_tensor = torch.FloatTensor(y_train.values).unsqueeze(1).to(self.device)
        X_val_tensor = torch.FloatTensor(X_val.values).to(self.device)
        y_val_tensor = torch.FloatTensor(y_val.values).unsqueeze(1).to(self.device)
        
        # Create dataloaders
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
        
        # Build model
        self.model = self._build_model(X.shape[1])
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        criterion = nn.BCELoss()
        
        # Training loop
        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        for epoch in range(self.epochs):
            self.model.train()
            train_loss = 0.0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
            
            # Validation
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val_tensor)
                val_loss = criterion(val_outputs, y_val_tensor).item()
                val_preds = val_outputs.cpu().numpy().flatten()
                val_auc = roc_auc_score(y_val, val_preds)
            
            if epoch % 10 == 0:
                self.logger.info(f"Epoch {epoch}: train_loss={train_loss/len(train_loader):.4f}, "
                               f"val_loss={val_loss:.4f}, val_auc={val_auc:.4f}")
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    self.logger.info(f"Early stopping at epoch {epoch}")
                    break
        
        # Final evaluation
        metrics = {
            "auc": val_auc,
            "log_loss": val_loss,
        }
        
        return metrics
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities."""
        if self.model is None:
            raise ValueError("Model not trained")
        
        self.model.eval()
        X_tensor = torch.FloatTensor(X.values).to(self.device)
        
        with torch.no_grad():
            preds = self.model(X_tensor).cpu().numpy().flatten()
        
        return preds


class StackedEnsembleClassifier:
    """Stacked ensemble with multiple base models and meta-learner."""
    
    def __init__(
        self,
        use_lightgbm: bool = True,
        use_xgboost: bool = True,
        use_catboost: bool = True,
        use_tabnet: bool = False,
        meta_model: str = "logistic",
        calibrate: bool = True,
    ):
        self.logger = logger.bind(model="ensemble")
        self.use_lightgbm = use_lightgbm
        self.use_xgboost = use_xgboost
        self.use_catboost = use_catboost
        self.use_tabnet = use_tabnet and TORCH_AVAILABLE
        self.meta_model_type = meta_model
        self.calibrate = calibrate
        
        self.base_models: Dict[str, Any] = {}
        self.meta_model = None
        self.calibrator = None
        self.feature_names: List[str] = []
        
    def _train_lightgbm(self, X_train, y_train, X_val, y_val) -> lgb.Booster:
        """Train LightGBM model."""
        self.logger.info("Training LightGBM...")
        
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        params = {
            "objective": "binary",
            "metric": "auc",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.03,  # Plus lent = moins overfit
            "feature_fraction": 0.8,  # Feature sampling
            "bagging_fraction": 0.7,  # Bagging réduit
            "bagging_freq": 5,
            "max_depth": 5,  # Limiter profondeur
            "min_child_samples": 30,  # Plus conservateur
            "min_gain_to_split": 0.01,  # Éviter splits inutiles
            "lambda_l1": 0.1,  # Régularisation L1
            "lambda_l2": 0.5,  # Régularisation L2
            "verbose": -1,
        }
        
        model = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(50)],
        )
        
        return model
    
    def _train_xgboost(self, X_train, y_train, X_val, y_val) -> xgb.Booster:
        """Train XGBoost model."""
        self.logger.info("Training XGBoost...")
        
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=self.feature_names)
        dval = xgb.DMatrix(X_val, label=y_val, feature_names=self.feature_names)
        
        params = {
            "objective": "binary:logistic",
            "eval_metric": "auc",
            "max_depth": 5,  # Limiter profondeur
            "eta": 0.03,  # Plus lent
            "subsample": 0.7,  # Bagging réduit
            "colsample_bytree": 0.7,  # Feature sampling réduit
            "min_child_weight": 30,  # Plus conservateur
            "reg_alpha": 0.1,  # L1
            "reg_lambda": 1.0,  # L2
            "tree_method": "auto",
        }
        
        model = xgb.train(
            params,
            dtrain,
            num_boost_round=500,
            evals=[(dval, "validation")],
            early_stopping_rounds=50,
            verbose_eval=50,
        )
        
        return model
    
    def _train_catboost(self, X_train, y_train, X_val, y_val) -> CatBoostClassifier:
        """Train CatBoost model."""
        self.logger.info("Training CatBoost...")
        
        model = CatBoostClassifier(
            iterations=500,
            learning_rate=0.03,  # Plus lent
            depth=5,  # Limiter profondeur
            l2_leaf_reg=5,  # Régularisation plus forte
            random_seed=42,
            verbose=50,
            early_stopping_rounds=50,
        )
        
        model.fit(
            X_train, y_train,
            eval_set=(X_val, y_val),
            use_best_model=True,
        )
        
        return model
    
    def _train_tabnet(self, X_train, y_train) -> TabNetClassifier:
        """Train TabNet model."""
        self.logger.info("Training TabNet...")
        
        model = TabNetClassifier(epochs=50, batch_size=256)
        model.train(pd.DataFrame(X_train, columns=self.feature_names), pd.Series(y_train))
        
        return model
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Train ensemble model."""
        self.logger.info(f"Training ensemble on {len(X)} samples with {X.shape[1]} features")
        
        self.feature_names = X.columns.tolist()
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train base models
        base_predictions_train = []
        base_predictions_val = []
        
        if self.use_lightgbm:
            lgb_model = self._train_lightgbm(X_train, y_train, X_val, y_val)
            self.base_models['lightgbm'] = lgb_model
            
            base_predictions_train.append(lgb_model.predict(X_train))
            base_predictions_val.append(lgb_model.predict(X_val))
        
        if self.use_xgboost:
            xgb_model = self._train_xgboost(X_train, y_train, X_val, y_val)
            self.base_models['xgboost'] = xgb_model
            
            dtrain = xgb.DMatrix(X_train, feature_names=self.feature_names)
            dval = xgb.DMatrix(X_val, feature_names=self.feature_names)
            base_predictions_train.append(xgb_model.predict(dtrain))
            base_predictions_val.append(xgb_model.predict(dval))
        
        if self.use_catboost:
            cat_model = self._train_catboost(X_train, y_train, X_val, y_val)
            self.base_models['catboost'] = cat_model
            
            base_predictions_train.append(cat_model.predict_proba(X_train)[:, 1])
            base_predictions_val.append(cat_model.predict_proba(X_val)[:, 1])
        
        if self.use_tabnet and TORCH_AVAILABLE:
            tabnet_model = self._train_tabnet(X_train, y_train)
            self.base_models['tabnet'] = tabnet_model
            
            base_predictions_train.append(tabnet_model.predict_proba(pd.DataFrame(X_train, columns=self.feature_names)))
            base_predictions_val.append(tabnet_model.predict_proba(pd.DataFrame(X_val, columns=self.feature_names)))
        
        # Stack predictions
        meta_X_train = np.column_stack(base_predictions_train)
        meta_X_val = np.column_stack(base_predictions_val)
        
        self.logger.info(f"Training meta-model on {len(self.base_models)} base models")
        
        # Train meta-model
        if self.meta_model_type == "logistic":
            self.meta_model = LogisticRegression(max_iter=1000, random_state=42)
        elif self.meta_model_type == "lightgbm":
            params = {
                "objective": "binary",
                "metric": "auc",
                "num_leaves": 7,
                "learning_rate": 0.05,
                "verbose": -1,
            }
            train_data = lgb.Dataset(meta_X_train, label=y_train)
            self.meta_model = lgb.train(params, train_data, num_boost_round=100)
        else:
            raise ValueError(f"Unknown meta model type: {self.meta_model_type}")
        
        if self.meta_model_type == "logistic":
            self.meta_model.fit(meta_X_train, y_train)
            meta_preds = self.meta_model.predict_proba(meta_X_val)[:, 1]
        else:
            meta_preds = self.meta_model.predict(meta_X_val)
        
        # Calibrate
        if self.calibrate and self.meta_model_type == "logistic":
            self.logger.info("Calibrating ensemble...")
            # Use direct calibration on meta model (simpler approach)
            self.calibrator = CalibratedClassifierCV(
                self.meta_model, 
                method="isotonic", 
                cv="prefit"
            )
            self.calibrator.fit(meta_X_val, y_val)
            # Update meta predictions with calibrated predictions
            meta_preds = self.calibrator.predict_proba(meta_X_val)[:, 1]
        
        # Evaluate
        val_auc = roc_auc_score(y_val, meta_preds)
        val_ap = average_precision_score(y_val, meta_preds)
        
        metrics = {
            "auc": val_auc,
            "average_precision": val_ap,
            "n_base_models": len(self.base_models),
        }
        
        self.logger.info(f"Ensemble AUC: {val_auc:.4f}, AP: {val_ap:.4f}")
        
        return metrics
    
    def _get_base_predictions(self, X: pd.DataFrame) -> List[np.ndarray]:
        """Get predictions from all base models."""
        predictions = []
        
        if 'lightgbm' in self.base_models:
            predictions.append(self.base_models['lightgbm'].predict(X))
        
        if 'xgboost' in self.base_models:
            dmat = xgb.DMatrix(X, feature_names=self.feature_names)
            predictions.append(self.base_models['xgboost'].predict(dmat))
        
        if 'catboost' in self.base_models:
            predictions.append(self.base_models['catboost'].predict_proba(X)[:, 1])
        
        if 'tabnet' in self.base_models:
            predictions.append(self.base_models['tabnet'].predict_proba(X))
        
        return predictions
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities with ensemble."""
        base_preds = self._get_base_predictions(X)
        meta_X = np.column_stack(base_preds)
        
        if self.calibrator:
            return self.calibrator.predict_proba(meta_X)[:, 1]
        elif self.meta_model_type == "logistic":
            return self.meta_model.predict_proba(meta_X)[:, 1]
        else:
            return self.meta_model.predict(meta_X)
    
    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Predict binary class."""
        proba = self.predict_proba(X)
        return (proba >= threshold).astype(int)
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get aggregated feature importance."""
        importances = []
        
        if 'lightgbm' in self.base_models:
            lgb_imp = pd.DataFrame({
                'feature': self.feature_names,
                'importance_lgb': self.base_models['lightgbm'].feature_importance(importance_type='gain')
            })
            importances.append(lgb_imp)
        
        if 'xgboost' in self.base_models:
            xgb_imp = self.base_models['xgboost'].get_score(importance_type='gain')
            xgb_df = pd.DataFrame({
                'feature': list(xgb_imp.keys()),
                'importance_xgb': list(xgb_imp.values())
            })
            importances.append(xgb_df)
        
        if 'catboost' in self.base_models:
            cat_imp = pd.DataFrame({
                'feature': self.feature_names,
                'importance_cat': self.base_models['catboost'].get_feature_importance()
            })
            importances.append(cat_imp)
        
        # Merge all
        if importances:
            result = importances[0]
            for imp in importances[1:]:
                result = result.merge(imp, on='feature', how='outer')
            
            # Average importance
            imp_cols = [c for c in result.columns if c.startswith('importance_')]
            result['importance_avg'] = result[imp_cols].mean(axis=1)
            result = result.sort_values('importance_avg', ascending=False)
            
            return result
        
        return pd.DataFrame()
    
    def save(self, path: Path) -> None:
        """Save ensemble model."""
        model_data = {
            'base_models': self.base_models,
            'meta_model': self.meta_model,
            'calibrator': self.calibrator,
            'feature_names': self.feature_names,
            'config': {
                'use_lightgbm': self.use_lightgbm,
                'use_xgboost': self.use_xgboost,
                'use_catboost': self.use_catboost,
                'use_tabnet': self.use_tabnet,
                'meta_model_type': self.meta_model_type,
                'calibrate': self.calibrate,
            }
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        self.logger.info(f"Ensemble saved to {path}")
    
    def load(self, path: Path) -> None:
        """Load ensemble model."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.base_models = model_data['base_models']
        self.meta_model = model_data['meta_model']
        self.calibrator = model_data.get('calibrator')
        self.feature_names = model_data['feature_names']
        
        config = model_data['config']
        self.use_lightgbm = config['use_lightgbm']
        self.use_xgboost = config['use_xgboost']
        self.use_catboost = config['use_catboost']
        self.use_tabnet = config['use_tabnet']
        self.meta_model_type = config['meta_model_type']
        self.calibrate = config['calibrate']
        
        self.logger.info(f"Ensemble loaded from {path}")


class AutoMLClassifier:
    """AutoML with Optuna hyperparameter optimization."""
    
    def __init__(
        self,
        base_model: str = "lightgbm",
        n_trials: int = 50,
        timeout: Optional[int] = 3600,
    ):
        self.logger = logger.bind(model="automl")
        self.base_model = base_model
        self.n_trials = n_trials
        self.timeout = timeout
        
        self.best_model = None
        self.best_params = None
        self.study = None
        
    def _objective_lightgbm(self, trial: optuna.Trial, X_train, y_train, X_val, y_val):
        """Optuna objective for LightGBM."""
        params = {
            "objective": "binary",
            "metric": "auc",
            "boosting_type": trial.suggest_categorical("boosting_type", ["gbdt", "dart"]),
            "num_leaves": trial.suggest_int("num_leaves", 20, 100),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
            "feature_fraction": trial.suggest_float("feature_fraction", 0.6, 1.0),
            "bagging_fraction": trial.suggest_float("bagging_fraction", 0.6, 1.0),
            "bagging_freq": trial.suggest_int("bagging_freq", 1, 10),
            "max_depth": trial.suggest_int("max_depth", 5, 15),
            "min_child_samples": trial.suggest_int("min_child_samples", 10, 50),
            "lambda_l1": trial.suggest_float("lambda_l1", 1e-8, 10.0, log=True),
            "lambda_l2": trial.suggest_float("lambda_l2", 1e-8, 10.0, log=True),
            "verbose": -1,
        }
        
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        model = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(50)],
        )
        
        preds = model.predict(X_val)
        auc = roc_auc_score(y_val, preds)
        
        return auc
    
    def optimize(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Run hyperparameter optimization."""
        if not OPTUNA_AVAILABLE:
            raise RuntimeError("Optuna not available")
        
        self.logger.info(f"Starting AutoML optimization with {self.n_trials} trials")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Create study
        self.study = optuna.create_study(
            direction="maximize",
            sampler=TPESampler(seed=42),
            study_name="viral_prediction_automl"
        )
        
        # Optimize
        if self.base_model == "lightgbm":
            objective = lambda trial: self._objective_lightgbm(trial, X_train, y_train, X_val, y_val)
        else:
            raise ValueError(f"Unknown base model: {self.base_model}")
        
        self.study.optimize(objective, n_trials=self.n_trials, timeout=self.timeout, show_progress_bar=True)
        
        # Train best model
        self.best_params = self.study.best_params
        self.logger.info(f"Best AUC: {self.study.best_value:.4f}")
        self.logger.info(f"Best params: {self.best_params}")
        
        # Train final model with best params
        if self.base_model == "lightgbm":
            params = {**self.best_params, "objective": "binary", "metric": "auc", "verbose": -1}
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            self.best_model = lgb.train(
                params,
                train_data,
                num_boost_round=500,
                valid_sets=[val_data],
                callbacks=[lgb.early_stopping(50)],
            )
        
        return {
            "best_auc": self.study.best_value,
            "best_params": self.best_params,
            "n_trials": len(self.study.trials),
        }
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities."""
        if self.best_model is None:
            raise ValueError("Model not optimized")
        
        return self.best_model.predict(X)
