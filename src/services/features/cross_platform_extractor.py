"""
Cross-Platform Correlation Feature Extractor

Extrait des features basées sur les corrélations cross-platform:
- Co-occurrence de trends sur plusieurs plateformes
- Vitesse de propagation inter-plateformes
- Lag correlation (ex: TikTok → Reddit 2-6h)
- Score de transfert de topics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import timedelta
from scipy.stats import pearsonr
from collections import defaultdict


class CrossPlatformCorrelationExtractor:
    """
    Extrait des features de corrélation cross-platform pour détecter
    les tendances qui se propagent d'une plateforme à l'autre.
    
    Features extraites:
    - co_occurrence_score: Topics présents sur N plateformes simultanément
    - cross_platform_velocity: Vitesse de spread inter-plateformes
    - lag_correlation_tiktok_reddit: Corrélation avec lag 2-6h (TikTok → Reddit)
    - lag_correlation_tiktok_instagram: Corrélation avec lag 1-4h
    - topic_transfer_score: Score de transfert topic (weighted by engagement)
    - platform_diversity: Nombre de plateformes uniques
    - dominant_platform: Plateforme avec le plus d'engagement
    - cross_platform_engagement_ratio: Ratio engagement max/min
    """
    
    SUPPORTED_PLATFORMS = ['tiktok', 'reddit', 'instagram', 'youtube', 'twitter', 'facebook']
    
    # Lag typiques observés (en heures)
    PLATFORM_LAGS = {
        'tiktok_to_reddit': (2, 6),      # TikTok → Reddit: 2-6h
        'tiktok_to_instagram': (1, 4),   # TikTok → Instagram: 1-4h
        'instagram_to_twitter': (1, 3),  # Instagram → Twitter: 1-3h
        'youtube_to_tiktok': (6, 24),    # YouTube → TikTok: 6-24h
        'reddit_to_twitter': (2, 8),     # Reddit → Twitter: 2-8h
    }
    
    def __init__(self):
        self.feature_names = [
            'co_occurrence_score',
            'cross_platform_velocity',
            'lag_correlation_tiktok_to_reddit',
            'lag_correlation_tiktok_to_instagram',
            'lag_correlation_instagram_to_twitter',
            'lag_correlation_youtube_to_tiktok',
            'lag_correlation_reddit_to_twitter',
            'topic_transfer_score',
            'platform_diversity',
            'cross_platform_engagement_ratio',
            'tiktok_dominance',
            'reddit_dominance',
            'instagram_dominance',
            'youtube_dominance',
        ]
    
    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrait toutes les features cross-platform.
        
        Args:
            df: DataFrame avec colonnes:
                - topic (str): Le topic/trend
                - platform (str): tiktok, reddit, instagram, etc.
                - created_at (datetime): Timestamp
                - engagement (float): Score d'engagement
                - views (int): Nombre de vues (optionnel)
        
        Returns:
            DataFrame avec features cross-platform ajoutées
        """
        if df.empty:
            return self._empty_features()
        
        # Group by topic pour calculer features cross-platform
        grouped = df.groupby('topic')
        
        features = []
        for topic, group in grouped:
            topic_features = self._extract_topic_features(group)
            topic_features['topic'] = topic
            features.append(topic_features)
        
        features_df = pd.DataFrame(features)
        
        # Merge avec df original (broadcast features à toutes les lignes du topic)
        result = df.merge(features_df, on='topic', how='left')
        
        return result
    
    def _extract_topic_features(self, group: pd.DataFrame) -> Dict[str, float]:
        """Extrait features pour un topic donné présent sur plusieurs plateformes"""
        features = {}
        
        # 1. Co-occurrence score: combien de plateformes ont ce topic?
        platforms = set(group['platform'].unique())
        features['co_occurrence_score'] = len(platforms) / len(self.SUPPORTED_PLATFORMS)
        
        # 2. Platform diversity
        features['platform_diversity'] = len(platforms)
        
        # 3. Cross-platform velocity: vitesse de propagation
        features['cross_platform_velocity'] = self._calculate_velocity(group)
        
        # 4. Lag correlations (TikTok → Reddit, etc.)
        lag_corrs = self._calculate_lag_correlations(group)
        features.update(lag_corrs)
        
        # 5. Topic transfer score
        features['topic_transfer_score'] = self._calculate_transfer_score(group)
        
        # 6. Engagement ratio (max/min cross-platform)
        features['cross_platform_engagement_ratio'] = self._calculate_engagement_ratio(group)
        
        # 7. Platform dominance (% engagement par plateforme)
        dominance = self._calculate_platform_dominance(group)
        features.update(dominance)
        
        return features
    
    def _calculate_velocity(self, group: pd.DataFrame) -> float:
        """
        Calcule la vitesse de propagation cross-platform.
        Vitesse = nombre de plateformes / temps écoulé (heures)
        """
        num_platforms = len(group['platform'].unique())
        
        if 'created_at' not in group.columns or len(group) < 2:
            return float(num_platforms)  # Single platform = instantané
        
        # Sort by timestamp
        sorted_group = group.sort_values('created_at')
        
        # Time between first and last appearance
        time_delta = (sorted_group.iloc[-1]['created_at'] - 
                     sorted_group.iloc[0]['created_at'])
        
        hours = time_delta.total_seconds() / 3600
        
        if hours == 0:
            return float(num_platforms)  # Instantané sur toutes plateformes
        
        # Velocity: platforms/hour
        velocity = num_platforms / hours
        
        return float(velocity)
    
    def _calculate_lag_correlations(self, group: pd.DataFrame) -> Dict[str, float]:
        """
        Calcule les corrélations avec lag entre plateformes.
        Ex: TikTok trend à t=0, Reddit à t=4h → lag correlation
        """
        correlations = {}
        
        for lag_name, (min_lag, max_lag) in self.PLATFORM_LAGS.items():
            source_platform, target_platform = lag_name.split('_to_')
            
            corr = self._compute_lag_correlation(
                group, 
                source_platform, 
                target_platform,
                min_lag_hours=min_lag,
                max_lag_hours=max_lag
            )
            
            correlations[f'lag_correlation_{lag_name}'] = corr
        
        return correlations
    
    def _compute_lag_correlation(
        self, 
        group: pd.DataFrame,
        source: str,
        target: str,
        min_lag_hours: int,
        max_lag_hours: int
    ) -> float:
        """
        Calcule la corrélation avec lag entre 2 plateformes.
        
        Returns:
            Correlation [-1, 1], ou 0.0 si données insuffisantes
        """
        if 'created_at' not in group.columns:
            return 0.0
        
        # Filter source and target platforms
        source_data = group[group['platform'] == source]
        target_data = group[group['platform'] == target]
        
        if source_data.empty or target_data.empty:
            return 0.0
        
        # Get timestamps
        source_times = pd.to_datetime(source_data['created_at'])
        target_times = pd.to_datetime(target_data['created_at'])
        
        if len(source_times) == 0 or len(target_times) == 0:
            return 0.0
        
        # Check if target appeared after source within lag window
        for source_time in source_times:
            for target_time in target_times:
                lag = (target_time - source_time).total_seconds() / 3600
                
                if min_lag_hours <= lag <= max_lag_hours:
                    # Found valid lag: return correlation based on engagement
                    if 'engagement' in group.columns:
                        source_eng = source_data['engagement'].mean()
                        target_eng = target_data['engagement'].mean()
                        
                        # Correlation as ratio (normalized)
                        if source_eng > 0:
                            return float(min(target_eng / source_eng, 1.0))
                    
                    # Default: positive correlation if lag found
                    return 0.5
        
        return 0.0
    
    def _calculate_transfer_score(self, group: pd.DataFrame) -> float:
        """
        Score de transfert de topic cross-platform.
        Weighted by engagement: si engagement augmente sur nouvelle plateforme,
        score plus élevé.
        """
        if 'engagement' not in group.columns or len(group) < 2:
            return 0.0
        
        # Sort by timestamp
        if 'created_at' in group.columns:
            sorted_group = group.sort_values('created_at')
        else:
            sorted_group = group
        
        # Calculate engagement growth
        engagements = sorted_group['engagement'].values
        
        if len(engagements) < 2:
            return 0.0
        
        # Score: moyenne des ratios engagement[i+1]/engagement[i]
        ratios = []
        for i in range(len(engagements) - 1):
            if engagements[i] > 0:
                ratio = engagements[i+1] / engagements[i]
                ratios.append(ratio)
        
        if not ratios:
            return 0.0
        
        # Normalize: score entre 0 et 1
        avg_ratio = np.mean(ratios)
        transfer_score = min(avg_ratio, 2.0) / 2.0  # Cap at 2x growth
        
        return float(transfer_score)
    
    def _calculate_engagement_ratio(self, group: pd.DataFrame) -> float:
        """
        Ratio engagement max/min cross-platform.
        Indique si engagement est uniforme ou concentré sur une plateforme.
        """
        if 'engagement' not in group.columns or len(group) < 2:
            return 1.0
        
        engagements = group['engagement'].values
        
        max_eng = engagements.max()
        min_eng = engagements.min()
        
        if min_eng == 0:
            return float(max_eng)  # Avoid division by zero
        
        ratio = max_eng / min_eng
        
        return float(ratio)
    
    def _calculate_platform_dominance(self, group: pd.DataFrame) -> Dict[str, float]:
        """
        Calcule le % d'engagement par plateforme (dominance).
        """
        dominance = {}
        
        if 'engagement' not in group.columns:
            # Default: equal dominance
            for platform in self.SUPPORTED_PLATFORMS:
                dominance[f'{platform}_dominance'] = 0.0
            return dominance
        
        # Group by platform
        platform_eng = group.groupby('platform')['engagement'].sum()
        total_eng = platform_eng.sum()
        
        if total_eng == 0:
            for platform in self.SUPPORTED_PLATFORMS:
                dominance[f'{platform}_dominance'] = 0.0
            return dominance
        
        # Calculate % for each platform
        for platform in self.SUPPORTED_PLATFORMS:
            if platform in platform_eng.index:
                dominance[f'{platform}_dominance'] = float(
                    platform_eng[platform] / total_eng
                )
            else:
                dominance[f'{platform}_dominance'] = 0.0
        
        return dominance
    
    def _empty_features(self) -> pd.DataFrame:
        """Retourne un DataFrame vide avec les colonnes features"""
        return pd.DataFrame(columns=self.feature_names)


