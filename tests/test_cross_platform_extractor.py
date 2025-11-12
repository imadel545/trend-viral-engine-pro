"""
Tests unitaires pour CrossPlatformCorrelationExtractor
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.services.features.cross_platform_extractor import (
    CrossPlatformCorrelationExtractor,
    get_cross_platform_extractor
)


class TestCrossPlatformCorrelationExtractor:
    """Tests pour le CrossPlatformCorrelationExtractor"""
    
    @pytest.fixture
    def extractor(self):
        """Fixture: retourne une instance de l'extracteur"""
        return CrossPlatformCorrelationExtractor()
    
    @pytest.fixture
    def sample_data(self):
        """Fixture: données synthétiques multi-plateformes"""
        base_time = datetime(2024, 11, 4, 10, 0, 0)
        
        return pd.DataFrame([
            {
                'topic': 'AI coding revolution',
                'platform': 'tiktok',
                'created_at': base_time,
                'engagement': 1000,
                'views': 50000
            },
            {
                'topic': 'AI coding revolution',
                'platform': 'reddit',
                'created_at': base_time + timedelta(hours=4),  # 4h lag
                'engagement': 1500,
                'views': 30000
            },
            {
                'topic': 'AI coding revolution',
                'platform': 'instagram',
                'created_at': base_time + timedelta(hours=2),  # 2h lag
                'engagement': 800,
                'views': 20000
            },
            {
                'topic': 'Cat videos',
                'platform': 'youtube',
                'created_at': base_time - timedelta(hours=1),
                'engagement': 5000,
                'views': 100000
            },
            {
                'topic': 'Cat videos',
                'platform': 'tiktok',
                'created_at': base_time + timedelta(hours=12),  # 12h lag
                'engagement': 3000,
                'views': 80000
            }
        ])
    
    def test_extractor_initialization(self, extractor):
        """Test: initialisation de l'extracteur"""
        assert extractor is not None
        assert len(extractor.feature_names) == 14
        assert 'co_occurrence_score' in extractor.feature_names
        assert 'cross_platform_velocity' in extractor.feature_names
        assert 'lag_correlation_tiktok_to_reddit' in extractor.feature_names
    
    def test_factory_function(self):
        """Test: fonction factory retourne une instance"""
        extractor = get_cross_platform_extractor()
        assert isinstance(extractor, CrossPlatformCorrelationExtractor)
    
    def test_extract_basic(self, extractor, sample_data):
        """Test: extraction basique avec données valides"""
        result = extractor.extract(sample_data)
        
        # Vérifier que toutes les features sont présentes
        for feature in extractor.feature_names:
            assert feature in result.columns, f"Feature {feature} manquante"
        
        # Vérifier le nombre de lignes (inchangé)
        assert len(result) == len(sample_data)
    
    def test_co_occurrence_score(self, extractor, sample_data):
        """Test: calcul du co-occurrence score"""
        result = extractor.extract(sample_data)
        
        # AI coding revolution: 3 plateformes (tiktok, reddit, instagram)
        ai_rows = result[result['topic'] == 'AI coding revolution']
        co_occurrence = ai_rows['co_occurrence_score'].iloc[0]
        
        # 3 plateformes sur 6 possibles = 0.5
        assert co_occurrence == pytest.approx(0.5, rel=0.01)
    
    def test_platform_diversity(self, extractor, sample_data):
        """Test: calcul de la diversité de plateformes"""
        result = extractor.extract(sample_data)
        
        # AI coding revolution: 3 plateformes
        ai_rows = result[result['topic'] == 'AI coding revolution']
        diversity = ai_rows['platform_diversity'].iloc[0]
        assert diversity == 3.0
        
        # Cat videos: 2 plateformes
        cat_rows = result[result['topic'] == 'Cat videos']
        diversity = cat_rows['platform_diversity'].iloc[0]
        assert diversity == 2.0
    
    def test_cross_platform_velocity(self, extractor, sample_data):
        """Test: calcul de la vitesse cross-platform"""
        result = extractor.extract(sample_data)
        
        # AI coding: 3 plateformes en 4h (tiktok à t=0, reddit à t=4h)
        # velocity = 3 plateformes / 4 heures = 0.75
        ai_rows = result[result['topic'] == 'AI coding revolution']
        velocity = ai_rows['cross_platform_velocity'].iloc[0]
        assert velocity == pytest.approx(0.75, rel=0.01)
    
    def test_engagement_ratio(self, extractor, sample_data):
        """Test: calcul du ratio d'engagement"""
        result = extractor.extract(sample_data)
        
        # AI coding: max=1500 (reddit), min=800 (instagram)
        # ratio = 1500/800 = 1.875
        ai_rows = result[result['topic'] == 'AI coding revolution']
        ratio = ai_rows['cross_platform_engagement_ratio'].iloc[0]
        assert ratio == pytest.approx(1.875, rel=0.01)
    
    def test_platform_dominance(self, extractor, sample_data):
        """Test: calcul de la dominance par plateforme"""
        result = extractor.extract(sample_data)
        
        ai_rows = result[result['topic'] == 'AI coding revolution']
        
        # Total engagement: 1000 + 1500 + 800 = 3300
        # tiktok: 1000/3300 ≈ 0.303
        # reddit: 1500/3300 ≈ 0.455
        # instagram: 800/3300 ≈ 0.242
        assert ai_rows['tiktok_dominance'].iloc[0] == pytest.approx(0.303, rel=0.01)
        assert ai_rows['reddit_dominance'].iloc[0] == pytest.approx(0.455, rel=0.01)
        assert ai_rows['instagram_dominance'].iloc[0] == pytest.approx(0.242, rel=0.01)
        assert ai_rows['youtube_dominance'].iloc[0] == 0.0  # Pas présent
    
    def test_lag_correlation_tiktok_reddit(self, extractor, sample_data):
        """Test: corrélation avec lag TikTok → Reddit"""
        result = extractor.extract(sample_data)
        
        # TikTok à t=0, Reddit à t=4h → lag de 4h (dans fenêtre 2-6h)
        ai_rows = result[result['topic'] == 'AI coding revolution']
        lag_corr = ai_rows['lag_correlation_tiktok_to_reddit'].iloc[0]
        
        # Doit être > 0 car lag valide détecté
        assert lag_corr > 0
    
    def test_empty_dataframe(self, extractor):
        """Test: gestion d'un DataFrame vide"""
        empty_df = pd.DataFrame()
        result = extractor.extract(empty_df)
        
        assert result.empty
        assert all(col in result.columns for col in extractor.feature_names)
    
    def test_single_platform(self, extractor):
        """Test: trend sur une seule plateforme"""
        single_platform_data = pd.DataFrame([{
            'topic': 'Single platform trend',
            'platform': 'tiktok',
            'created_at': datetime(2024, 11, 4, 10, 0, 0),
            'engagement': 1000,
            'views': 50000
        }])
        
        result = extractor.extract(single_platform_data)
        
        # Co-occurrence: 1 plateforme sur 6 = 0.1667
        assert result['co_occurrence_score'].iloc[0] == pytest.approx(0.1667, rel=0.01)
        
        # Diversity: 1
        assert result['platform_diversity'].iloc[0] == 1.0
        
        # Velocity: 1 plateforme instantanée
        assert result['cross_platform_velocity'].iloc[0] == 1.0
    
    def test_missing_engagement_column(self, extractor):
        """Test: gestion de colonnes manquantes (engagement)"""
        data_no_engagement = pd.DataFrame([
            {
                'topic': 'Test topic',
                'platform': 'tiktok',
                'created_at': datetime(2024, 11, 4, 10, 0, 0),
                'views': 50000
            },
            {
                'topic': 'Test topic',
                'platform': 'reddit',
                'created_at': datetime(2024, 11, 4, 14, 0, 0),
                'views': 30000
            }
        ])
        
        # Ne doit pas crasher, utiliser valeurs par défaut
        result = extractor.extract(data_no_engagement)
        assert not result.empty
        
        # Dominance doit être 0 si pas d'engagement
        assert result['tiktok_dominance'].iloc[0] == 0.0
    
    def test_transfer_score(self, extractor, sample_data):
        """Test: calcul du transfer score"""
        result = extractor.extract(sample_data)
        
        # AI coding: engagement augmente (1000 → 800 → 1500)
        # Doit avoir un transfer score > 0
        ai_rows = result[result['topic'] == 'AI coding revolution']
        transfer_score = ai_rows['topic_transfer_score'].iloc[0]
        assert transfer_score > 0
        assert transfer_score <= 1.0  # Normalisé entre 0 et 1
    
    def test_all_lag_correlations_present(self, extractor, sample_data):
        """Test: toutes les lag correlations sont calculées"""
        result = extractor.extract(sample_data)
        
        expected_lags = [
            'lag_correlation_tiktok_to_reddit',
            'lag_correlation_tiktok_to_instagram',
            'lag_correlation_instagram_to_twitter',
            'lag_correlation_youtube_to_tiktok',
            'lag_correlation_reddit_to_twitter'
        ]
        
        for lag_feature in expected_lags:
            assert lag_feature in result.columns
            # Valeur doit être entre 0 et 1
            assert result[lag_feature].iloc[0] >= 0
            assert result[lag_feature].iloc[0] <= 1.0
    
    def test_feature_names_count(self, extractor):
        """Test: nombre correct de features"""
        assert len(extractor.feature_names) == 14
        
        # Vérifier que chaque feature est unique
        assert len(extractor.feature_names) == len(set(extractor.feature_names))
    
    def test_supported_platforms(self, extractor):
        """Test: plateformes supportées"""
        expected_platforms = ['tiktok', 'reddit', 'instagram', 'youtube', 'twitter', 'facebook']
        assert extractor.SUPPORTED_PLATFORMS == expected_platforms


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
