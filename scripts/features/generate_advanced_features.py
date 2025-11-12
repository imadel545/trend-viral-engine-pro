"""
Test script for production-ready advanced features.

Regenerate features with advanced extractors and measure impact on model performance.
"""

import argparse
from pathlib import Path

import pandas as pd
from loguru import logger

from src.core.config import settings
from src.services.features.production_extractors import (
    AdvancedTemporalExtractor,
    TrendDynamicsExtractor,
    EmbeddingClusteringExtractor,
    EmbeddingReductionExtractor,
    StatisticalFeaturesExtractor
)


def load_raw_data() -> pd.DataFrame:
    """Load all raw data files."""
    logger.info("Loading raw data...")
    
    raw_files = sorted(settings.data_raw_path.glob("*.parquet"))
    if not raw_files:
        raise ValueError(f"No raw files found in {settings.data_raw_path}")
    
    dfs = []
    for f in raw_files:
        df = pd.read_parquet(f)
        dfs.append(df)
        logger.info(f"Loaded {len(df)} rows from {f.name}")
    
    data = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total raw data: {len(data)} rows")
    
    return data


def load_existing_features() -> pd.DataFrame:
    """Load existing feature files (with embeddings)."""
    logger.info("Loading existing features...")
    
    feature_files = sorted(settings.data_features_path.glob("features_*.parquet"))
    if not feature_files:
        raise ValueError(f"No feature files found in {settings.data_features_path}")
    
    # Prefer augmented files (more samples for clustering)
    for f in reversed(feature_files):
        if 'augmented' in f.name:
            df = pd.read_parquet(f)
            logger.info(f"Loaded {len(df)} rows from {f.name}")
            return df
    
    # Fallback to latest file
    df = pd.read_parquet(feature_files[-1])
    logger.info(f"Loaded {len(df)} rows from {feature_files[-1].name}")
    return df


def main():
    """Main feature generation function."""
    parser = argparse.ArgumentParser(description="Generate advanced features")
    parser.add_argument(
        "--use-raw",
        action="store_true",
        help="Start from raw data (slower, generates embeddings)"
    )
    parser.add_argument(
        "--skip-clustering",
        action="store_true",
        help="Skip clustering (faster)"
    )
    parser.add_argument(
        "--skip-reduction",
        action="store_true",
        help="Skip dimensionality reduction (faster)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        if args.use_raw:
            logger.info("⚠️  Starting from raw data - this will take longer")
            df = load_raw_data()
            # Would need to run embedding extraction here
            logger.error("Raw data mode requires embedding extraction - not implemented yet")
            logger.info("Use existing features instead (remove --use-raw flag)")
            return
        else:
            df = load_existing_features()
        
        initial_cols = len(df.columns)
        logger.info(f"Starting with {initial_cols} columns")
        
        # 1. Advanced Temporal Features
        logger.info("=" * 60)
        logger.info("EXTRACTING ADVANCED TEMPORAL FEATURES")
        logger.info("=" * 60)
        temporal_extractor = AdvancedTemporalExtractor()
        df = temporal_extractor.extract(df)
        logger.info(f"Columns after temporal: {len(df.columns)} (+{len(df.columns) - initial_cols})")
        
        # 2. Trend Dynamics
        logger.info("=" * 60)
        logger.info("EXTRACTING TREND DYNAMICS FEATURES")
        logger.info("=" * 60)
        dynamics_extractor = TrendDynamicsExtractor()
        df = dynamics_extractor.extract(df)
        logger.info(f"Columns after dynamics: {len(df.columns)} (+{len(df.columns) - initial_cols})")
        
        # 3. Embedding Clustering (optional)
        if not args.skip_clustering:
            logger.info("=" * 60)
            logger.info("EXTRACTING CLUSTERING FEATURES")
            logger.info("=" * 60)
            clustering_extractor = EmbeddingClusteringExtractor(n_clusters=8)
            df = clustering_extractor.extract(df)
            logger.info(f"Columns after clustering: {len(df.columns)} (+{len(df.columns) - initial_cols})")
        
        # 4. Dimensionality Reduction (optional)
        if not args.skip_reduction:
            logger.info("=" * 60)
            logger.info("EXTRACTING DIMENSIONALITY REDUCTION FEATURES")
            logger.info("=" * 60)
            reduction_extractor = EmbeddingReductionExtractor(
                n_components_pca=10,
                n_components_umap=3,
                use_umap=False  # Disable UMAP by default (not installed)
            )
            df = reduction_extractor.extract(df)
            logger.info(f"Columns after reduction: {len(df.columns)} (+{len(df.columns) - initial_cols})")
        
        # 5. Statistical Features
        logger.info("=" * 60)
        logger.info("EXTRACTING STATISTICAL FEATURES")
        logger.info("=" * 60)
        stats_extractor = StatisticalFeaturesExtractor()
        df = stats_extractor.extract(df)
        logger.info(f"Columns after statistics: {len(df.columns)} (+{len(df.columns) - initial_cols})")
        
        # Save enhanced features
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        output_path = settings.data_features_path / f"features_advanced_{timestamp}.parquet"
        df.to_parquet(output_path, index=False)
        
        logger.info("=" * 60)
        logger.info("FEATURE GENERATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Initial columns: {initial_cols}")
        logger.info(f"Final columns: {len(df.columns)}")
        logger.info(f"New features: {len(df.columns) - initial_cols}")
        logger.info(f"Samples: {len(df)}")
        logger.info(f"Output: {output_path}")
        logger.info("=" * 60)
        
        # Feature summary
        print("\n📊 FEATURE SUMMARY:")
        print(f"  • Embeddings: {len([c for c in df.columns if c.startswith('emb_')])}")
        print(f"  • Temporal: {len([c for c in df.columns if any(x in c for x in ['hour', 'day', 'month', 'weekend', 'night', 'prime', 'quarter', 'since', 'sin', 'cos'])])}")
        print(f"  • Dynamics: {len([c for c in df.columns if any(x in c for x in ['velocity', 'acceleration', 'pct_change', 'rolling', 'zscore', 'percentile'])])}")
        print(f"  • Clustering: {len([c for c in df.columns if 'cluster' in c])}")
        print(f"  • Reduction: {len([c for c in df.columns if c.startswith('pca_') or c.startswith('umap_')])}")
        print(f"  • Statistical: {len([c for c in df.columns if any(x in c for x in ['emb_mean', 'emb_std', 'emb_min', 'emb_max', 'emb_median', 'emb_range', 'emb_iqr', 'emb_skewness', 'emb_kurtosis', 'emb_l2_norm', 'emb_sparsity'])])}")
        
        print(f"\n✅ Ready to train model with {len(df.columns)} features!")
        print(f"   Run: python scripts/training/train_baseline.py --force")
        
    except Exception as e:
        logger.error(f"Feature generation failed: {e}")
        raise


if __name__ == "__main__":
    main()
