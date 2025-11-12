"""
Production-Ready Advanced Feature Extractors.

Implements pragmatic, high-impact features that work with current data pipeline.
Focus on features proven to improve viral prediction models.
"""

import warnings
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from scipy import stats

# Optional: UMAP for better dimensionality reduction
try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    warnings.warn("UMAP not available - using PCA only")


class AdvancedTemporalExtractor:
    """
    Advanced temporal features for viral trend prediction.
    
    Captures time-based patterns: hour-of-day effects, weekend spikes,
    seasonality, and freshness decay.
    """
    
    def __init__(self):
        self.logger = logger.bind(extractor="advanced_temporal")
    
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract advanced temporal features.
        
        Args:
            df: DataFrame with 'timestamp' or 'collected_at' column
            
        Returns:
            DataFrame with additional temporal features
        """
        df = df.copy()
        
        # Find timestamp column
        ts_col = None
        for col in ['timestamp', 'collected_at', 'created_at', 'published_at']:
            if col in df.columns:
                ts_col = col
                break
        
        if ts_col is None:
            self.logger.warning("No timestamp column found - using current time")
            df['_temp_timestamp'] = pd.Timestamp.now()
            ts_col = '_temp_timestamp'
        
        # Convert to datetime
        df[ts_col] = pd.to_datetime(df[ts_col], errors='coerce')
        
        # Extract temporal features
        df['hour_of_day'] = df[ts_col].dt.hour
        df['day_of_week'] = df[ts_col].dt.dayofweek  # 0=Monday, 6=Sunday
        df['day_of_month'] = df[ts_col].dt.day
        df['month'] = df[ts_col].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_night'] = ((df['hour_of_day'] >= 22) | (df['hour_of_day'] <= 6)).astype(int)
        df['is_prime_time'] = ((df['hour_of_day'] >= 18) & (df['hour_of_day'] <= 22)).astype(int)
        
        # Quarter of year (seasonality)
        df['quarter'] = df[ts_col].dt.quarter
        
        # Time since collection (freshness)
        now = pd.Timestamp.now()
        df['hours_since_collection'] = (now - df[ts_col]).dt.total_seconds() / 3600
        df['days_since_collection'] = df['hours_since_collection'] / 24
        
        # Cyclical encoding (sine/cosine for periodic features)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Cleanup temp column if created
        if '_temp_timestamp' in df.columns:
            df = df.drop(columns=['_temp_timestamp'])
        
        n_features = 17  # hour, dow, dom, month, is_weekend, is_night, is_prime, quarter, hours/days_since, 6 cyclical
        self.logger.info(f"Extracted {n_features} advanced temporal features")
        
        return df


class TrendDynamicsExtractor:
    """
    Trend dynamics and velocity features.
    
    Captures rate of change, acceleration, momentum - critical for
    identifying breakout trends vs. stable/declining topics.
    """
    
    def __init__(self):
        self.logger = logger.bind(extractor="trend_dynamics")
    
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract trend dynamics features.
        
        Supports: velocity, acceleration, growth_rate (from synthetic/real data)
        
        Args:
            df: DataFrame with engagement metrics (views, likes, shares, comments, growth_rate, velocity, acceleration)
            
        Returns:
            DataFrame with dynamics features
        """
        df = df.copy()
        
        # Find engagement metric columns (NEW: include synthetic columns)
        metrics = []
        for col in ['score', 'views', 'likes', 'shares', 'comments', 'total_engagement', 'upvote_ratio', 'rank']:
            if col in df.columns:
                metrics.append(col)
        
        # If we have pre-computed velocity/acceleration (from synthetic data or real-time tracking)
        has_precomputed_dynamics = all(col in df.columns for col in ['growth_rate', 'velocity', 'acceleration'])
        
        if not metrics and not has_precomputed_dynamics:
            self.logger.warning("No engagement metrics found for dynamics")
            return df
        
        # Group by topic if available (for time series analysis)
        if 'topic' in df.columns and 'timestamp' in df.columns:
            df = df.sort_values(['topic', 'timestamp'])
            
            for metric in metrics:
                # Velocity (rate of change)
                df[f'{metric}_velocity'] = df.groupby('topic')[metric].diff()
                
                # Acceleration (change in velocity)
                df[f'{metric}_acceleration'] = df.groupby('topic')[f'{metric}_velocity'].diff()
                
                # Normalized velocity (% change)
                df[f'{metric}_pct_change'] = df.groupby('topic')[metric].pct_change()
                
                # Rolling statistics (if enough data)
                if len(df) >= 3:
                    df[f'{metric}_rolling_mean_3'] = df.groupby('topic')[metric].transform(
                        lambda x: x.rolling(window=3, min_periods=1).mean()
                    )
                    df[f'{metric}_rolling_std_3'] = df.groupby('topic')[metric].transform(
                        lambda x: x.rolling(window=3, min_periods=1).std()
                    )
        
        else:
            # Without time series, compute simple statistics
            for metric in metrics:
                if df[metric].dtype in ['int64', 'float64']:
                    # Z-score (standardized value)
                    df[f'{metric}_zscore'] = (df[metric] - df[metric].mean()) / (df[metric].std() + 1e-10)
                    
                    # Percentile rank
                    df[f'{metric}_percentile'] = df[metric].rank(pct=True)
        
        # Fill NaNs from diff/pct_change with 0
        df = df.fillna(0)
        
        self.logger.info(f"Extracted trend dynamics for {len(metrics)} metrics")
        
        return df


