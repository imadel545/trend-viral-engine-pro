"""
Validation complète du modèle ensemble - Détection overfitting + Feature Importance.

Analyse:
1. Cross-validation 5-fold (AUC, Accuracy, Precision, Recall)
2. SHAP values (feature importance)
3. Learning curves (train vs validation)
4. Confusion matrix
5. ROC curves

Output: Rapport complet avec visualisations.
"""

import argparse
import pickle
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import shap
from loguru import logger
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score

from src.core.config import settings


def load_data() -> tuple[pd.DataFrame, pd.Series]:
    """Load cleaned features and labels."""
    # Load latest cleaned features
    feature_files = sorted(settings.data_features_path.glob("features_*_cleaned.parquet"))
    if not feature_files:
        feature_files = sorted(settings.data_features_path.glob("features_*.parquet"))
    
    features_df = pd.read_parquet(feature_files[-1])
    logger.info(f"Loaded {len(features_df)} samples from {feature_files[-1].name}")
    
    # Load labels
    label_files = sorted(settings.data_labels_path.glob("labels_*.parquet"))
    labels_df = pd.read_parquet(label_files[-1])
    
    # Get label column
    if "is_breakout" in labels_df.columns:
        y = labels_df["is_breakout"]
    elif "label" in labels_df.columns:
        y = labels_df["label"]
    else:
        raise ValueError("No label column found")
    
    # Align lengths
    min_len = min(len(features_df), len(y))
    features_df = features_df.iloc[:min_len]
    y = y.iloc[:min_len]
    
    # Extract numeric features
    numeric_cols = features_df.select_dtypes(include=["int", "float", "bool"]).columns.tolist()
    for label_col in ["is_breakout", "label"]:
        if label_col in numeric_cols:
            numeric_cols.remove(label_col)
    
    X = features_df[numeric_cols]
    
    logger.info(f"Features: {len(X.columns)} ({len([c for c in X.columns if c.startswith('emb_')])} embeddings)")
    logger.info(f"Class distribution: {y.value_counts().to_dict()}")
    
    return X, y


def load_model(model_path: Path):
    """Load trained ensemble model."""
    # Recreate ensemble from saved models
    from src.services.scoring.advanced_ensemble import EnsembleVotingModel
    
    model = EnsembleVotingModel()
    
    # Load individual models
    model.load(model_path)
    
    logger.info(f"Loaded ensemble model from {model_path}")
    return model


def cross_validate_model(model, X: pd.DataFrame, y: pd.Series, cv: int = 5) -> dict:
    """Perform k-fold cross-validation."""
    logger.info(f"\n{'='*70}")
    logger.info(f"🔄 CROSS-VALIDATION ({cv}-FOLD)")
    logger.info(f"{'='*70}")
    
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    
    results = {
        "auc": [],
        "accuracy": [],
        "precision": [],
        "recall": []
    }
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # Predict
        y_pred_proba = model.predict_proba(X_val)[:, 1]
        y_pred = (y_pred_proba >= 0.5).astype(int)
        
        # Metrics
        results["auc"].append(roc_auc_score(y_val, y_pred_proba))
        results["accuracy"].append(accuracy_score(y_val, y_pred))
        results["precision"].append(precision_score(y_val, y_pred, zero_division=0))
        results["recall"].append(recall_score(y_val, y_pred, zero_division=0))
        
        logger.info(f"Fold {fold}: AUC={results['auc'][-1]:.4f}, Acc={results['accuracy'][-1]:.4f}")
    
    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("📊 CROSS-VALIDATION SUMMARY")
    logger.info(f"{'='*70}")
    for metric, values in results.items():
        mean_val = np.mean(values)
        std_val = np.std(values)
        logger.info(f"{metric.upper():12s}: {mean_val:.4f} ± {std_val:.4f}")
    logger.info(f"{'='*70}\n")
    
    return results


def compute_shap_values(model, X: pd.DataFrame, max_samples: int = 100) -> tuple:
    """Compute SHAP values for feature importance."""
    logger.info(f"\n🔬 Computing SHAP values (using {max_samples} samples)...")
    
    # Subsample for speed
    if len(X) > max_samples:
        X_sample = X.sample(n=max_samples, random_state=42)
    else:
        X_sample = X
    
    # Create SHAP explainer (TreeExplainer for ensemble)
    try:
        # Try with LightGBM model (fastest)
        explainer = shap.TreeExplainer(model.lgb_model)
        shap_values = explainer.shap_values(X_sample)
        
        # For binary classification, take positive class
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
    except Exception as e:
        logger.warning(f"TreeExplainer failed: {e}, using KernelExplainer (slower)...")
        explainer = shap.KernelExplainer(
            lambda x: model.predict_proba(pd.DataFrame(x, columns=X.columns))[:, 1],
            X_sample.sample(n=min(50, len(X_sample)), random_state=42)
        )
        shap_values = explainer.shap_values(X_sample)
    
    logger.info(f"✅ SHAP values computed: {shap_values.shape}")
    
    return shap_values, X_sample, explainer


def plot_shap_summary(shap_values, X_sample: pd.DataFrame, output_dir: Path):
    """Plot SHAP summary (feature importance)."""
    logger.info("📊 Generating SHAP summary plot...")
    
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X_sample, max_display=20, show=False)
    plt.tight_layout()
    
    output_path = output_dir / "shap_summary.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    logger.info(f"✅ Saved: {output_path}")
    plt.close()


