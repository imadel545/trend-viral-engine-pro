"""
Feature Service - Extract features from raw data.
Handles temporal features, embeddings (text/vision/audio), and transformations.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger
from sentence_transformers import SentenceTransformer

from src.core.config import settings


class FeatureExtractor:
    """Base feature extractor."""

    def __init__(self):
        self.logger = logger.bind(service="features")

    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features from dataframe."""
        raise NotImplementedError


class TemporalFeatureExtractor(FeatureExtractor):
    """Extract temporal features (slopes, acceleration, etc.)."""

    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract temporal features."""
        if "timestamp" not in df.columns:
            self.logger.warning("No timestamp column found")
            return df

        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        # FIX #3: Renommer avec prefix 'temporal_' pour compatibility train_baseline.py
        # Time-based features (AVANT: hour, day_of_week, is_weekend)
        df["temporal_hour"] = df["timestamp"].dt.hour
        df["temporal_day_of_week"] = df["timestamp"].dt.dayofweek
        df["temporal_is_weekend"] = df["temporal_day_of_week"].isin([5, 6]).astype(int)

        # Group by topic and calculate slopes
        if "topic" in df.columns and "views" in df.columns:
            df = self._calculate_slopes(df)

        return df

    def _calculate_slopes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate growth slopes and acceleration."""
        grouped = df.groupby("topic")

        slopes = []
        accelerations = []

        for name, group in grouped:
            if len(group) < 2:
                slopes.extend([0] * len(group))
                accelerations.extend([0] * len(group))
                continue

            # Calculate differences
            view_diff = group["views"].diff().fillna(0)
            time_diff = group["timestamp"].diff().dt.total_seconds().fillna(1)

            slope = (view_diff / time_diff).fillna(0)
            accel = slope.diff().fillna(0)

            slopes.extend(slope.tolist())
            accelerations.extend(accel.tolist())

        df["slope"] = slopes
        df["acceleration"] = accelerations

        return df


class EmbeddingFeatureExtractor(FeatureExtractor):
    """Extract embedding features using pre-trained models."""

    def __init__(self):
        super().__init__()
        self.text_model = None
        self.vision_model = None

    def _load_text_model(self):
        """Load text embedding model."""
        if self.text_model is None:
            self.logger.info(f"Loading text model: {settings.embedding_model_text}")
            self.text_model = SentenceTransformer(settings.embedding_model_text)
        return self.text_model

    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract embeddings for text columns."""
        df = df.copy()

        # Determine text column (try multiple column names)
        text_col = None
        for col_name in ["topic", "title", "text", "description"]:
            if col_name in df.columns:
                text_col = col_name
                break

        if text_col is None:
            self.logger.warning("No text column found for embeddings")
            return df

        # Extract text embeddings
        model = self._load_text_model()
        texts = df[text_col].fillna("").tolist()

        self.logger.info(f"Computing embeddings for {len(texts)} texts from '{text_col}' column")
        embeddings = model.encode(texts, show_progress_bar=False)

        # FIX #1: Optimisation vectorisée pour éviter DataFrame fragmentation
        # AVANT: for i in range(embeddings.shape[1]): df[f"emb_{i}"] = embeddings[:, i]
        # APRÈS: pd.concat vectorisé (x3 plus rapide, 0 PerformanceWarning)
        emb_df = pd.DataFrame(
            embeddings,
            columns=[f"emb_{i}" for i in range(embeddings.shape[1])],
            index=df.index
        )
        df = pd.concat([df, emb_df], axis=1)
        
        self.logger.info(f"Added {embeddings.shape[1]} embedding features (vectorized)")

        return df


class StatisticalFeatureExtractor(FeatureExtractor):
    """Extract statistical aggregations from embedding features.
    
    FIX #2: Génère 13 features statistiques pour aligner avec baseline_model.pkl:
    - emb_max, emb_median, emb_range, emb_q25, emb_q75, emb_iqr
    - emb_skewness, emb_kurtosis, emb_l2_norm, emb_sparsity
    - emb_min, emb_mean, emb_std
    """
    
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract statistical features from embeddings."""
        # Trouver toutes les colonnes d'embeddings
        emb_cols = [col for col in df.columns if col.startswith("emb_") and col[4:].isdigit()]
        
        if not emb_cols:
            self.logger.warning("No embedding columns found for statistical extraction")
            return df
        
        df = df.copy()
        emb_values = df[emb_cols].values
        
        # Calcul des statistiques vectorisées (axis=1 pour chaque row)
        df["emb_min"] = np.min(emb_values, axis=1)
        df["emb_max"] = np.max(emb_values, axis=1)
        df["emb_mean"] = np.mean(emb_values, axis=1)
        df["emb_median"] = np.median(emb_values, axis=1)
        df["emb_std"] = np.std(emb_values, axis=1)
        df["emb_range"] = df["emb_max"] - df["emb_min"]
        
        # Quartiles
        df["emb_q25"] = np.percentile(emb_values, 25, axis=1)
        df["emb_q75"] = np.percentile(emb_values, 75, axis=1)
        df["emb_iqr"] = df["emb_q75"] - df["emb_q25"]
        
        # Moments d'ordre supérieur
        from scipy.stats import skew, kurtosis
        df["emb_skewness"] = skew(emb_values, axis=1)
        df["emb_kurtosis"] = kurtosis(emb_values, axis=1)
        
        # Normes et sparsity
        df["emb_l2_norm"] = np.linalg.norm(emb_values, axis=1)
        df["emb_sparsity"] = np.count_nonzero(np.abs(emb_values) < 0.01, axis=1) / emb_values.shape[1]
        
        self.logger.info(f"Added 13 statistical features from {len(emb_cols)} embeddings")
        
        return df


