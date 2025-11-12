"""
Service Interfaces - Protocols pour Dependency Injection.

Définit interfaces (Protocol) pour tous les services principaux.
Permet Dependency Inversion Principle (SOLID).

Usage:
    from src.core.interfaces import IScoringService, IIngestionService
    
    # Type hint avec interface
    def process(scoring: IScoringService):
        scores = scoring.predict(features)

Author: Trend & Viral Engine Pro
Date: 11 novembre 2025
"""

from typing import Protocol, List, Dict, Any, Optional
import pandas as pd
import numpy as np


class IScoringService(Protocol):
    """
    Interface pour Scoring Service.
    
    Service de prédiction de scores viraux.
    """
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """
        Prédire scores viraux.
        
        Args:
            features: DataFrame avec features ML
        
        Returns:
            Array de scores (0-1)
        """
        ...
    
    def score(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Scorer DataFrame complet.
        
        Args:
            data: DataFrame avec features
        
        Returns:
            DataFrame avec colonne 'score' ajoutée
        """
        ...


class IIngestionService(Protocol):
    """
    Interface pour Ingestion Service.
    
    Service de collecte de données depuis sources externes.
    """
    
    async def collect(
        self,
        source: str,
        **kwargs: Any
    ) -> pd.DataFrame:
        """
        Collecter données d'une source.
        
        Args:
            source: Nom de la source (reddit, google_trends, etc.)
            **kwargs: Paramètres spécifiques à la source
        
        Returns:
            DataFrame avec données collectées
        """
        ...
    
    async def run_collection(
        self,
        sources: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Lancer collecte multi-sources.
        
        Args:
            sources: Liste sources à collecter (None = toutes)
        
        Returns:
            Dictionnaire {source: DataFrame}
        """
        ...


class IFeatureService(Protocol):
    """
    Interface pour Feature Service.
    
    Service d'extraction de features ML.
    """
    
    def extract(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Extraire features ML.
        
        Args:
            data: DataFrame avec données brutes
        
        Returns:
            DataFrame avec features extraites
        """
        ...
    
    def extract_from_file(self, input_path: str) -> pd.DataFrame:
        """
        Extraire features depuis fichier.
        
        Args:
            input_path: Chemin fichier Parquet
        
        Returns:
            DataFrame avec features
        """
        ...


class ISelectionService(Protocol):
    """
    Interface pour Selection Service.
    
    Service de sélection Top-K trends.
    """
    
    def select_top_k(
        self,
        scored_df: pd.DataFrame,
        k: int = 10,
        diversity: bool = True
    ) -> pd.DataFrame:
        """
        Sélectionner Top K tendances.
        
        Args:
            scored_df: DataFrame avec scores
            k: Nombre de tendances à sélectionner
            diversity: Appliquer diversification
        
        Returns:
            DataFrame avec Top K tendances
        """
        ...


class IGeneratorService(Protocol):
    """
    Interface pour Generator Service.
    
    Service de génération de contenu (scripts, vidéos).
    """
    
    async def generate_content(
        self,
        topic: str,
        format: str = "video",
        duration: int = 25
    ) -> Dict[str, Any]:
        """
        Générer contenu.
        
        Args:
            topic: Sujet du contenu
            format: Format (video, script, caption)
            duration: Durée en secondes
        
        Returns:
            Dictionnaire avec paths des fichiers générés
        """
        ...


class IFeedbackService(Protocol):
    """
    Interface pour Feedback Service.
    
    Service de collecte et traitement du feedback.
    """
    
    async def submit_feedback(
        self,
        content_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Soumettre feedback.
        
        Args:
            content_id: ID du contenu
            metrics: Métriques (views, likes, etc.)
        """
        ...
    
    def should_retrain(self) -> bool:
        """
        Vérifier si retraining nécessaire.
        
        Returns:
            True si ≥100 nouveaux feedbacks
        """
        ...


class IDataRepository(Protocol):
    """
    Interface pour Data Repository.
    
    Abstraction du stockage de données (Parquet, DuckDB, S3, etc.).
    """
    
    def save(
        self,
        data: pd.DataFrame,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Sauvegarder données.
        
        Args:
            data: DataFrame à sauvegarder
            metadata: Métadonnées optionnelles
        
        Returns:
            ID/path du fichier sauvegardé
        """
        ...
    
    def load(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Charger données avec filtres optionnels.
        
        Args:
            filters: Filtres à appliquer (ex: {'source': 'reddit'})
        
        Returns:
            DataFrame avec données filtrées
        """
        ...
    
    def list_files(self) -> List[str]:
        """
        Lister fichiers disponibles.
        
        Returns:
            Liste des noms de fichiers
        """
        ...


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'IScoringService',
    'IIngestionService',
    'IFeatureService',
    'ISelectionService',
    'IGeneratorService',
    'IFeedbackService',
    'IDataRepository',
]
