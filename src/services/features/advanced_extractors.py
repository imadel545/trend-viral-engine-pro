"""
Advanced Feature Extractors - State-of-the-Art Feature Engineering
Implémente les meilleures techniques de feature engineering au monde.
"""

import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from scipy import signal, stats
from scipy.fft import fft, fftfreq
from sklearn.preprocessing import StandardScaler

# Conditional imports
try:
    import pywt
    PYWT_AVAILABLE = True
except ImportError:
    PYWT_AVAILABLE = False
    warnings.warn("PyWavelets not available - wavelet features disabled")

try:
    from tsfresh import extract_features
    from tsfresh.feature_extraction import ComprehensiveFCParameters
    TSFRESH_AVAILABLE = True
except ImportError:
    TSFRESH_AVAILABLE = False
    warnings.warn("tsfresh not available - comprehensive temporal features disabled")

try:
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import CLIPProcessor, CLIPModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    warnings.warn("Transformers not available - advanced embeddings disabled")

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    warnings.warn("NetworkX not available - graph features disabled")


class WaveletFeatureExtractor:
    """Extract wavelet transform features (time-frequency analysis)."""
    
    def __init__(self, wavelet: str = 'db4', levels: int = 3):
        self.logger = logger.bind(extractor="wavelet")
        self.wavelet = wavelet
        self.levels = levels
        
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract wavelet coefficients and statistics."""
        if not PYWT_AVAILABLE:
            self.logger.warning("PyWavelets not available, skipping")
            return df
            
        df = df.copy()
        
        # Group by topic for temporal analysis
        if "topic" not in df.columns or "views" not in df.columns:
            return df
            
        wavelet_features = []
        
        for topic, group in df.groupby("topic"):
            if len(group) < 2**self.levels:
                # Pad with zeros if insufficient data
                values = np.pad(group["views"].values, 
                               (0, 2**self.levels - len(group)),
                               mode='edge')
            else:
                values = group["views"].values[:2**self.levels]
            
            # Discrete Wavelet Transform
            coeffs = pywt.wavedec(values, self.wavelet, level=self.levels)
            
            # Extract statistics from each level
            features = {}
            for i, c in enumerate(coeffs):
                features[f'wavelet_mean_L{i}'] = np.mean(c)
                features[f'wavelet_std_L{i}'] = np.std(c)
                features[f'wavelet_energy_L{i}'] = np.sum(c**2)
                features[f'wavelet_entropy_L{i}'] = stats.entropy(np.abs(c) + 1e-10)
            
            wavelet_features.extend([features] * len(group))
        
        # Add features to dataframe
        wavelet_df = pd.DataFrame(wavelet_features, index=df.index)
        df = pd.concat([df, wavelet_df], axis=1)
        
        self.logger.info(f"Extracted {len(wavelet_df.columns)} wavelet features")
        return df


class FourierFeatureExtractor:
    """Extract Fourier transform features (frequency domain)."""
    
    def __init__(self, n_components: int = 10):
        self.logger = logger.bind(extractor="fourier")
        self.n_components = n_components
        
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract FFT features."""
        df = df.copy()
        
        if "topic" not in df.columns or "views" not in df.columns:
            return df
        
        fft_features = []
        
        for topic, group in df.groupby("topic"):
            if len(group) < 4:
                features = {f'fft_mag_{i}': 0.0 for i in range(self.n_components)}
                features.update({f'fft_phase_{i}': 0.0 for i in range(self.n_components)})
                fft_features.extend([features] * len(group))
                continue
            
            # Compute FFT
            values = group["views"].values
            fft_vals = fft(values)
            freqs = fftfreq(len(values))
            
            # Get top N frequency components
            magnitudes = np.abs(fft_vals)
            phases = np.angle(fft_vals)
            
            # Take only positive frequencies
            pos_mask = freqs > 0
            pos_freqs = freqs[pos_mask]
            pos_mags = magnitudes[pos_mask]
            pos_phases = phases[pos_mask]
            
            # Sort by magnitude and take top N
            if len(pos_mags) > 0:
                top_indices = np.argsort(pos_mags)[::-1][:self.n_components]
                
                features = {}
                for i, idx in enumerate(top_indices):
                    features[f'fft_mag_{i}'] = pos_mags[idx]
                    features[f'fft_phase_{i}'] = pos_phases[idx]
                
                # Pad if less than n_components
                for i in range(len(top_indices), self.n_components):
                    features[f'fft_mag_{i}'] = 0.0
                    features[f'fft_phase_{i}'] = 0.0
            else:
                features = {f'fft_mag_{i}': 0.0 for i in range(self.n_components)}
                features.update({f'fft_phase_{i}': 0.0 for i in range(self.n_components)})
            
            fft_features.extend([features] * len(group))
        
        fft_df = pd.DataFrame(fft_features, index=df.index)
        df = pd.concat([df, fft_df], axis=1)
        
        self.logger.info(f"Extracted {len(fft_df.columns)} FFT features")
        return df


