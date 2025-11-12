"""
Train advanced ensemble model (LightGBM + XGBoost + CatBoost).
"""

import argparse
from pathlib import Path

import pandas as pd
from loguru import logger

from src.core.config import settings
from src.services.scoring.advanced_ensemble import EnsembleVotingModel


def load_training_data() -> tuple[pd.DataFrame, pd.Series]:
    """Load augmented features and labels."""
    logger.info("Loading training data...")
    
    # Load latest features (prefer advanced > augmented > regular)
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
    
    # Load labels
    label_files = sorted(settings.data_labels_path.glob("labels_*.parquet"))
    if label_files:
        labels_df = pd.read_parquet(label_files[-1])
        # Support both 'is_breakout' and 'label' column names
        if "is_breakout" in labels_df.columns:
            y = labels_df["is_breakout"]
        elif "label" in labels_df.columns:
            y = labels_df["label"]
        else:
            raise ValueError("Labels must have 'is_breakout' or 'label' column")
    else:
        # Synthetic labels
        import numpy as np
        y = pd.Series(np.random.randint(0, 2, len(features_df)))
    
    # Align lengths
    min_len = min(len(features_df), len(y))
    features_df = features_df.iloc[:min_len]
    y = y.iloc[:min_len]
    
    # Extract ALL numeric features (embeddings + advanced)
    numeric_cols = features_df.select_dtypes(include=["int", "float", "bool"]).columns.tolist()
    # Remove label columns if present
    for label_col in ["is_breakout", "label"]:
        if label_col in numeric_cols:
            numeric_cols.remove(label_col)
    
    if not numeric_cols:
        raise ValueError("No numeric features found!")
    
    X = features_df[numeric_cols]
    
    logger.info(f"Training data: {len(X)} samples, {len(numeric_cols)} features")
    logger.info(f"Features: {len([c for c in numeric_cols if c.startswith('emb_')])} embeddings + {len([c for c in numeric_cols if not c.startswith('emb_')])} advanced")
    logger.info(f"Class distribution: {y.value_counts().to_dict()}")
    
    return X, y


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description="Train ensemble model")
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.models_path / "ensemble_model.pkl",
        help="Output model path"
    )
    parser.add_argument(
        "--optimize-weights",
        action="store_true",
        help="Optimize voting weights on validation set"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force training even if model exists"
    )
    
    args = parser.parse_args()
    
    # Check if model exists
    if args.output.exists() and not args.force:
        logger.warning(f"Model already exists at {args.output}. Use --force to overwrite.")
        return
    
    try:
        # Load data
        X, y = load_training_data()
        
        # Create and train ensemble
        model = EnsembleVotingModel()
        metrics = model.train(
            X, y,
            test_size=0.2,
            optimize_weights=args.optimize_weights
        )
        
        # Save model
        model.save(args.output)
        
        # Save metrics
        import json
        metrics_path = args.output.with_suffix('.json')
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metrics saved to {metrics_path}")
        
        print("\n" + "=" * 60)
        print("ENSEMBLE TRAINING COMPLETE")
        print("=" * 60)
        print(f"Model: {args.output}")
        print(f"Samples: {len(X)}")
        print(f"Features: {X.shape[1]}")
        print()
        print("Individual Models:")
        print(f"  LightGBM AUC: {metrics['lightgbm']['auc']:.4f}")
        print(f"  XGBoost  AUC: {metrics['xgboost']['auc']:.4f}")
        print(f"  CatBoost AUC: {metrics['catboost']['auc']:.4f}")
        print()
        print(f"Ensemble AUC: {metrics['ensemble']['auc']:.4f} ✨")
        print(f"Ensemble Accuracy: {metrics['ensemble']['accuracy']:.4f}")
        print(f"Ensemble Precision: {metrics['ensemble']['precision']:.4f}")
        print(f"Ensemble Recall: {metrics['ensemble']['recall']:.4f}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