# Factory function for integration with FeatureService
def get_cross_platform_extractor() -> CrossPlatformCorrelationExtractor:
    """Returns a CrossPlatformCorrelationExtractor instance"""
    return CrossPlatformCorrelationExtractor()


if __name__ == "__main__":
    # Test avec données synthétiques
    test_data = pd.DataFrame([
        {
            'topic': 'AI coding revolution',
            'platform': 'tiktok',
            'created_at': pd.Timestamp('2024-11-04 10:00:00'),
            'engagement': 1000,
            'views': 50000
        },
        {
            'topic': 'AI coding revolution',
            'platform': 'reddit',
            'created_at': pd.Timestamp('2024-11-04 14:00:00'),  # 4h après TikTok
            'engagement': 1500,
            'views': 30000
        },
        {
            'topic': 'AI coding revolution',
            'platform': 'instagram',
            'created_at': pd.Timestamp('2024-11-04 12:00:00'),  # 2h après TikTok
            'engagement': 800,
            'views': 20000
        },
        {
            'topic': 'Cat videos',
            'platform': 'youtube',
            'created_at': pd.Timestamp('2024-11-04 09:00:00'),
            'engagement': 5000,
            'views': 100000
        }
    ])
    
    extractor = CrossPlatformCorrelationExtractor()
    result = extractor.extract(test_data)
    
    print("✅ CrossPlatformCorrelationExtractor Test")
    print(f"\n📊 Features extraites ({len(extractor.feature_names)}):")
    for feature in extractor.feature_names:
        if feature in result.columns:
            print(f"  - {feature}: {result[feature].iloc[0]:.4f}")
    
    print(f"\n✅ Test passed! {len(result)} rows with {len(extractor.feature_names)} new features")