class TSFreshFeatureExtractor:
    """Extract comprehensive time series features using tsfresh."""
    
    def __init__(self, minimal: bool = True):
        self.logger = logger.bind(extractor="tsfresh")
        self.minimal = minimal
        
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract tsfresh features."""
        if not TSFRESH_AVAILABLE:
            self.logger.warning("tsfresh not available, skipping")
            return df
            
        df = df.copy()
        
        if "topic" not in df.columns or "views" not in df.columns or "timestamp" not in df.columns:
            return df
        
        # Prepare data for tsfresh
        ts_df = df[["topic", "timestamp", "views"]].copy()
        ts_df["id"] = ts_df.groupby("topic").ngroup()
        ts_df = ts_df.rename(columns={"timestamp": "time", "views": "value"})
        
        try:
            # Extract features
            if self.minimal:
                # Use minimal feature set for speed
                extracted = extract_features(
                    ts_df,
                    column_id="id",
                    column_sort="time",
                    column_value="value",
                    default_fc_parameters={
                        "mean": None,
                        "variance": None,
                        "skewness": None,
                        "kurtosis": None,
                        "absolute_sum_of_changes": None,
                        "longest_strike_above_mean": None,
                    }
                )
            else:
                # Comprehensive feature set
                extracted = extract_features(
                    ts_df,
                    column_id="id",
                    column_sort="time",
                    column_value="value",
                    default_fc_parameters=ComprehensiveFCParameters()
                )
            
            # Map back to original dataframe
            id_map = ts_df.groupby("id")["topic"].first()
            extracted["topic"] = extracted.index.map(id_map)
            
            # Merge with original
            df = df.merge(extracted, on="topic", how="left")
            
            self.logger.info(f"Extracted {len(extracted.columns)-1} tsfresh features")
            
        except Exception as e:
            self.logger.error(f"tsfresh extraction failed: {e}")
        
        return df


class MultimodalEmbeddingExtractor:
    """Extract state-of-the-art multimodal embeddings (Text + Vision)."""
    
    def __init__(
        self,
        text_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        clip_model: str = "openai/clip-vit-base-patch32",
    ):
        self.logger = logger.bind(extractor="multimodal")
        self.text_model_name = text_model
        self.clip_model_name = clip_model
        
        self.text_model = None
        self.clip_model = None
        self.clip_processor = None
        
    def _load_text_model(self):
        """Lazy load text embedding model."""
        if self.text_model is None and TRANSFORMERS_AVAILABLE:
            self.logger.info(f"Loading text model: {self.text_model_name}")
            self.text_model = SentenceTransformer(self.text_model_name)
        return self.text_model
    
    def _load_clip_model(self):
        """Lazy load CLIP model."""
        if self.clip_model is None and TRANSFORMERS_AVAILABLE:
            self.logger.info(f"Loading CLIP model: {self.clip_model_name}")
            self.clip_model = CLIPModel.from_pretrained(self.clip_model_name)
            self.clip_processor = CLIPProcessor.from_pretrained(self.clip_model_name)
        return self.clip_model, self.clip_processor
    
    def extract_text_embeddings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract advanced text embeddings."""
        if not TRANSFORMERS_AVAILABLE:
            self.logger.warning("Transformers not available, skipping text embeddings")
            return df
            
        df = df.copy()
        
        if "topic" not in df.columns:
            return df
        
        model = self._load_text_model()
        if model is None:
            return df
        
        # Encode topics
        texts = df["topic"].fillna("").tolist()
        self.logger.info(f"Encoding {len(texts)} texts with {self.text_model_name}")
        
        embeddings = model.encode(
            texts,
            show_progress_bar=False,
            batch_size=32,
            convert_to_numpy=True
        )
        
        # Add embeddings as features (optimized with concat to avoid fragmentation)
        emb_df = pd.DataFrame(
            embeddings,
            columns=[f'text_emb_{i}' for i in range(embeddings.shape[1])],
            index=df.index
        )
        df = pd.concat([df, emb_df], axis=1)
        
        self.logger.info(f"Extracted {embeddings.shape[1]} text embedding dimensions")
        return df
    
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract all multimodal embeddings."""
        df = self.extract_text_embeddings(df)
        # Could add CLIP image embeddings here if image URLs available
        return df


class GraphFeatureExtractor:
    """Extract graph-based features (topic relationships)."""
    
    def __init__(self, window_size: int = 24):
        self.logger = logger.bind(extractor="graph")
        self.window_size = window_size
        
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract graph features from topic co-occurrence."""
        if not NETWORKX_AVAILABLE:
            self.logger.warning("NetworkX not available, skipping graph features")
            return df
            
        df = df.copy()
        
        if "topic" not in df.columns or "timestamp" not in df.columns:
            return df
        
        # Build co-occurrence graph
        G = nx.Graph()
        
        # Add nodes
        topics = df["topic"].unique()
        G.add_nodes_from(topics)
        
        # Add edges based on temporal co-occurrence
        df_sorted = df.sort_values("timestamp")
        for i in range(len(df_sorted) - 1):
            t1 = df_sorted.iloc[i]["topic"]
            t2 = df_sorted.iloc[i+1]["topic"]
            if t1 != t2:
                if G.has_edge(t1, t2):
                    G[t1][t2]['weight'] += 1
                else:
                    G.add_edge(t1, t2, weight=1)
        
        # Extract graph metrics
        try:
            pagerank = nx.pagerank(G, weight='weight')
            betweenness = nx.betweenness_centrality(G, weight='weight')
            closeness = nx.closeness_centrality(G)
            degree_centrality = nx.degree_centrality(G)
            
            # Map to dataframe
            df['graph_pagerank'] = df['topic'].map(pagerank).fillna(0)
            df['graph_betweenness'] = df['topic'].map(betweenness).fillna(0)
            df['graph_closeness'] = df['topic'].map(closeness).fillna(0)
            df['graph_degree'] = df['topic'].map(degree_centrality).fillna(0)
            
            self.logger.info("Extracted 4 graph features")
            
        except Exception as e:
            self.logger.error(f"Graph feature extraction failed: {e}")
        
        return df


