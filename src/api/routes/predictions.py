"""
API Routes - Predictions & Comparisons.

Endpoints pour prédictions exactes et comparaisons multi-plateformes.
Utilise AdvancedMetricsPredictor et MultiPlatformCollector.

Author: Trend & Viral Engine Pro
Date: 11 novembre 2025
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from loguru import logger

from src.services.scoring.advanced_metrics_predictor import (
    AdvancedMetricsPredictor,
    MetricsPrediction
)
from src.services.ingestion.multiplatform_collector import MultiPlatformCollector


router = APIRouter(prefix="/api/v1", tags=["Predictions"])


# ============================================================================
# MODELS
# ============================================================================

class PredictRequest(BaseModel):
    """Request pour prédiction single-platform."""
    
    title: str = Field(..., description="Titre du contenu", min_length=3)
    platform: str = Field(..., description="Plateforme (tiktok, instagram, youtube, reddit)")
    follower_count: int = Field(..., description="Nombre de followers", ge=0)
    content_type: Optional[str] = Field(None, description="Type contenu (video, image, text)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Top 10 AI Tools in 2025",
                "platform": "tiktok",
                "follower_count": 50000,
                "content_type": "video"
            }
        }


class PredictResponse(BaseModel):
    """Response prédiction complète."""
    
    # Identification
    prediction_id: str
    title: str
    platform: str
    
    # Métriques prédites
    predicted_views: int
    views_range: Dict[str, int]  # {"min": X, "max": Y}
    
    predicted_likes: int
    likes_range: Dict[str, int]
    
    predicted_comments: int
    predicted_shares: int
    
    # Engagement
    engagement_rate: float
    viral_probability: float
    
    # Monétisation
    estimated_revenue: float
    estimated_cost: float
    roi_percentage: float
    
    # Recommandations
    best_posting_time: str
    best_posting_day: str
    recommendations: List[str]
    
    # 🆕 PROJECTION 7 JOURS (pour graphique frontend)
    projection_7_days: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Projection views 7 jours: [{day: 1, views: 1000}, ...]"
    )


class CompareRequest(BaseModel):
    """Request pour comparaison multi-plateformes."""
    
    title: str = Field(..., description="Titre du contenu")
    platforms: List[str] = Field(..., description="Plateformes à comparer")
    follower_counts: Dict[str, int] = Field(..., description="Followers par plateforme")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Amazing AI Demo",
                "platforms": ["tiktok", "instagram", "youtube"],
                "follower_counts": {
                    "tiktok": 10000,
                    "instagram": 25000,
                    "youtube": 5000
                }
            }
        }


class CompareResponse(BaseModel):
    """Response comparaison multi-plateformes."""
    
    title: str
    comparison_id: str
    platforms_analyzed: List[str]
    best_platform: str
    predictions: Dict[str, Dict[str, Any]]  # {platform: prediction}
    summary: Dict[str, Any]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/predict", response_model=PredictResponse, status_code=status.HTTP_200_OK)
async def predict_content(request: PredictRequest):
    """
    🎯 Prédire métriques exactes pour un contenu.
    
    Retourne prédictions complètes:
    - Vues, likes, comments, shares
    - Engagement rate & probabilité virale
    - Revenue estimé & ROI
    - Meilleur moment de publication
    - Recommandations personnalisées
    
    Utilise AdvancedMetricsPredictor avec modèles calibrés.
    """
    try:
        logger.info(f"Prediction request: {request.title} on {request.platform}")
        
        # Créer predictor
        predictor = AdvancedMetricsPredictor()
        
        # TODO: Scorer le titre avec ML model pour obtenir viral_score
        # Pour l'instant, utiliser score basique basé sur longueur/mots-clés
        viral_score = _estimate_viral_score(request.title, request.platform)
        
        # Prédire métriques
        prediction = predictor.predict_metrics(
            viral_score=viral_score,
            platform=request.platform,
            follower_count=request.follower_count
        )
        
        # Construire response
        import uuid
        
        # 🆕 Générer projection 7 jours pour graphique frontend
        projection_7_days = [
            {
                "day": i + 1,
                "views": int(prediction.predicted_views * (1 + i * 0.15)),
                "date": f"Jour {i+1}"
            }
            for i in range(7)
        ]
        
        response = PredictResponse(
            prediction_id=str(uuid.uuid4()),
            title=request.title,
            platform=request.platform,
            
            predicted_views=prediction.predicted_views,
            views_range={
                "min": prediction.views_range[0],
                "max": prediction.views_range[1]
            },
            
            predicted_likes=prediction.predicted_likes,
            likes_range={
                "min": prediction.likes_range[0],
                "max": prediction.likes_range[1]
            },
            
            predicted_comments=prediction.predicted_comments,
            predicted_shares=prediction.predicted_shares,
            
            engagement_rate=prediction.engagement_rate,
            viral_probability=prediction.viral_probability,
            
            estimated_revenue=prediction.estimated_revenue,
            estimated_cost=prediction.estimated_cost,
            roi_percentage=prediction.roi_percentage,
            
            best_posting_time=prediction.best_posting_time,
            best_posting_day=prediction.best_posting_day,
            recommendations=prediction.recommendations,
            
            # 🆕 Ajouter projection
            projection_7_days=projection_7_days
        )
        
        logger.info(f"Prediction completed: {prediction.predicted_views:,} views, {prediction.estimated_revenue:.2f}€")
        return response
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )


@router.post("/compare", response_model=CompareResponse, status_code=status.HTTP_200_OK)
async def compare_platforms(request: CompareRequest):
    """
    📊 Comparer prédictions across multiple platforms.
    
    Retourne comparaison détaillée:
    - Prédictions par plateforme
    - Meilleure plateforme (ROI max)
    - Résumé comparatif
    
    Permet de choisir où publier pour maximiser engagement/revenue.
    """
    try:
        logger.info(f"Comparison request: {request.title} across {len(request.platforms)} platforms")
        
        predictor = AdvancedMetricsPredictor()
        predictions = {}
        
        # Prédire pour chaque plateforme
        for platform in request.platforms:
            if platform not in request.follower_counts:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing follower count for platform: {platform}"
                )
            
            viral_score = _estimate_viral_score(request.title, platform)
            
            pred = predictor.predict_metrics(
                viral_score=viral_score,
                platform=platform,
                follower_count=request.follower_counts[platform]
            )
            
            predictions[platform] = {
                "views": pred.predicted_views,
                "likes": pred.predicted_likes,
                "engagement_rate": pred.engagement_rate,
                "revenue": pred.estimated_revenue,
                "roi": pred.roi_percentage,
                "viral_probability": pred.viral_probability
            }
        
        # Déterminer meilleure plateforme (ROI max)
        best_platform = max(
            predictions.items(),
            key=lambda x: x[1]["roi"]
        )[0]
        
        # Résumé
        summary = {
            "total_estimated_views": sum(p["views"] for p in predictions.values()),
            "total_estimated_revenue": sum(p["revenue"] for p in predictions.values()),
            "best_roi": predictions[best_platform]["roi"],
            "average_engagement": sum(p["engagement_rate"] for p in predictions.values()) / len(predictions)
        }
        
        import uuid
        response = CompareResponse(
            title=request.title,
            comparison_id=str(uuid.uuid4()),
            platforms_analyzed=request.platforms,
            best_platform=best_platform,
            predictions=predictions,
            summary=summary
        )
        
        logger.info(f"Comparison completed: Best platform = {best_platform} (ROI: {predictions[best_platform]['roi']:.1f}%)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison error: {str(e)}"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _estimate_viral_score(title: str, platform: str) -> float:
    """
    Estimer score viral basique (0-1).
    
    TODO: Remplacer par vrai modèle ML (LightGBM/Ensemble).
    
    Pour l'instant utilise heuristiques:
    - Longueur titre optimale
    - Mots-clés viraux
    - Plateforme
    """
    score = 0.5  # Base
    
    # Longueur optimale
    title_len = len(title)
    if 30 <= title_len <= 60:
        score += 0.1
    elif title_len < 20 or title_len > 80:
        score -= 0.1
    
    # Mots-clés viraux
    viral_keywords = [
        'ai', 'top', 'best', 'amazing', 'viral', 'trending',
        'how to', 'tutorial', 'secret', 'hack', 'tips'
    ]
    
    title_lower = title.lower()
    for keyword in viral_keywords:
        if keyword in title_lower:
            score += 0.05
    
    # Bonus plateforme
    if platform == 'tiktok':
        score += 0.1  # TikTok plus viral
    elif platform == 'youtube':
        score += 0.05
    
    # Clamp [0, 1]
    return max(0.0, min(1.0, score))
