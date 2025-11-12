"""
Explainability & Monitoring - Production ML Best Practices
Implémente SHAP, drift detection, A/B testing, et monitoring avancé.
"""

import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    warnings.warn("SHAP not available - explainability limited")

try:
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset, DataQualityPreset, TargetDriftPreset
    from evidently.metrics import *
    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False
    warnings.warn("Evidently not available - drift detection disabled")


class SHAPExplainer:
    """SHAP-based model explainability."""
    
    def __init__(self, model, model_type: str = "lightgbm"):
        self.logger = logger.bind(component="shap")
        self.model = model
        self.model_type = model_type
        self.explainer = None
        self.base_value = None
        
    def fit(self, X_background: pd.DataFrame, max_samples: int = 100) -> None:
        """Initialize SHAP explainer with background data."""
        if not SHAP_AVAILABLE:
            self.logger.warning("SHAP not available")
            return
        
        # Sample background data if too large
        if len(X_background) > max_samples:
            X_bg = X_background.sample(n=max_samples, random_state=42)
        else:
            X_bg = X_background
        
        self.logger.info(f"Initializing SHAP explainer with {len(X_bg)} background samples")
        
        try:
            if self.model_type == "lightgbm":
                self.explainer = shap.TreeExplainer(self.model)
            elif self.model_type == "xgboost":
                self.explainer = shap.TreeExplainer(self.model)
            elif self.model_type == "ensemble":
                # Use KernelExplainer for ensemble
                def model_predict(X):
                    return self.model.predict_proba(pd.DataFrame(X, columns=X_bg.columns))
                
                self.explainer = shap.KernelExplainer(model_predict, X_bg)
            else:
                # Generic kernel explainer
                def model_predict(X):
                    return self.model.predict_proba(pd.DataFrame(X, columns=X_bg.columns))
                
                self.explainer = shap.KernelExplainer(model_predict, X_bg)
            
            self.logger.info("SHAP explainer initialized")
            
        except Exception as e:
            self.logger.error(f"SHAP explainer initialization failed: {e}")
    
    def explain(self, X: pd.DataFrame, max_samples: Optional[int] = None) -> Dict[str, Any]:
        """Generate SHAP explanations."""
        if not SHAP_AVAILABLE or self.explainer is None:
            return {}
        
        if max_samples and len(X) > max_samples:
            X_sample = X.sample(n=max_samples, random_state=42)
        else:
            X_sample = X
        
        self.logger.info(f"Computing SHAP values for {len(X_sample)} samples")
        
        try:
            shap_values = self.explainer.shap_values(X_sample)
            
            # Handle multi-output
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Take positive class
            
            # Global feature importance
            feature_importance = pd.DataFrame({
                'feature': X_sample.columns,
                'importance': np.abs(shap_values).mean(axis=0)
            }).sort_values('importance', ascending=False)
            
            # Expected value
            if hasattr(self.explainer, 'expected_value'):
                expected_value = self.explainer.expected_value
                if isinstance(expected_value, (list, np.ndarray)):
                    expected_value = expected_value[1] if len(expected_value) > 1 else expected_value[0]
            else:
                expected_value = None
            
            return {
                'shap_values': shap_values,
                'feature_importance': feature_importance,
                'expected_value': expected_value,
                'base_values': getattr(self.explainer, 'expected_value', None),
            }
            
        except Exception as e:
            self.logger.error(f"SHAP computation failed: {e}")
            return {}
    
    def explain_instance(self, instance: pd.Series, feature_names: List[str]) -> Dict[str, Any]:
        """Explain a single prediction."""
        if not SHAP_AVAILABLE or self.explainer is None:
            return {}
        
        try:
            instance_df = pd.DataFrame([instance], columns=feature_names)
            shap_values = self.explainer.shap_values(instance_df)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[1][0]
            else:
                shap_values = shap_values[0]
            
            # Create explanation
            explanation = pd.DataFrame({
                'feature': feature_names,
                'value': instance.values,
                'shap_value': shap_values,
                'abs_shap': np.abs(shap_values)
            }).sort_values('abs_shap', ascending=False)
            
            return {
                'explanation': explanation,
                'prediction_impact': explanation['shap_value'].sum(),
            }
            
        except Exception as e:
            self.logger.error(f"Instance explanation failed: {e}")
            return {}


