"""
Advanced Viral Prediction Features
Features ULTRA-AVANCÉES pour prédire contenus à millions de vues.
"""

import numpy as np
import pandas as pd
from loguru import logger
from scipy import stats
from sklearn.preprocessing import RobustScaler


class ViralPredictionFeatures:
    """Features spécialisées pour prédiction virale."""
    
    def __init__(self):
        self.logger = logger.bind(extractor="viral")
        
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extrait features viral-specific."""
        df = df.copy()
        
        # 1. ENGAGEMENT METRICS AVANCÉS
        if 'score' in df.columns and 'num_comments' in df.columns:
            # Viral velocity (score/heure)
            if 'hours_since_posted' in df.columns:
                df['viral_velocity'] = df['score'] / (df['hours_since_posted'] + 1)
                df['comment_velocity'] = df['num_comments'] / (df['hours_since_posted'] + 1)
            
            # Engagement intensity (ratio comments/score élevé = discussions virales)
            df['engagement_intensity'] = df['num_comments'] / (df['score'] + 1)
            
            # Logarithmic features (viral content suit loi puissance)
            df['log_score'] = np.log1p(df['score'])
            df['log_comments'] = np.log1p(df['num_comments'])
        
        # 2. RATIO VIRALITÉ
        if 'upvote_ratio' in df.columns:
            # Controversé = plus viral (Reddit algorithm boost)
            df['controversy_score'] = 1 - abs(df['upvote_ratio'] - 0.5) * 2
            
            # Consensus vs polarization
            df['consensus_factor'] = df['upvote_ratio'] ** 2
        
        # 3. TIMING FEATURES
        if 'temporal_hour' in df.columns:
            # Prime time (18h-23h = peak viral)
            df['is_prime_time'] = ((df['temporal_hour'] >= 18) & (df['temporal_hour'] <= 23)).astype(int)
            
            # Weekend boost
            if 'temporal_is_weekend' in df.columns:
                df['weekend_prime'] = (df['is_prime_time'] * df['temporal_is_weekend']).astype(int)
        
        # 4. CONTENT TYPE SIGNALS
        if 'is_video' in df.columns:
            df['video_boost'] = df['is_video'].astype(int) * 2  # Vidéos = 2x plus virales
        
        if 'is_self' in df.columns:
            # Text posts moins viraux
            df['media_penalty'] = df['is_self'].astype(int) * -1
        
        # 5. EMBEDDINGS STATISTICS (si disponibles)
        emb_cols = [c for c in df.columns if c.startswith('emb_')]
        if len(emb_cols) > 0:
            emb_matrix = df[emb_cols].values
            
            # Norme L2 (magnitude sémantique)
            df['emb_magnitude'] = np.linalg.norm(emb_matrix, axis=1)
            
            # Variance (diversité sémantique)
            df['emb_variance'] = np.var(emb_matrix, axis=1)
            
            # Sparsité (spécificité du sujet)
            df['emb_sparsity'] = np.count_nonzero(emb_matrix < 0.1, axis=1) / len(emb_cols)
        
        # 6. POLYNOMIAL FEATURES (interactions)
        if 'log_score' in df.columns and 'engagement_intensity' in df.columns:
            df['score_engagement_interaction'] = df['log_score'] * df['engagement_intensity']
        
        if 'viral_velocity' in df.columns and 'controversy_score' in df.columns:
            df['velocity_controversy_interaction'] = df['viral_velocity'] * df['controversy_score']
        
        # 7. NORMALIZATION (robuste aux outliers)
        numeric_features = [
            'viral_velocity', 'comment_velocity', 'engagement_intensity',
            'controversy_score', 'emb_magnitude', 'emb_variance'
        ]
        
        for feat in numeric_features:
            if feat in df.columns:
                # Z-score clipped (remove extreme outliers)
                z_scores = stats.zscore(df[feat].fillna(0), nan_policy='omit')
                df[f'{feat}_normalized'] = np.clip(z_scores, -3, 3)
        
        self.logger.info(f"Added {len([c for c in df.columns if c not in df.columns])} viral features")
        
        return df


class BoostingFeatures:
    """Features pour améliorer recall (détecter TOUS les viraux)."""
    
    def __init__(self):
        self.logger = logger.bind(extractor="boosting")
    
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """Features pour réduire false negatives."""
        df = df.copy()
        
        # 1. PERCENTILE RANKING (position relative)
        if 'score' in df.columns:
            df['score_percentile'] = df['score'].rank(pct=True)
            df['is_top_10pct'] = (df['score_percentile'] >= 0.9).astype(int)
            df['is_top_20pct'] = (df['score_percentile'] >= 0.8).astype(int)
        
        # 2. MOMENTUM INDICATORS
        if 'score' in df.columns and 'hours_since_posted' in df.columns:
            # Early momentum (viral dans premières heures)
            df['early_momentum'] = np.where(
                df['hours_since_posted'] < 6,
                df['score'] / (df['hours_since_posted'] + 0.1),
                0
            )
        
        # 3. COMPOSITE VIRAL SCORE
        viral_signals = []
        
        if 'log_score' in df.columns:
            viral_signals.append(df['log_score'])
        if 'engagement_intensity' in df.columns:
            viral_signals.append(df['engagement_intensity'])
        if 'viral_velocity' in df.columns:
            viral_signals.append(df['viral_velocity'])
        
        if viral_signals:
            # Moyenne normalisée des signaux
            stacked = np.column_stack([stats.zscore(s.fillna(0)) for s in viral_signals])
            df['composite_viral_score'] = np.mean(stacked, axis=1)
        
        self.logger.info(f"Added {3} boosting features")
        
        return df
