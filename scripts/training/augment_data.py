"""
Data Augmentation via SMOTE for viral trend prediction.

SMOTE (Synthetic Minority Oversampling Technique) generates synthetic samples
by interpolating between existing samples in embedding space.
This is particularly effective for small datasets (<100 samples).
"""

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
from loguru import logger
from imblearn.over_sampling import SMOTE, ADASYN, BorderlineSMOTE
from sklearn.decomposition import PCA

from src.core.config import settings


def load_features_and_labels() -> tuple[pd.DataFrame, pd.Series]:
    """Load existing features and labels."""
    logger.info("Loading features and labels for augmentation...")
    
    # Load features
    feature_files = sorted(settings.data_features_path.glob("*features*.parquet"))
    if not feature_files:
        raise ValueError(f"No feature files found in {settings.data_features_path}")
    
    dfs = [pd.read_parquet(f) for f in feature_files]
    features_df = pd.concat(dfs, ignore_index=True)
    
    # Extract embedding columns only (for SMOTE)
    emb_cols = [col for col in features_df.columns if col.startswith("emb_")]
    if not emb_cols:
        raise ValueError("No embedding features found!")
    
    X = features_df[emb_cols]
    
    # Load labels (or create synthetic)
    label_files = sorted(settings.data_labels_path.glob("labels_*.parquet"))
    if label_files:
        labels_df = pd.read_parquet(label_files[-1])
        y = labels_df["is_breakout"]
    else:
        # Create synthetic labels based on engagement
        if "score" in features_df.columns:
            y = (features_df["score"] > features_df["score"].median()).astype(int)
        else:
            y = pd.Series(np.random.randint(0, 2, len(features_df)))
    
    # Align lengths
    min_len = min(len(X), len(y))
    X = X.iloc[:min_len]
    y = y.iloc[:min_len]
    
    logger.info(f"Loaded {len(X)} samples with {len(emb_cols)} features")
    logger.info(f"Class distribution: {y.value_counts().to_dict()}")
    
    return X, y, emb_cols