class EmbeddingClusteringExtractor:
    """
    Clustering-based features from embeddings.
    
    Groups similar topics into clusters, adds cluster ID and distance
    to centroid as features. Helps model learn topic categories.
    """
    
    def __init__(self, n_clusters: int = 8, random_state: int = 42):
        self.logger = logger.bind(extractor="embedding_clustering")
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.kmeans: Optional[KMeans] = None
        self.fitted = False
    
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract clustering features from embeddings.
        
        Args:
            df: DataFrame with embedding columns (emb_0, emb_1, ...)
            
        Returns:
            DataFrame with cluster_id and cluster_distance features
        """
        df = df.copy()
        
        # Find embedding columns
        emb_cols = [col for col in df.columns if col.startswith('emb_')]
        
        if not emb_cols:
            self.logger.warning("No embedding columns found")
            return df
        
        X_emb = df[emb_cols].values
        
        # Fit K-means (or use existing if fitted)
        if not self.fitted:
            self.logger.info(f"Fitting K-means with {self.n_clusters} clusters on {len(emb_cols)}-dim embeddings")
            self.kmeans = KMeans(
                n_clusters=self.n_clusters,
                random_state=self.random_state,
                n_init=10,
                max_iter=300
            )
            self.kmeans.fit(X_emb)
            self.fitted = True
        
        # Predict clusters
        cluster_ids = self.kmeans.predict(X_emb)
        df['cluster_id'] = cluster_ids
        
        # Distance to cluster centroid (confidence measure)
        distances = self.kmeans.transform(X_emb)
        df['cluster_distance'] = distances[np.arange(len(distances)), cluster_ids]
        
        # Distance to nearest cluster (alternative cluster proximity)
        sorted_distances = np.sort(distances, axis=1)
        df['cluster_distance_2nd'] = sorted_distances[:, 1] if sorted_distances.shape[1] > 1 else 0
        
        # Cluster size (popularity of category)
        cluster_counts = pd.Series(cluster_ids).value_counts()
        df['cluster_size'] = df['cluster_id'].map(cluster_counts)
        
        self.logger.info(f"Assigned {len(df)} samples to {self.n_clusters} clusters")
        
        return df


class EmbeddingReductionExtractor:
    """
    Dimensionality reduction features (PCA/UMAP).
    
    Reduces 384-dim embeddings to low-dim (2-3D) for:
    1. Visualization
    2. Additional features (variance-capturing components)
    3. Noise reduction
    """
    
    def __init__(
        self,
        n_components_pca: int = 10,
        n_components_umap: int = 3,
        use_umap: bool = True,
        random_state: int = 42
    ):
        self.logger = logger.bind(extractor="embedding_reduction")
        self.n_components_pca = n_components_pca
        self.n_components_umap = n_components_umap
        self.use_umap = use_umap and UMAP_AVAILABLE
        self.random_state = random_state
        
        self.pca: Optional[PCA] = None
        self.umap_model: Optional[umap.UMAP] = None
        self.fitted = False
    
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract dimensionality reduction features.
        
        Args:
            df: DataFrame with embedding columns
            
        Returns:
            DataFrame with PCA/UMAP components as new features
        """
        df = df.copy()
        
        # Find embedding columns
        emb_cols = [col for col in df.columns if col.startswith('emb_')]
        
        if not emb_cols:
            self.logger.warning("No embedding columns found")
            return df
        
        X_emb = df[emb_cols].values
        
        # PCA
        if not self.fitted:
            self.logger.info(f"Fitting PCA ({self.n_components_pca} components)")
            self.pca = PCA(n_components=self.n_components_pca, random_state=self.random_state)
            self.pca.fit(X_emb)
        
        pca_features = self.pca.transform(X_emb)
        for i in range(self.n_components_pca):
            df[f'pca_{i}'] = pca_features[:, i]
        
        # Log explained variance
        var_explained = self.pca.explained_variance_ratio_.sum()
        self.logger.info(f"PCA {self.n_components_pca} components explain {var_explained:.2%} variance")
        
        # UMAP (if available)
        if self.use_umap:
            if not self.fitted:
                self.logger.info(f"Fitting UMAP ({self.n_components_umap} components)")
                self.umap_model = umap.UMAP(
                    n_components=self.n_components_umap,
                    random_state=self.random_state,
                    n_neighbors=15,
                    min_dist=0.1,
                    metric='cosine'
                )
                umap_features = self.umap_model.fit_transform(X_emb)
            else:
                umap_features = self.umap_model.transform(X_emb)
            
            for i in range(self.n_components_umap):
                df[f'umap_{i}'] = umap_features[:, i]
        
        self.fitted = True
        
        total_features = self.n_components_pca + (self.n_components_umap if self.use_umap else 0)
        self.logger.info(f"Extracted {total_features} dimensionality reduction features")
        
        return df