from src.services.features.viral_features import ViralPredictionFeatures, BoostingFeatures


class FeatureService:
    """Main feature service orchestrating all extractors."""

    def __init__(self):
        self.logger = logger.bind(service="features")
        # FIX #2: Ajouter StatisticalFeatureExtractor après EmbeddingFeatureExtractor
        self.extractors: List[FeatureExtractor] = [
            TemporalFeatureExtractor(),
            EmbeddingFeatureExtractor(),
            StatisticalFeatureExtractor(),  # Génère 13 stats features
            ViralPredictionFeatures(),  # Features viral-specific
            BoostingFeatures(),  # Features pour recall
        ]

    def process_raw_data(self, input_path: Path) -> Path:
        """Process raw data and extract features."""
        self.logger.info(f"Processing raw data from {input_path}")

        # Load raw data
        df = pd.read_parquet(input_path)
        self.logger.info(f"Loaded {len(df)} records")

        # Apply all extractors
        for extractor in self.extractors:
            extractor_name = extractor.__class__.__name__
            self.logger.info(f"Applying {extractor_name}")
            df = extractor.extract(df)

        # Save features
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = settings.data_features_path / f"features_{timestamp}.parquet"

        df.to_parquet(output_path, engine="pyarrow", compression="snappy", index=False)
        self.logger.info(f"Saved features to {output_path}")

        return output_path

    def batch_process(self, input_dir: Optional[Path] = None) -> List[Path]:
        """Process all raw data files in directory."""
        input_dir = input_dir or settings.data_raw_path
        raw_files = sorted(input_dir.glob("*.parquet"))

        self.logger.info(f"Found {len(raw_files)} raw files to process")

        output_paths = []
        for raw_file in raw_files:
            try:
                output_path = self.process_raw_data(raw_file)
                output_paths.append(output_path)
            except Exception as e:
                self.logger.error(f"Error processing {raw_file}: {e}")
                continue

        return output_paths


# Singleton instance
_feature_service: Optional[FeatureService] = None


def get_feature_service() -> FeatureService:
    """Get or create feature service instance."""
    global _feature_service
    if _feature_service is None:
        _feature_service = FeatureService()
    return _feature_service