def augment_with_smote(
    X: pd.DataFrame,
    y: pd.Series,
    target_samples: int = 100,
    method: str = "smote",
    random_state: int = 42
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Augment data using SMOTE or variants.
    
    Args:
        X: Features (embeddings)
        y: Labels
        target_samples: Desired number of samples after augmentation
        method: 'smote', 'borderline', or 'adasyn'
        random_state: Random seed for reproducibility
    
    Returns:
        Augmented X, y
    """
    logger.info(f"Augmenting data with {method.upper()}...")
    
    # Calculate sampling strategy
    n_current = len(X)
    if n_current >= target_samples:
        logger.warning(f"Already have {n_current} samples (target: {target_samples})")
        return X, y
    
    # Ensure at least 2 samples per class for SMOTE
    class_counts = y.value_counts()
    if (class_counts < 2).any():
        logger.error(f"Need at least 2 samples per class for SMOTE. Current: {class_counts.to_dict()}")
        raise ValueError("Insufficient samples per class for SMOTE")
    
    # For SMOTE, we need k_neighbors < minority class count
    minority_count = class_counts.min()
    k_neighbors = min(5, minority_count - 1)  # Default 5, but adapt if needed
    
    # Calculate target per class (balanced)
    n_per_class = target_samples // 2
    
    # Create SMOTE sampler
    if method == "smote":
        sampler = SMOTE(
            sampling_strategy={0: n_per_class, 1: n_per_class},
            k_neighbors=k_neighbors,
            random_state=random_state
        )
    elif method == "borderline":
        sampler = BorderlineSMOTE(
            sampling_strategy={0: n_per_class, 1: n_per_class},
            k_neighbors=k_neighbors,
            random_state=random_state
        )
    elif method == "adasyn":
        sampler = ADASYN(
            sampling_strategy={0: n_per_class, 1: n_per_class},
            n_neighbors=k_neighbors,
            random_state=random_state
        )
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Apply SMOTE
    try:
        X_resampled, y_resampled = sampler.fit_resample(X, y)
        
        logger.info(f"Augmentation complete:")
        logger.info(f"  Original: {len(X)} samples")
        logger.info(f"  Augmented: {len(X_resampled)} samples")
        logger.info(f"  New distribution: {pd.Series(y_resampled).value_counts().to_dict()}")
        
        return pd.DataFrame(X_resampled, columns=X.columns), pd.Series(y_resampled, name="is_breakout")
    
    except Exception as e:
        logger.error(f"SMOTE failed: {e}")
        raise


def add_gaussian_noise(
    X: pd.DataFrame,
    noise_factor: float = 0.01
) -> pd.DataFrame:
    """
    Add small Gaussian noise to synthetic samples for diversity.
    
    Args:
        X: Features
        noise_factor: Std of noise relative to feature std
    
    Returns:
        Features with noise
    """
    logger.info(f"Adding Gaussian noise (factor={noise_factor})...")
    
    X_noisy = X.copy()
    for col in X.columns:
        std = X[col].std()
        noise = np.random.normal(0, std * noise_factor, len(X))
        X_noisy[col] = X[col] + noise
    
    return X_noisy


def save_augmented_data(
    X: pd.DataFrame,
    y: pd.Series,
    emb_cols: list,
    output_dir: Path
) -> tuple[Path, Path]:
    """Save augmented features and labels."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save features (add metadata columns if needed)
    features_path = output_dir / f"features_augmented_{timestamp}.parquet"
    X.to_parquet(features_path, index=False)
    logger.info(f"Saved augmented features to {features_path}")
    
    # Save labels
    labels_path = settings.data_labels_path / f"labels_augmented_{timestamp}.parquet"
    labels_df = pd.DataFrame({"is_breakout": y})
    labels_df.to_parquet(labels_path, index=False)
    logger.info(f"Saved augmented labels to {labels_path}")
    
    return features_path, labels_path


def visualize_augmentation(
    X_original: pd.DataFrame,
    X_augmented: pd.DataFrame,
    y_original: pd.Series,
    y_augmented: pd.Series,
    output_path: Path = None
):
    """
    Visualize original vs augmented data in 2D (PCA).
    
    Args:
        X_original: Original features
        X_augmented: Augmented features
        y_original: Original labels
        y_augmented: Augmented labels
        output_path: Where to save plot (optional)
    """
    try:
        import matplotlib.pyplot as plt
        
        logger.info("Visualizing augmentation with PCA...")
        
        # PCA to 2D
        pca = PCA(n_components=2, random_state=42)
        X_orig_2d = pca.fit_transform(X_original)
        X_aug_2d = pca.transform(X_augmented)
        
        # Plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Original data
        ax1.scatter(X_orig_2d[:, 0], X_orig_2d[:, 1], c=y_original, cmap='coolwarm', alpha=0.7)
        ax1.set_title(f"Original Data (n={len(X_original)})")
        ax1.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})")
        ax1.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})")
        
        # Augmented data
        # Distinguish original vs synthetic
        is_synthetic = np.zeros(len(X_augmented), dtype=bool)
        is_synthetic[len(X_original):] = True
        
        ax2.scatter(X_aug_2d[~is_synthetic, 0], X_aug_2d[~is_synthetic, 1], 
                   c=y_augmented[~is_synthetic], cmap='coolwarm', alpha=0.7, label='Original', marker='o')
        ax2.scatter(X_aug_2d[is_synthetic, 0], X_aug_2d[is_synthetic, 1], 
                   c=y_augmented[is_synthetic], cmap='coolwarm', alpha=0.5, label='Synthetic', marker='x')
        ax2.set_title(f"Augmented Data (n={len(X_augmented)})")
        ax2.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})")
        ax2.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})")
        ax2.legend()
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            logger.info(f"Saved visualization to {output_path}")
        
        plt.close()
        
    except ImportError:
        logger.warning("matplotlib not available - skipping visualization")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")


def main():
    """Main augmentation function."""
    parser = argparse.ArgumentParser(description="Augment training data with SMOTE")
    parser.add_argument(
        "--target-samples",
        type=int,
        default=100,
        help="Target number of samples after augmentation (default: 100)"
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["smote", "borderline", "adasyn"],
        default="smote",
        help="SMOTE variant to use (default: smote)"
    )
    parser.add_argument(
        "--add-noise",
        action="store_true",
        help="Add Gaussian noise to synthetic samples"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate visualization of augmented data"
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        X, y, emb_cols = load_features_and_labels()
        
        # Augment
        X_aug, y_aug = augment_with_smote(
            X, y, 
            target_samples=args.target_samples,
            method=args.method
        )
        
        # Add noise if requested
        if args.add_noise:
            X_aug = add_gaussian_noise(X_aug, noise_factor=0.01)
        
        # Save
        features_path, labels_path = save_augmented_data(
            X_aug, y_aug, emb_cols, settings.data_features_path
        )
        
        # Visualize if requested
        if args.visualize:
            viz_path = settings.models_path / "augmentation_visualization.png"
            visualize_augmentation(X, X_aug, y, y_aug, viz_path)
        
        print("\n" + "=" * 60)
        print("DATA AUGMENTATION COMPLETE")
        print("=" * 60)
        print(f"Original samples: {len(X)}")
        print(f"Augmented samples: {len(X_aug)}")
        print(f"Method: {args.method.upper()}")
        print(f"Features: {features_path}")
        print(f"Labels: {labels_path}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Augmentation failed: {e}")
        raise


if __name__ == "__main__":
    main()
