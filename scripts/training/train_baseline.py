"""
Training script for baseline LightGBM model.
"""

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from src.core.config import settings
from src.services.scoring import LightGBMModel


def load_training_data() -> tuple[pd.DataFrame, pd.Series]:
    """Load features and labels for training."""
    logger.info("Loading training data...")

    # Load latest features (prefer augmented/advanced files with most features)
    feature_files = sorted(settings.data_features_path.glob("*features*.parquet"))
    if not feature_files:
        raise ValueError(f"No feature files found in {settings.data_features_path}")

    # Priority: advanced > augmented > regular
    selected_file = None
    for f in reversed(feature_files):
        if 'advanced' in f.name:
            selected_file = f
            break
    
    if selected_file is None:
        for f in reversed(feature_files):
            if 'augmented' in f.name:
                selected_file = f
                break
    
    if selected_file is None:
        selected_file = feature_files[-1]
    
    features_df = pd.read_parquet(selected_file)
    logger.info(f"Loaded {len(features_df)} rows from {selected_file.name}")

    # Load matching labels (same timestamp if possible)
    label_files = sorted(settings.data_labels_path.glob("labels_*.parquet"))
    if not label_files:
        logger.warning("No label files found - creating synthetic labels for MVP testing")
        # Create synthetic labels based on engagement metrics
        labels_df = features_df[[]].copy()  # Empty df with same index
        
        # Synthetic label: high engagement = breakout
        # Use score, upvote_ratio, rank, etc.
        if "score" in features_df.columns:
            labels_df["is_breakout"] = (features_df["score"] > features_df["score"].median()).astype(int)
        elif "rank" in features_df.columns:
            labels_df["is_breakout"] = (features_df["rank"] <= 3).astype(int)
        else:
            # Random for testing
            import numpy as np
            labels_df["is_breakout"] = np.random.randint(0, 2, len(features_df))
        
        logger.info(f"Created {len(labels_df)} synthetic labels (positive rate: {labels_df['is_breakout'].mean():.2%})")
    else:
        labels_df = pd.read_parquet(label_files[-1])
        logger.info(f"Loaded labels from {label_files[-1]}")

    # Align lengths
    if len(features_df) != len(labels_df):
        logger.warning(f"Mismatched lengths: {len(features_df)} features vs {len(labels_df)} labels")
        min_len = min(len(features_df), len(labels_df))
        features_df = features_df.iloc[:min_len]
        labels_df = labels_df.iloc[:min_len]

    # PHASE 1 FIX (P1): Use ONLY API-compatible features (embeddings + temporal)
    # This ensures training/inference consistency and resolves feature mismatch.
    # Previously used ALL numeric columns (554 features), now matches API (387 features).
    
    # Define allowed prefixes (same as FeaturePreprocessor)
    allowed_prefixes = ["emb_", "temporal_"]
    
    # Get numeric columns
    numeric_cols = features_df.select_dtypes(include=["int", "float", "bool"]).columns.tolist()
    
    # Filter to API-compatible features only
    feature_cols = [
        col for col in numeric_cols 
        if any(col.startswith(prefix) for prefix in allowed_prefixes)
    ]
    
    # Also exclude label column if present
    if "is_breakout" in feature_cols:
        feature_cols.remove("is_breakout")
    if "label" in feature_cols:
        feature_cols.remove("label")
    
    if not feature_cols:
        raise ValueError(
            f"No feature columns found matching prefixes {allowed_prefixes}! "
            f"Run feature extraction first."
        )
    
    # Count feature types for logging
    emb_cols = [c for c in feature_cols if c.startswith("emb_")]
    temporal_cols = [c for c in feature_cols if c.startswith("temporal_")]
    
    logger.info(f"✓ Using {len(feature_cols)} API-compatible features:")
    logger.info(f"  - {len(emb_cols)} embeddings (emb_*)")
    logger.info(f"  - {len(temporal_cols)} temporal (temporal_*)")
    logger.info(f"  (Excluded {len(numeric_cols) - len(feature_cols)} non-API features for consistency)")
    
    X = features_df[feature_cols]
    # Support both 'is_breakout' and 'label' column names
    if "is_breakout" in labels_df.columns:
        y = labels_df["is_breakout"]
    elif "label" in labels_df.columns:
        y = labels_df["label"]
    else:
        raise ValueError("Labels must have 'is_breakout' or 'label' column")

    logger.info(f"Training data: {len(X)} samples, {len(numeric_cols)} features")

    return X, y


def train_model(X: pd.DataFrame, y: pd.Series, output_path: Path, min_samples: int = None) -> dict:
    """Train and save the model."""
    logger.info("Training LightGBM model...")

    # Check minimum samples
    min_required = min_samples if min_samples is not None else settings.min_samples_for_training
    if len(X) < min_required:
        logger.warning(
            f"Low sample count: {len(X)} < {min_required} (recommended minimum)"
        )
        if len(X) < 5:  # Absolute minimum for train/test split
            raise ValueError(f"Insufficient samples: {len(X)} < 5 (absolute minimum)")

    # Create and train model
    model = LightGBMModel()
    metrics = model.train(X, y, calibrate=False, log_mlflow=True)  # Disable calibration for MVP

    # Save model
    model.save(output_path)
    logger.info(f"Model saved to {output_path}")

    # Save metrics
    metrics_path = output_path.with_suffix(".json")
    import json

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics saved to {metrics_path}")
    logger.info(f"Training complete! AUC: {metrics['auc']:.4f}")

    return metrics


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description="Train baseline model")
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.models_path / "baseline_model.pkl",
        help="Output model path",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force training even if model exists"
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=None,
        help="Minimum samples required (default: from settings)",
    )

    args = parser.parse_args()

    # Check if model already exists
    if args.output.exists() and not args.force:
        logger.warning(f"Model already exists at {args.output}. Use --force to overwrite.")
        return

    try:
        # Load data
        X, y = load_training_data()

        # Train model
        metrics = train_model(X, y, args.output, args.min_samples)

        print("\n" + "=" * 50)
        print("TRAINING COMPLETE")
        print("=" * 50)
        print(f"Model: {args.output}")
        print(f"Samples: {len(X)}")
        print(f"Features: {X.shape[1]}")
        print(f"AUC: {metrics['auc']:.4f}")
        print(f"Accuracy: {metrics['accuracy']:.4f}")
        print(f"Precision: {metrics['precision']:.4f}")
        print(f"Recall: {metrics['recall']:.4f}")
        print("=" * 50)

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