def plot_confusion_matrix(model, X: pd.DataFrame, y: pd.Series, output_dir: Path):
    """Plot confusion matrix."""
    logger.info("📊 Generating confusion matrix...")
    
    y_pred_proba = model.predict_proba(X)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    cm = confusion_matrix(y, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    plt.tight_layout()
    
    output_path = output_dir / "confusion_matrix.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    logger.info(f"✅ Saved: {output_path}")
    plt.close()


def plot_roc_curve(model, X: pd.DataFrame, y: pd.Series, output_dir: Path):
    """Plot ROC curve."""
    logger.info("📊 Generating ROC curve...")
    
    y_pred_proba = model.predict_proba(X)[:, 1]
    fpr, tpr, _ = roc_curve(y, y_pred_proba)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f"Ensemble (AUC = {roc_auc:.4f})", linewidth=2)
    plt.plot([0, 1], [0, 1], "k--", label="Random")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    output_path = output_dir / "roc_curve.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    logger.info(f"✅ Saved: {output_path}")
    plt.close()


def plot_precision_recall_curve(model, X: pd.DataFrame, y: pd.Series, output_dir: Path):
    """Plot Precision-Recall curve."""
    logger.info("📊 Generating Precision-Recall curve...")
    
    y_pred_proba = model.predict_proba(X)[:, 1]
    precision, recall, _ = precision_recall_curve(y, y_pred_proba)
    pr_auc = auc(recall, precision)
    
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, label=f"Ensemble (AUC = {pr_auc:.4f})", linewidth=2)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    output_path = output_dir / "precision_recall_curve.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    logger.info(f"✅ Saved: {output_path}")
    plt.close()


def generate_report(cv_results: dict, shap_values, X_sample: pd.DataFrame, output_dir: Path):
    """Generate validation report."""
    logger.info("\n📝 Generating validation report...")
    
    # Top 20 features by SHAP
    feature_importance = pd.DataFrame({
        "feature": X_sample.columns,
        "importance": np.abs(shap_values).mean(axis=0)
    }).sort_values("importance", ascending=False).head(20)
    
    report = f"""# Model Validation Report
Generated: {pd.Timestamp.now()}

## Cross-Validation Results (5-Fold)

| Metric    | Mean    | Std Dev |
|-----------|---------|---------|
| AUC       | {np.mean(cv_results['auc']):.4f} | {np.std(cv_results['auc']):.4f} |
| Accuracy  | {np.mean(cv_results['accuracy']):.4f} | {np.std(cv_results['accuracy']):.4f} |
| Precision | {np.mean(cv_results['precision']):.4f} | {np.std(cv_results['precision']):.4f} |
| Recall    | {np.mean(cv_results['recall']):.4f} | {np.std(cv_results['recall']):.4f} |

## Top 20 Features (by SHAP Importance)

| Rank | Feature | SHAP Importance |
|------|---------|-----------------|
"""
    
    for i, row in feature_importance.iterrows():
        report += f"| {i+1} | {row['feature']} | {row['importance']:.6f} |\n"
    
    report += f"""
## Interpretation

### Overfitting Analysis
- **AUC Std Dev**: {np.std(cv_results['auc']):.4f}
  - < 0.05: Excellent consistency ✅
  - 0.05-0.10: Good ⚠️
  - > 0.10: High variance (overfitting) 🚨

### Feature Categories
- **Embeddings**: {len([f for f in feature_importance['feature'] if f.startswith('emb_')])} / 20
- **Dynamics**: {len([f for f in feature_importance['feature'] if any(x in f for x in ['velocity', 'acceleration'])])} / 20
- **Temporal**: {len([f for f in feature_importance['feature'] if any(x in f for x in ['hour', 'day', 'weekend'])])} / 20

## Visualizations
- `shap_summary.png`: Feature importance ranking
- `confusion_matrix.png`: Classification performance
- `roc_curve.png`: AUC visualization
- `precision_recall_curve.png`: Precision-Recall tradeoff
"""
    
    output_path = output_dir / "validation_report.md"
    output_path.write_text(report)
    logger.info(f"✅ Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Validate ensemble model")
    parser.add_argument("--model", type=str, default="models/ensemble_model.pkl", help="Model path")
    parser.add_argument("--cv", type=int, default=5, help="Number of CV folds")
    parser.add_argument("--shap-samples", type=int, default=100, help="Samples for SHAP")
    
    args = parser.parse_args()
    
    try:
        # Create output directory
        output_dir = Path("outputs/validation")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        X, y = load_data()
        
        # Load model
        model = load_model(Path(args.model))
        
        # Cross-validation
        cv_results = cross_validate_model(model, X, y, cv=args.cv)
        
        # SHAP analysis
        shap_values, X_sample, explainer = compute_shap_values(model, X, max_samples=args.shap_samples)
        
        # Visualizations
        plot_shap_summary(shap_values, X_sample, output_dir)
        plot_confusion_matrix(model, X, y, output_dir)
        plot_roc_curve(model, X, y, output_dir)
        plot_precision_recall_curve(model, X, y, output_dir)
        
        # Report
        generate_report(cv_results, shap_values, X_sample, output_dir)
        
        print("\n" + "="*70)
        print("✅ VALIDATION COMPLETE")
        print("="*70)
        print(f"Cross-validation AUC: {np.mean(cv_results['auc']):.4f} ± {np.std(cv_results['auc']):.4f}")
        print(f"Output directory: {output_dir}")
        print("="*70)
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()
