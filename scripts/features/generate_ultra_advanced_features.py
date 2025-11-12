"""
End-to-End Feature Generation Pipeline - 1000+ samples avec features ultra-avancées.

Pipeline:
1. Load synthetic viral trends (1000 samples)
2. Generate embeddings (384 dims)
3. Extract advanced temporal features
4. Extract trend dynamics (velocity, acceleration)
5. Extract clustering features (K-means)
6. Extract UMAP dimensionality reduction
7. Extract statistical features
8. Save to parquet with 500+ features

Target: AUC > 0.90
"""

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger
from sentence_transformers import SentenceTransformer

from src.core.config import settings
from src.services.features.production_extractors import (
    AdvancedTemporalExtractor,
    EmbeddingClusteringExtractor,
    EmbeddingReductionExtractor,
    StatisticalFeaturesExtractor,
    TrendDynamicsExtractor,
)


def load_raw_data(filepath: str | None = None) -> pd.DataFrame:
    """Load raw synthetic viral trends."""
    if filepath is None:
        # Find latest synthetic file
        raw_files = sorted(settings.data_raw_path.glob("synthetic_viral_trends_*.parquet"))
        if not raw_files:
            raise ValueError("No synthetic data files found. Run: python scripts/data/generate_synthetic_viral_trends.py")
        filepath = str(raw_files[-1])
    
    df = pd.read_parquet(filepath)
    logger.info(f"📂 Loaded {len(df)} samples from {Path(filepath).name}")
    logger.info(f"   Columns: {len(df.columns)}")
    logger.info(f"   Viral samples: {df['is_breakout'].sum()} ({df['is_breakout'].mean():.1%})")
    
    return df


def generate_embeddings(df: pd.DataFrame, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> pd.DataFrame:
    """Generate text embeddings from topic."""
    logger.info(f"🧠 Generating embeddings with {model_name}...")
    
    model = SentenceTransformer(model_name)
    
    # Generate embeddings from topic
    topics = df["topic"].tolist()
    embeddings = model.encode(topics, show_progress_bar=True, batch_size=32)
    
    # Add embeddings to dataframe
    for i in range(embeddings.shape[1]):
        df[f"emb_{i}"] = embeddings[:, i]
    
    logger.info(f"✅ Generated {embeddings.shape[1]} embedding features")
    
    return df


def extract_advanced_features(df: pd.DataFrame, use_umap: bool = True) -> pd.DataFrame:
    """Extract all advanced features."""
    
    logger.info("=" * 70)
    logger.info("🚀 EXTRACTING ADVANCED FEATURES")
    logger.info("=" * 70)
    
    initial_cols = len(df.columns)
    
    # 1. Advanced Temporal Features
    logger.info("\n📅 Extracting Advanced Temporal Features...")
    temporal_extractor = AdvancedTemporalExtractor()
    df = temporal_extractor.extract(df)
    logger.info(f"   Columns: {initial_cols} → {len(df.columns)} (+{len(df.columns) - initial_cols})")
    
    # 2. Trend Dynamics (velocity, acceleration)
    logger.info("\n⚡ Extracting Trend Dynamics Features...")
    dynamics_cols_before = len(df.columns)
    dynamics_extractor = TrendDynamicsExtractor()
    df = dynamics_extractor.extract(df)
    logger.info(f"   Columns: {dynamics_cols_before} → {len(df.columns)} (+{len(df.columns) - dynamics_cols_before})")
    
    # 3. Embedding Clustering
    logger.info("\n🎯 Extracting Clustering Features...")
    clustering_cols_before = len(df.columns)
    clustering_extractor = EmbeddingClusteringExtractor(n_clusters=10)
    df = clustering_extractor.extract(df)
    logger.info(f"   Columns: {clustering_cols_before} → {len(df.columns)} (+{len(df.columns) - clustering_cols_before})")
    
    # 4. Dimensionality Reduction (PCA + UMAP)
    logger.info("\n🔬 Extracting Dimensionality Reduction Features...")
    reduction_cols_before = len(df.columns)
    reduction_extractor = EmbeddingReductionExtractor(
        n_components_pca=15,
        n_components_umap=5,
        use_umap=use_umap
    )
    df = reduction_extractor.extract(df)
    logger.info(f"   Columns: {reduction_cols_before} → {len(df.columns)} (+{len(df.columns) - reduction_cols_before})")
    
    # 5. Statistical Features
    logger.info("\n📊 Extracting Statistical Features...")
    stats_cols_before = len(df.columns)
    stats_extractor = StatisticalFeaturesExtractor()
    df = stats_extractor.extract(df)
    logger.info(f"   Columns: {stats_cols_before} → {len(df.columns)} (+{len(df.columns) - stats_cols_before})")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"✅ FEATURE EXTRACTION COMPLETE")
    logger.info(f"   Initial columns: {initial_cols}")
    logger.info(f"   Final columns: {len(df.columns)}")
    logger.info(f"   New features: {len(df.columns) - initial_cols}")
    logger.info("=" * 70)
    
    return df


