"""
FastAPI application - Main API server.
Exposes endpoints for scoring, trends, generation, and feedback.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from src.core.config import settings
from src.services.feedback import get_feedback_service
from src.services.generator import get_generator_service
from src.services.ingestion import get_ingestion_service
from src.services.scoring import get_scoring_service
from src.services.selection import get_selection_service
from src.services.post_analyzer import get_post_analyzer_service

# Import new prediction routes
from src.api.routes.predictions import router as predictions_router


# Pydantic models
class ScoreRequest(BaseModel):
    """Request model for scoring endpoint."""

    topic: str = Field(..., description="Topic to score")
    hashtags: Optional[List[str]] = Field(default=None, description="Related hashtags")
    country: Optional[str] = Field(default="FR", description="Country code")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ScoreResponse(BaseModel):
    """Response model for scoring endpoint."""

    score: float = Field(..., description="Breakout probability (0-1)")
    predicted_views_24h: int = Field(..., description="Predicted views in 24h")
    confidence: float = Field(..., description="Prediction confidence")
    features_used: List[str] = Field(..., description="Features used for prediction")


class TrendItem(BaseModel):
    """Model for a single trend item."""

    topic: str
    score: float
    predicted_views: int
    country: str
    rank: int


class TopKResponse(BaseModel):
    """Response model for top K trends."""

    trends: List[TrendItem]
    count: int
    country: Optional[str]
    generated_at: str


class GenerateRequest(BaseModel):
    """Request model for content generation."""

    topic: str = Field(..., description="Topic for content")
    format: str = Field(default="video", description="Content format (video, script, caption)")
    duration: Optional[int] = Field(default=25, description="Video duration in seconds")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class GenerateResponse(BaseModel):
    """Response model for content generation."""

    content_id: str
    topic: str
    video_path: Optional[str]
    caption_path: Optional[str]
    script: Dict[str, str]
    generated_at: str


class FeedbackRequest(BaseModel):
    """Request model for feedback submission."""

    content_id: str = Field(..., description="Content identifier")
    views: int = Field(..., ge=0, description="Number of views")
    likes: int = Field(..., ge=0, description="Number of likes")
    comments: int = Field(default=0, ge=0, description="Number of comments")
    watch_time: float = Field(default=0.0, ge=0.0, le=1.0, description="Watch time ratio")
    shares: int = Field(default=0, ge=0, description="Number of shares")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str


class StatsOverview(BaseModel):
    """Dashboard stats overview."""
    
    trends_collected: int
    predictions_made: int
    videos_generated: int
    model_accuracy: float


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Trend & Viral Engine Pro API")
    settings.ensure_directories()
    yield
    logger.info("Shutting down API")


# Create FastAPI app
app = FastAPI(
    title="Trend & Viral Engine Pro API",
    description="API for viral trend detection and content generation",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Include prediction routes
app.include_router(predictions_router)

# 🆕 SERVIR FICHIERS STATIQUES (vidéos, images, etc.)
from fastapi.staticfiles import StaticFiles

# Créer dossier outputs s'il n'existe pas
Path("outputs").mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
logger.info("Static files mounted: /outputs")


# Health check
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.environment,
    )


# 🆕 STATS OVERVIEW ENDPOINT (pour dashboard)
@app.get("/api/v1/stats/overview", response_model=StatsOverview, tags=["Stats"])
async def get_stats_overview():
    """
    Get dashboard overview statistics.
    
    Returns real-time counts for:
    - Trends collected
    - Predictions made
    - Videos generated
    - Model accuracy
    """
    try:
        # Count trends collected (fichiers parquet dans data/raw)
        trends_path = settings.data_raw_path
        trends_count = len(list(trends_path.glob("*.parquet"))) if trends_path.exists() else 0
        
        # Count predictions (fichiers feedback dans data/feedback)
        feedback_path = settings.data_feedback_path
        predictions_count = len(list(feedback_path.glob("*.json"))) if feedback_path.exists() else 0
        
        # Count videos generated (fichiers MP4 dans outputs)
        outputs_path = Path("outputs")
        videos_count = len(list(outputs_path.glob("*.mp4"))) if outputs_path.exists() else 0
        
        # Get model accuracy (TODO: charger depuis MLflow)
        # Pour l'instant, valeur statique
        model_accuracy = 0.873
        
        logger.info(f"Stats: {trends_count} trends, {predictions_count} predictions, {videos_count} videos")
        
        return StatsOverview(
            trends_collected=trends_count,
            predictions_made=predictions_count,
            videos_generated=videos_count,
            model_accuracy=model_accuracy
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting stats: {str(e)}"
        )


# Score endpoint
@app.post("/api/v1/score", response_model=ScoreResponse, tags=["Scoring"])
async def score_topic(request: ScoreRequest):
    """
    Score a topic for viral potential.

    Returns predicted viral score (0-1) and estimated 24h views.
    """
    try:
        # Create raw data with timestamp
        from datetime import datetime
        import tempfile
        
        raw_data = pd.DataFrame([{
            "topic": request.topic,
            "country": request.country,
            "collected_at": datetime.now(),
            "source": "api_request",
        }])

        # Save to temp file for feature extraction
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.parquet', delete=False) as tmp:
            temp_path = Path(tmp.name)
            raw_data.to_parquet(temp_path, engine="pyarrow", index=False)

        # Extract features using FeatureService
        from src.services.features import get_feature_service
        feature_service = get_feature_service()
        
        feature_path = feature_service.process_raw_data(temp_path)
        features_df = pd.read_parquet(feature_path)
        
        # Keep ONLY embedding columns (same as training)
        emb_cols = [col for col in features_df.columns if col.startswith("emb_")]
        features_df = features_df[emb_cols]
        
        # Cleanup temp files
        temp_path.unlink(missing_ok=True)
        feature_path.unlink(missing_ok=True)

        # Get scoring service and score
        scoring_service = get_scoring_service()
        scores = scoring_service.score(features_df)

        return ScoreResponse(
            score=float(scores["p_breakout_24h"].iloc[0]),
            predicted_views_24h=int(scores["predicted_views_24h"].iloc[0]),
            confidence=0.85,  # Placeholder
            features_used=list(features_df.columns),
        )

    except Exception as e:
        logger.error(f"Error scoring topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scoring topic: {str(e)}",
        )


# Top K trends endpoint
@app.get("/api/v1/trends/topK", response_model=TopKResponse, tags=["Trends"])
async def get_top_k_trends(
    country: Optional[str] = Query(default=None, description="Filter by country"),
    k: int = Query(default=10, ge=1, le=100, description="Number of trends to return"),
):
    """
    Get top K trending topics.

    Returns the most promising topics based on viral potential scores.
    """
    try:
        # In production, this would load latest scored data
        # For now, return mock data
        from datetime import datetime

        trends = [
            TrendItem(
                topic=f"Trend {i+1}",
                score=0.9 - (i * 0.05),
                predicted_views=100000 - (i * 5000),
                country=country or "FR",
                rank=i + 1,
            )
            for i in range(k)
        ]

        return TopKResponse(
            trends=trends,
            count=len(trends),
            country=country,
            generated_at=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error getting top K trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting trends: {str(e)}",
        )


# 🆕 NOUVEAUX ENDPOINTS POUR FRONTEND

# ============================================================================
# ENDPOINT CRITIQUE: Analyze Post from URL
# ============================================================================

class AnalyzePostRequest(BaseModel):
    """Request model for post analysis."""
    
    url: str = Field(..., description="URL du post (Instagram, TikTok, Facebook, etc.)")
    extract_content: bool = Field(default=True, description="Extraire images/vidéos")


class AnalyzePostResponse(BaseModel):
    """Response model for post analysis."""
    
    url: str
    platform: str
    metadata: Dict[str, Any]
    analysis: Dict[str, Any]
    content_path: Optional[str]
    analyzed_at: str


@app.post("/api/v1/analyze-post", response_model=AnalyzePostResponse, tags=["Analysis"])
async def analyze_post(request: AnalyzePostRequest):
    """
    🎯 FONCTIONNALITÉ CRITIQUE: Analyser un post depuis son URL.
    
    Fonctionnalités:
    1. Extraction metadata (titre, likes, comments, views)
    2. Download images/vidéos (optionnel)
    3. Calcul viral score et engagement rate
    4. Identification facteurs de succès
    5. Recommandations d'amélioration
    
    Plateformes supportées: Instagram, TikTok, Facebook, Twitter, Reddit, YouTube
    """
    try:
        analyzer_service = get_post_analyzer_service()
        
        result = await analyzer_service.analyze_post(
            url=request.url,
            extract_content=request.extract_content
        )
        
        return AnalyzePostResponse(
            url=result["url"],
            platform=result["platform"],
            metadata=result["metadata"],
            analysis=result["analysis"],
            content_path=result.get("content_path"),
            analyzed_at=result["analyzed_at"]
        )
        
    except ValueError as e:
        logger.error(f"Invalid URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL invalide ou plateforme non supportée: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error analyzing post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse: {str(e)}"
        )


# ============================================================================
# AUTRES ENDPOINTS NOUVEAUX
# ============================================================================

# Trends collection endpoint (frontend needs this)
@app.post("/api/v1/trends/collect", tags=["Trends"])
async def collect_trends(sources: Optional[List[str]] = None):
    """
    Déclenche la collecte manuelle de tendances.
    
    Frontend: bouton "Lancer Collecte" dans page Trends.
    """
    try:
        ingestion_service = get_ingestion_service()
        
        # Use default sources if none provided
        if not sources:
            sources = ["google_trends", "reddit"]
        
        results = await ingestion_service.run_collection(sources)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Collection completed",
                "collected": sum(1 for v in results.values() if v),
                "sources": sources,
            },
        )

    except Exception as e:
        logger.error(f"Error collecting trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error collecting trends: {str(e)}",
        )


# Generate script only (frontend needs this)
@app.post("/api/v1/generate/script", tags=["Generation"])
async def generate_script_only(
    topic: str,
    platform: str = "tiktok",
    duration: int = 60
):
    """
    Génère uniquement le script avec Groq LLM.
    
    Frontend: bouton "Générer Script" dans page Generation.
    """
    try:
        generator_service = get_generator_service()
        
        # Generate script using ScriptGenerator
        script_dict = await generator_service.script_gen.generate(
            topic=topic,
            context={"duration": duration, "platform": platform}
        )
        
        # Convert dict to readable string for frontend display
        script_text = f"""HOOK ({duration//3}s):
{script_dict['hook']}

PAYOFF ({duration*2//3}s):
{script_dict['payoff']}

CTA ({duration//10}s):
{script_dict['cta']}

CAPTION:
{script_dict['caption']}"""

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "script": script_text,
                "script_dict": script_dict,
                "topic": topic,
                "platform": platform,
                "duration": duration,
            },
        )

    except Exception as e:
        logger.error(f"Error generating script: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating script: {str(e)}",
        )


# Generate video from script (frontend needs this)
@app.post("/api/v1/generate/video", tags=["Generation"])
async def generate_video_from_script(
    script: str,
    platform: str = "tiktok",
    style: str = "modern"
):
    """
    Génère vidéo MP4 à partir d'un script avec MoviePy.
    
    Frontend: bouton "Générer Vidéo" dans page Generation.
    """
    try:
        generator_service = get_generator_service()
        
        # Parse script string to dict if needed
        import re
        script_dict = {}
        
        # Extract sections from formatted script
        hook_match = re.search(r'HOOK.*?:\s*(.*?)(?=\n\n|PAYOFF)', script, re.DOTALL)
        payoff_match = re.search(r'PAYOFF.*?:\s*(.*?)(?=\n\nCTA)', script, re.DOTALL)
        cta_match = re.search(r'CTA.*?:\s*(.*?)(?=\n\nCAPTION|$)', script, re.DOTALL)
        caption_match = re.search(r'CAPTION:\s*(.*?)$', script, re.DOTALL)
        
        script_dict = {
            "hook": hook_match.group(1).strip() if hook_match else "🔥 Regarde ça !",
            "payoff": payoff_match.group(1).strip() if payoff_match else script[:200],
            "cta": cta_match.group(1).strip() if cta_match else "💡 Like si tu as aimé !",
            "caption": caption_match.group(1).strip() if caption_match else "#viral"
        }
        
        # Generate video using VideoGenerator  
        video_path = generator_service.video_gen.generate(script_dict)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "video_path": str(video_path),
                "platform": platform,
                "style": style,
                "message": "Vidéo générée avec succès"
            },
        )

    except Exception as e:
        logger.error(f"Error generating video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating video: {str(e)}",
        )


# Generate content endpoint (legacy, kept for compatibility)
@app.post("/api/v1/generate", response_model=GenerateResponse, tags=["Generation"])
async def generate_content(request: GenerateRequest):
    """
    Generate content (script, video, caption) for a topic.

    Uses Groq LLM for scripts and MoviePy for video generation.
    """
    try:
        generator_service = get_generator_service()

        # Generate content
        result = await generator_service.generate_content(
            topic=request.topic,
            context=request.context or {"duration": request.duration},
        )

        return GenerateResponse(
            content_id=result["video_path"].split("/")[-1].replace(".mp4", ""),
            topic=result["topic"],
            video_path=result.get("video_path"),
            caption_path=result.get("caption_path"),
            script=result["script"],
            generated_at=result["generated_at"],
        )

    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating content: {str(e)}",
        )


# Feedback endpoint
@app.post("/api/v1/feedback", tags=["Feedback"])
async def submit_feedback(request: FeedbackRequest):
    """
    Submit performance feedback for published content.

    Used to improve the model through the learning loop.
    """
    try:
        feedback_service = get_feedback_service()

        result = feedback_service.submit_feedback(
            content_id=request.content_id,
            views=request.views,
            likes=request.likes,
            comments=request.comments,
            watch_time=request.watch_time,
            shares=request.shares,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Feedback recorded successfully",
                "should_retrain": result["should_retrain"],
            },
        )

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting feedback: {str(e)}",
        )


# Ingestion trigger endpoint (admin)
@app.post("/api/v1/admin/trigger-ingestion", tags=["Admin"])
async def trigger_ingestion(sources: Optional[List[str]] = None):
    """
    Manually trigger data ingestion.

    Admin endpoint to force data collection.
    """
    try:
        ingestion_service = get_ingestion_service()
        results = await ingestion_service.run_collection(sources)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Ingestion completed",
                "sources": list(results.keys()),
                "files": [str(p) for p in results.values() if p],
            },
        )

    except Exception as e:
        logger.error(f"Error triggering ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering ingestion: {str(e)}",
        )


# 🚀 ULTRA-COLLECTOR ENDPOINTS
@app.post("/api/v1/ultra/collect", tags=["Ultra-Collector"])
async def ultra_collect(
    force_refresh: bool = Query(default=False, description="Force refresh (ignore cache)"),
    sources: Optional[List[str]] = Query(default=None, description="Specific sources to collect (None=all)"),
):
    """
    🚀 Ultra-robust parallel collection from 4 sources.
    
    Features:
    - Circuit Breaker per source
    - Cache with TTL
    - Fallback strategies
    - Parallel execution with Bulkhead pattern
    
    Sources: reddit, google_trends, facebook, tiktok
    """
    try:
        from src.services.ingestion.ultra_collector import get_ultra_collector
        
        collector = get_ultra_collector()
        
        # Collect from selected sources
        results = await collector.collect_all(
            force_refresh=force_refresh,
            sources=sources,
            reddit={"subreddits": ["trending", "viral", "popular"], "limit": 50},
            google_trends={"regions": ["US"]},
            facebook={"query": "viral video", "limit": 50},
            tiktok={"limit": 50}
        )
        
        # Build response
        summary = {
            "total_items": sum(len(items) for items in results.values()),
            "sources_count": len(results),
            "sources_successful": sum(1 for items in results.values() if len(items) > 0),
            "breakdown": {
                source: len(items)
                for source, items in results.items()
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Ultra collection completed",
                "summary": summary,
                "data": results
            }
        )
        
    except Exception as e:
        logger.error(f"Ultra collection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ultra collection error: {str(e)}"
        )


@app.get("/api/v1/ultra/metrics", tags=["Ultra-Collector"])
async def ultra_metrics():
    """
    📊 Get detailed metrics from Ultra-Collector.
    
    Returns:
    - Global metrics (requests, success rate)
    - Per-source metrics (cache hits, fallbacks, breaker state)
    - Cache statistics
    """
    try:
        from src.services.ingestion.ultra_collector import get_ultra_collector
        
        collector = get_ultra_collector()
        
        # Initialize if not done
        if not collector._initialized:
            await collector.initialize()
        
        metrics = collector.get_all_metrics()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"metrics": metrics}
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics error: {str(e)}"
        )


@app.post("/api/v1/ultra/batch", tags=["Ultra-Collector"])
async def ultra_batch(
    target_count: int = Query(default=100, description="Target number of items to collect"),
    force_refresh: bool = Query(default=False, description="Force refresh (ignore cache)"),
):
    """
    🎯 Batch collection with target count.
    
    Collects data from all sources until target is reached.
    Automatically retries with force_refresh if target not met.
    
    Returns DataFrame as JSON.
    """
    try:
        from src.services.ingestion.ultra_collector import get_ultra_collector
        
        collector = get_ultra_collector()
        
        # Collect batch
        df = await collector.collect_batch(
            target_count=target_count,
            force_refresh=force_refresh
        )
        
        if df.empty:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "No data collected",
                    "count": 0,
                    "data": []
                }
            )
        
        # Convert to JSON
        data = df.to_dict(orient="records")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Batch collection completed",
                "count": len(df),
                "target": target_count,
                "sources": df["source"].unique().tolist() if "source" in df.columns else [],
                "data": data
            }
        )
        
    except Exception as e:
        logger.error(f"Batch collection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch collection error: {str(e)}"
        )


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers if not settings.api_reload else 1,
        log_level=settings.log_level.lower(),
    )
