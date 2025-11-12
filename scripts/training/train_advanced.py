"""
Advanced Training Script - Train State-of-the-Art ML Models
Usage: python scripts/training/train_advanced.py --model ensemble --optimize
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from loguru import logger

from src.core.config import settings
from src.services.features.enhanced_service import get_enhanced_feature_service
from src.services.scoring.enhanced_service import get_enhanced_scoring_service


def load_training_data() -> tuple[pd.DataFrame, pd.Series]:
    """Load and prepare training data."""
    logger.info("Loading training data...")
    
    # Load features
    features_path = settings.data_features_path
    feature_files = sorted(features_path.glob("*.parquet"))
    
    if not feature_files:
        raise FileNotFoundError(f"No feature files found in {features_path}")
    
    logger.info(f"Found {len(feature_files)} feature files")
    
    # Load most recent
    latest_features = feature_files[-1]
    X = pd.read_parquet(latest_features)
    
    logger.info(f"Loaded features from {latest_features.name}: {X.shape}")
    
    # Load labels
    labels_path = settings.data_labels_path
    label_files = sorted(labels_path.glob("*.parquet"))
    
    if not label_files:
        logger.warning("No label files found, creating synthetic labels for demo")
        # Create synthetic labels based on views threshold
        if "views" in X.columns:
            y = (X["views"] > X["views"].median()).astype(int)
        else:
            y = pd.Series([0] * len(X))
    else:
        latest_labels = label_files[-1]
        labels_df = pd.read_parquet(latest_labels)
        y = labels_df["is_breakout"]
        logger.info(f"Loaded labels from {latest_labels.name}")
    
    # Remove non-feature columns
    exclude_cols = {'topic', 'timestamp', 'collected_at', 'source', 'country', 'is_breakout'}
    feature_cols = [c for c in X.columns if c not in exclude_cols]
    
    X_clean = X[feature_cols].fillna(0)
    
    logger.info(f"✓ Prepared {len(X_clean)} samples with {len(feature_cols)} features")
    logger.info(f"  Positive class: {y.sum()} ({y.mean()*100:.1f}%)")
    
    return X_clean, y


def train_ensemble(optimize: bool = False):
    """Train ensemble model."""
    logger.info("\n" + "="*60)
    logger.info("TRAINING ENSEMBLE MODEL")
    logger.info("="*60 + "\n")
    
    # Load data
    X, y = load_training_data()
    
    if len(X) < 100:
        logger.error("Insufficient data for training (need at least 100 samples)")
        return
    
    # Get service
    scoring_service = get_enhanced_scoring_service()
    
    # Train
    metrics = scoring_service.train_ensemble(
        X, y,
        use_lightgbm=True,
        use_xgboost=True,
        use_catboost=True,
        use_tabnet=False,  # Disable TabNet for CPU training
        meta_model="logistic",
        calibrate=True,
    )
    
    logger.info("\n" + "="*60)
    logger.info("TRAINING COMPLETE")
    logger.info("="*60)
    logger.info(f"AUC: {metrics['auc']:.4f}")
    logger.info(f"Average Precision: {metrics['average_precision']:.4f}")
    logger.info(f"Base Models: {metrics['n_base_models']}")
    
    # Feature importance
    importance = scoring_service.get_feature_importance()
    if importance is not None:
        logger.info("\nTop 10 Most Important Features:")
        for i, (idx, row) in enumerate(importance.head(10).iterrows(), 1):
            logger.info(f"  {i}. {row['feature']}: {row['importance_avg']:.2f}")


def train_automl(n_trials: int = 50, timeout: int = 3600):
    """Train model with AutoML."""
    logger.info("\n" + "="*60)
    logger.info("TRAINING WITH AUTOML")
    logger.info("="*60 + "\n")
    
    # Load data
    X, y = load_training_data()
    
    if len(X) < 100:
        logger.error("Insufficient data for training (need at least 100 samples)")
        return
    
    # Get service
    scoring_service = get_enhanced_scoring_service()
    
    # Optimize
    results = scoring_service.train_automl(
        X, y,
        n_trials=n_trials,
        timeout=timeout,
    )
    
    logger.info("\n" + "="*60)
    logger.info("AUTOML OPTIMIZATION COMPLETE")
    logger.info("="*60)
    logger.info(f"Best AUC: {results['best_auc']:.4f}")
    logger.info(f"Trials Completed: {results['n_trials']}")
    logger.info(f"\nBest Parameters:")
    for param, value in results['best_params'].items():
        logger.info(f"  {param}: {value}")


def extract_features():
    """Extract features from raw data."""
    logger.info("\n" + "="*60)
    logger.info("EXTRACTING ADVANCED FEATURES")
    logger.info("="*60 + "\n")
    
    # Get service
    feature_service = get_enhanced_feature_service()
    
    # Process raw data
    processed = feature_service.batch_process()
    
    if processed:
        # Show stats for first file
        stats = feature_service.get_feature_stats(processed[0])
        
        logger.info("\n" + "="*60)
        logger.info("FEATURE EXTRACTION COMPLETE")
        logger.info("="*60)
        logger.info(f"Samples: {stats['n_samples']}")
        logger.info(f"Features: {stats['n_features']}")
        logger.info(f"Memory: {stats['memory_usage_mb']:.2f} MB")
        logger.info(f"\nFeature Types:")
        for ftype, count in stats['feature_types'].items():
            logger.info(f"  {ftype}: {count}")


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description="Train advanced ML models")
    
    parser.add_argument(
        "--model",
        type=str,
        choices=["ensemble", "automl", "features"],
        default="ensemble",
        help="Model type to train"
    )
    
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Use AutoML for hyperparameter optimization"
    )
    
    parser.add_argument(
        "--n-trials",
        type=int,
        default=50,
        help="Number of Optuna trials for AutoML"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Timeout in seconds for AutoML"
    )
    
    args = parser.parse_args()
    
    # Ensure directories exist
    settings.ensure_directories()
    
    try:
        if args.model == "features":
            extract_features()
        elif args.model == "ensemble":
            train_ensemble(optimize=args.optimize)
        elif args.model == "automl":
            train_automl(n_trials=args.n_trials, timeout=args.timeout)
        
        logger.info("\n✓ Training pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
