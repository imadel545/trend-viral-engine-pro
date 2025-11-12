"""
Model evaluation script.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)

from src.core.config import settings
from src.services.scoring import LightGBMModel


def evaluate_model(model_path: Path, test_data_path: Path):
    """Evaluate a trained model."""
    logger.info(f"Evaluating model: {model_path}")

    # Load model
    model = LightGBMModel()
    model.load(model_path)

    # Load test data
    test_df = pd.read_parquet(test_data_path)
    logger.info(f"Loaded test data: {len(test_df)} samples")

    # Prepare features
    exclude_cols = ["topic", "timestamp", "source", "collected_at", "is_breakout"]
    feature_cols = [col for col in test_df.columns if col not in exclude_cols]

    X_test = test_df[feature_cols]
    y_test = test_df["is_breakout"]

    # Predictions
    y_pred_proba = model.predict_proba(X_test)
    y_pred = model.predict(X_test)

    # Metrics
    auc = roc_auc_score(y_test, y_pred_proba)

    print("\n" + "=" * 50)
    print("MODEL EVALUATION")
    print("=" * 50)
    print(f"Test samples: {len(X_test)}")
    print(f"AUC: {auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("=" * 50)

    # Plot ROC curve
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)

    plt.figure(figsize=(10, 6))
    plt.plot(fpr, tpr, label=f"ROC Curve (AUC = {auc:.4f})")
    plt.plot([0, 1], [0, 1], "k--", label="Random")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend()
    plt.grid(True)

    # Save plot
    plot_path = model_path.parent / f"roc_curve_{model_path.stem}.png"
    plt.savefig(plot_path)
    logger.info(f"ROC curve saved to {plot_path}")

    return {
        "auc": auc,
        "predictions": y_pred,
        "probabilities": y_pred_proba,
    }


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description="Evaluate model")
    parser.add_argument(
        "--model",
        type=Path,
        default=settings.models_path / "baseline_model.pkl",
        help="Model path",
    )
    parser.add_argument(
        "--test-data", type=Path, required=True, help="Test data path (parquet)"
    )

    args = parser.parse_args()

    evaluate_model(args.model, args.test_data)


if __name__ == "__main__":
    main()