class StatisticalFeaturesExtractor:
    """
    Statistical features from embeddings.
    
    Compute distributional properties (std, skewness, kurtosis) of
    embedding vectors - captures embedding "shape" characteristics.
    """
    
    def __init__(self):
        self.logger = logger.bind(extractor="statistical")
    
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract statistical features from embeddings.
        
        Args:
            df: DataFrame with embedding columns
            
        Returns:
            DataFrame with statistical features
        """
        df = df.copy()
        
        # Find embedding columns
        emb_cols = [col for col in df.columns if col.startswith('emb_')]
        
        if not emb_cols:
            self.logger.warning("No embedding columns found")
            return df
        
        X_emb = df[emb_cols].values
        
        # Compute statistics across embedding dimensions (per sample)
        df['emb_mean'] = np.mean(X_emb, axis=1)
        df['emb_std'] = np.std(X_emb, axis=1)
        df['emb_min'] = np.min(X_emb, axis=1)
        df['emb_max'] = np.max(X_emb, axis=1)
        df['emb_median'] = np.median(X_emb, axis=1)
        
        # Range and IQR
        df['emb_range'] = df['emb_max'] - df['emb_min']
        df['emb_q25'] = np.percentile(X_emb, 25, axis=1)
        df['emb_q75'] = np.percentile(X_emb, 75, axis=1)
        df['emb_iqr'] = df['emb_q75'] - df['emb_q25']
        
        # Higher moments
        df['emb_skewness'] = stats.skew(X_emb, axis=1)
        df['emb_kurtosis'] = stats.kurtosis(X_emb, axis=1)
        
        # L2 norm (embedding magnitude)
        df['emb_l2_norm'] = np.linalg.norm(X_emb, axis=1)
        
        # Number of near-zero components (sparsity)
        df['emb_sparsity'] = np.sum(np.abs(X_emb) < 0.01, axis=1) / len(emb_cols)
        
        n_features = 13
        self.logger.info(f"Extracted {n_features} statistical features")
        
        return df