class MetaFeatureExtractor:
    """Extract meta-features (features on features)."""
    
    def __init__(self):
        self.logger = logger.bind(extractor="meta")
        
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract statistical meta-features."""
        df = df.copy()
        
        # Identify numeric feature columns (exclude identifiers and targets)
        exclude_cols = {'topic', 'timestamp', 'collected_at', 'source', 'country', 
                       'is_breakout', 'p_breakout_24h', 'predicted_views_24h'}
        
        numeric_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                       if col not in exclude_cols]
        
        if len(numeric_cols) < 2:
            return df
        
        # Extract meta-features on numeric columns
        numeric_data = df[numeric_cols].values
        
        # Row-wise statistics (across features)
        df['meta_mean'] = np.mean(numeric_data, axis=1)
        df['meta_std'] = np.std(numeric_data, axis=1)
        df['meta_min'] = np.min(numeric_data, axis=1)
        df['meta_max'] = np.max(numeric_data, axis=1)
        df['meta_median'] = np.median(numeric_data, axis=1)
        df['meta_iqr'] = np.percentile(numeric_data, 75, axis=1) - np.percentile(numeric_data, 25, axis=1)
        
        # Sparsity
        df['meta_sparsity'] = (numeric_data == 0).sum(axis=1) / numeric_data.shape[1]
        
        self.logger.info("Extracted 7 meta-features")
        return df


class CrossFeatureExtractor:
    """Extract interaction features between columns."""
    
    def __init__(self, max_interactions: int = 50):
        self.logger = logger.bind(extractor="cross")
        self.max_interactions = max_interactions
        
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract polynomial and interaction features."""
        df = df.copy()
        
        # Select key numeric features for interactions
        interaction_cols = []
        
        # Prioritize these if they exist
        priority_cols = ['slope', 'acceleration', 'views', 'hour', 'day_of_week']
        for col in priority_cols:
            if col in df.columns:
                interaction_cols.append(col)
        
        if len(interaction_cols) < 2:
            return df
        
        # Limit to top features to avoid explosion
        interaction_cols = interaction_cols[:min(7, len(interaction_cols))]
        
        interaction_count = 0
        
        # Generate pairwise interactions
        for i, col1 in enumerate(interaction_cols):
            for col2 in interaction_cols[i+1:]:
                if interaction_count >= self.max_interactions:
                    break
                    
                # Multiplicative interaction
                df[f'cross_{col1}_x_{col2}'] = df[col1] * df[col2]
                
                # Ratio (with safety)
                df[f'cross_{col1}_div_{col2}'] = df[col1] / (df[col2] + 1e-6)
                
                interaction_count += 2
        
        # Squared features
        for col in interaction_cols[:5]:
            if interaction_count >= self.max_interactions:
                break
            df[f'cross_{col}_squared'] = df[col] ** 2
            interaction_count += 1
        
        self.logger.info(f"Extracted {interaction_count} cross-features")
        return df