def save_features(df: pd.DataFrame, output_dir: Path | None = None) -> Path:
    """Save features to parquet."""
    output_dir = output_dir or settings.data_features_path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"features_ultra_advanced_{timestamp}.parquet"
    filepath = output_dir / filename
    
    df.to_parquet(filepath, engine="pyarrow", compression="snappy", index=False)
    
    logger.info(f"\n💾 Features saved: {filepath}")
    logger.info(f"   Size: {filepath.stat().st_size / 1024:.1f} KB")
    
    return filepath


def main():
    """Main pipeline."""
    parser = argparse.ArgumentParser(description="Generate ultra-advanced features")
    parser.add_argument("--input", type=str, help="Input parquet file (default: latest synthetic)")
    parser.add_argument("--use-umap", action="store_true", default=True, help="Use UMAP (slower)")
    parser.add_argument("--no-umap", action="store_false", dest="use_umap", help="Skip UMAP")
    
    args = parser.parse_args()
    
    try:
        # 1. Load raw data
        df = load_raw_data(args.input)
        
        # 2. Generate embeddings
        df = generate_embeddings(df)
        
        # 3. Extract advanced features
        df = extract_advanced_features(df, use_umap=args.use_umap)
        
        # 4. Save
        filepath = save_features(df)
        
        # Summary
        print("\n" + "=" * 70)
        print("🎉 PIPELINE COMPLETE")
        print("=" * 70)
        print(f"✅ Samples: {len(df)}")
        print(f"✅ Features: {len(df.columns)}")
        print(f"✅ Viral samples: {df['is_breakout'].sum()} ({df['is_breakout'].mean():.1%})")
        print(f"✅ Output: {filepath}")
        print("\n📊 Feature breakdown:")
        print(f"   • Embeddings: {len([c for c in df.columns if c.startswith('emb_')])}")
        print(f"   • Temporal: {len([c for c in df.columns if any(x in c for x in ['hour', 'day', 'month', 'weekend', 'night', 'prime', 'quarter', 'since', 'sin', 'cos'])])}")
        print(f"   • Dynamics: {len([c for c in df.columns if any(x in c for x in ['velocity', 'acceleration', 'pct_change', 'rolling', 'zscore', 'percentile'])])}")
        print(f"   • Clustering: {len([c for c in df.columns if 'cluster' in c])}")
        print(f"   • Reduction: {len([c for c in df.columns if c.startswith('pca_') or c.startswith('umap_')])}")
        print(f"   • Statistical: {len([c for c in df.columns if any(x in c for x in ['emb_mean', 'emb_std', 'emb_min', 'emb_max', 'emb_median', 'emb_range', 'emb_iqr', 'emb_skewness', 'emb_kurtosis', 'emb_l2_norm', 'emb_sparsity'])])}")
        print("\n✅ Ready to train model!")
        print(f"   Run: python scripts/training/train_baseline.py --force")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