class DriftDetector:
    """Data drift and model drift detection."""
    
    def __init__(self, reference_data: pd.DataFrame):
        self.logger = logger.bind(component="drift")
        self.reference_data = reference_data
        
    def detect_data_drift(
        self,
        current_data: pd.DataFrame,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Detect data drift between reference and current data."""
        if not EVIDENTLY_AVAILABLE:
            self.logger.warning("Evidently not available")
            return {}
        
        self.logger.info(f"Detecting drift on {len(current_data)} samples")
        
        try:
            # Create drift report
            report = Report(metrics=[
                DataDriftPreset(),
                DataQualityPreset(),
            ])
            
            report.run(reference_data=self.reference_data, current_data=current_data)
            
            # Save report
            if output_path:
                report.save_html(str(output_path))
                self.logger.info(f"Drift report saved to {output_path}")
            
            # Extract metrics
            results = report.as_dict()
            
            drift_summary = {
                'n_drifted_features': 0,
                'drift_share': 0.0,
                'drifted_features': [],
            }
            
            # Parse results
            if 'metrics' in results:
                for metric in results['metrics']:
                    if metric.get('metric') == 'DataDriftTable':
                        drift_by_columns = metric.get('result', {}).get('drift_by_columns', {})
                        drift_summary['n_drifted_features'] = sum(
                            1 for col_data in drift_by_columns.values() 
                            if col_data.get('drift_detected', False)
                        )
                        drift_summary['drifted_features'] = [
                            col for col, col_data in drift_by_columns.items()
                            if col_data.get('drift_detected', False)
                        ]
                        drift_summary['drift_share'] = metric.get('result', {}).get('dataset_drift', False)
            
            self.logger.info(f"Detected drift in {drift_summary['n_drifted_features']} features")
            
            return drift_summary
            
        except Exception as e:
            self.logger.error(f"Drift detection failed: {e}")
            return {}
    
    def detect_target_drift(
        self,
        current_data: pd.DataFrame,
        target_col: str = "is_breakout",
    ) -> Dict[str, Any]:
        """Detect target drift."""
        if not EVIDENTLY_AVAILABLE:
            return {}
        
        if target_col not in self.reference_data.columns or target_col not in current_data.columns:
            self.logger.warning(f"Target column {target_col} not found")
            return {}
        
        try:
            report = Report(metrics=[
                TargetDriftPreset(),
            ])
            
            report.run(
                reference_data=self.reference_data,
                current_data=current_data,
                column_mapping={'target': target_col}
            )
            
            results = report.as_dict()
            
            return {
                'target_drift_detected': results.get('metrics', [{}])[0].get('result', {}).get('drift_detected', False),
            }
            
        except Exception as e:
            self.logger.error(f"Target drift detection failed: {e}")
            return {}


class ABTestFramework:
    """A/B testing framework for model comparison."""
    
    def __init__(self):
        self.logger = logger.bind(component="ab_test")
        self.experiments: Dict[str, Dict[str, Any]] = {}
        
    def create_experiment(
        self,
        experiment_id: str,
        variant_a: str,
        variant_b: str,
        traffic_split: float = 0.5,
    ) -> None:
        """Create a new A/B test experiment."""
        self.experiments[experiment_id] = {
            'variant_a': variant_a,
            'variant_b': variant_b,
            'traffic_split': traffic_split,
            'results_a': [],
            'results_b': [],
            'created_at': datetime.now(),
        }
        
        self.logger.info(f"Created experiment {experiment_id}: {variant_a} vs {variant_b}")
    
    def assign_variant(self, experiment_id: str, user_id: str) -> str:
        """Assign user to a variant."""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        exp = self.experiments[experiment_id]
        
        # Deterministic assignment based on user_id hash
        hash_val = hash(user_id) % 100 / 100.0
        
        if hash_val < exp['traffic_split']:
            return exp['variant_a']
        else:
            return exp['variant_b']
    
    def record_result(
        self,
        experiment_id: str,
        variant: str,
        metric_value: float,
    ) -> None:
        """Record experiment result."""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        exp = self.experiments[experiment_id]
        
        if variant == exp['variant_a']:
            exp['results_a'].append(metric_value)
        elif variant == exp['variant_b']:
            exp['results_b'].append(metric_value)
        else:
            raise ValueError(f"Unknown variant: {variant}")
    
    def analyze_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Analyze A/B test results."""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        exp = self.experiments[experiment_id]
        
        results_a = np.array(exp['results_a'])
        results_b = np.array(exp['results_b'])
        
        if len(results_a) == 0 or len(results_b) == 0:
            return {'status': 'insufficient_data'}
        
        # Compute statistics
        mean_a = np.mean(results_a)
        mean_b = np.mean(results_b)
        std_a = np.std(results_a)
        std_b = np.std(results_b)
        
        # Simple t-test
        from scipy import stats
        t_stat, p_value = stats.ttest_ind(results_a, results_b)
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt((std_a**2 + std_b**2) / 2)
        cohens_d = (mean_b - mean_a) / pooled_std if pooled_std > 0 else 0
        
        # Determine winner
        if p_value < 0.05:
            winner = exp['variant_b'] if mean_b > mean_a else exp['variant_a']
            confidence = (1 - p_value) * 100
        else:
            winner = "no_significant_difference"
            confidence = 50.0
        
        analysis = {
            'experiment_id': experiment_id,
            'variant_a': exp['variant_a'],
            'variant_b': exp['variant_b'],
            'mean_a': float(mean_a),
            'mean_b': float(mean_b),
            'std_a': float(std_a),
            'std_b': float(std_b),
            'n_samples_a': len(results_a),
            'n_samples_b': len(results_b),
            'p_value': float(p_value),
            'cohens_d': float(cohens_d),
            'winner': winner,
            'confidence': float(confidence),
            'lift': float((mean_b - mean_a) / mean_a * 100) if mean_a > 0 else 0,
        }
        
        self.logger.info(f"Experiment {experiment_id}: winner={winner}, lift={analysis['lift']:.2f}%")
        
        return analysis


class ProductionMonitor:
    """Production monitoring and alerting."""
    
    def __init__(self, metrics_path: Path):
        self.logger = logger.bind(component="monitor")
        self.metrics_path = metrics_path
        self.metrics_path.mkdir(parents=True, exist_ok=True)
        
        # Thresholds
        self.thresholds = {
            'auc_drop': 0.05,  # Alert if AUC drops > 5%
            'latency_ms': 500,  # Alert if latency > 500ms
            'error_rate': 0.01,  # Alert if error rate > 1%
        }
        
    def log_prediction(
        self,
        prediction_id: str,
        features: Dict[str, Any],
        prediction: float,
        latency_ms: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Log a prediction for monitoring."""
        timestamp = timestamp or datetime.now()
        
        log_entry = {
            'prediction_id': prediction_id,
            'timestamp': timestamp.isoformat(),
            'prediction': prediction,
            'latency_ms': latency_ms,
            **{f'feature_{k}': v for k, v in features.items()}
        }
        
        # Append to daily log
        date_str = timestamp.strftime("%Y%m%d")
        log_file = self.metrics_path / f"predictions_{date_str}.jsonl"
        
        import json
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def log_feedback(
        self,
        prediction_id: str,
        actual_outcome: bool,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Log feedback for a prediction."""
        timestamp = timestamp or datetime.now()
        
        feedback_entry = {
            'prediction_id': prediction_id,
            'timestamp': timestamp.isoformat(),
            'actual_outcome': actual_outcome,
        }
        
        date_str = timestamp.strftime("%Y%m%d")
        feedback_file = self.metrics_path / f"feedback_{date_str}.jsonl"
        
        import json
        with open(feedback_file, 'a') as f:
            f.write(json.dumps(feedback_entry) + '\n')
    
    def compute_metrics(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Compute daily metrics."""
        date = date or datetime.now()
        date_str = date.strftime("%Y%m%d")
        
        pred_file = self.metrics_path / f"predictions_{date_str}.jsonl"
        feedback_file = self.metrics_path / f"feedback_{date_str}.jsonl"
        
        if not pred_file.exists():
            return {'status': 'no_data'}
        
        # Load predictions
        import json
        predictions = []
        with open(pred_file, 'r') as f:
            for line in f:
                predictions.append(json.loads(line))
        
        # Load feedback if available
        feedback = {}
        if feedback_file.exists():
            with open(feedback_file, 'r') as f:
                for line in f:
                    fb = json.loads(line)
                    feedback[fb['prediction_id']] = fb['actual_outcome']
        
        # Compute metrics
        metrics = {
            'date': date_str,
            'n_predictions': len(predictions),
            'avg_latency_ms': np.mean([p['latency_ms'] for p in predictions]),
            'p50_latency_ms': np.percentile([p['latency_ms'] for p in predictions], 50),
            'p95_latency_ms': np.percentile([p['latency_ms'] for p in predictions], 95),
            'p99_latency_ms': np.percentile([p['latency_ms'] for p in predictions], 99),
        }
        
        # Compute accuracy if feedback available
        if feedback:
            matched_preds = [p for p in predictions if p['prediction_id'] in feedback]
            
            if matched_preds:
                y_true = [feedback[p['prediction_id']] for p in matched_preds]
                y_pred = [p['prediction'] for p in matched_preds]
                
                from sklearn.metrics import roc_auc_score
                metrics['auc'] = roc_auc_score(y_true, y_pred)
                metrics['n_feedback'] = len(y_true)
        
        self.logger.info(f"Metrics for {date_str}: {metrics}")
        
        return metrics
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[str]:
        """Check for alert conditions."""
        alerts = []
        
        if metrics.get('auc') and metrics['auc'] < (1 - self.thresholds['auc_drop']):
            alerts.append(f"AUC dropped to {metrics['auc']:.4f}")
        
        if metrics.get('avg_latency_ms', 0) > self.thresholds['latency_ms']:
            alerts.append(f"High latency: {metrics['avg_latency_ms']:.0f}ms")
        
        if alerts:
            self.logger.warning(f"Alerts triggered: {alerts}")
        
        return alerts
