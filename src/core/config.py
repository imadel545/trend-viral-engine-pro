"""
Core configuration module for Trend & Viral Engine Pro.
Manages environment variables and application settings.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=('settings_',),  # Fix Pydantic warnings
    )

    # ========================================
    # Environment
    # ========================================
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # ========================================
    # API Configuration
    # ========================================
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="Number of API workers")
    api_reload: bool = Field(default=False, description="Auto-reload API")
    api_key: str = Field(default="", description="API authentication key")
    secret_key: str = Field(default="", description="Secret key for JWT")

    # ========================================
    # Groq API (LLM)
    # ========================================
    groq_api_key: str = Field(default="", description="Groq API key")
    groq_model: str = Field(
        default="openai/gpt-oss-120b", description="Groq model identifier"
    )
    groq_max_tokens: int = Field(default=2048, description="Max tokens for generation")
    groq_temperature: float = Field(default=0.7, description="LLM temperature")

    # ========================================
    # Data Sources - TikTok
    # ========================================
    tiktok_enabled: bool = Field(default=False, description="Enable TikTok collection")
    tiktok_client_key: str = Field(default="", description="TikTok client key")
    tiktok_client_secret: str = Field(default="", description="TikTok client secret")
    tiktok_api_key: str = Field(default="", description="TikTok API key (legacy)")
    tiktok_api_secret: str = Field(default="", description="TikTok API secret (legacy)")
    tiktok_rate_limit: int = Field(default=60, description="TikTok rate limit per minute")

    # ========================================
    # Data Sources - Google Trends
    # ========================================
    google_trends_enabled: bool = Field(
        default=True, description="Enable Google Trends collection"
    )
    google_trends_regions: str = Field(
        default="FR,MA,US", description="Comma-separated region codes"
    )

    @field_validator("google_trends_regions")
    @classmethod
    def parse_regions(cls, v: str) -> List[str]:
        """Parse comma-separated regions into list."""
        return [r.strip() for r in v.split(",") if r.strip()]

    # ========================================
    # Data Sources - Reddit
    # ========================================
    enable_reddit: bool = Field(default=False, description="Enable Reddit collection")
    reddit_client_id: str = Field(default="", description="Reddit client ID")
    reddit_client_secret: str = Field(default="", description="Reddit client secret")
    reddit_user_agent: str = Field(
        default="TrendEngine/1.0", description="Reddit user agent"
    )
    reddit_subreddits: str = Field(
        default="tiktok,viralvideos,socialmedia",
        description="Comma-separated subreddits",
    )

    @field_validator("reddit_subreddits")
    @classmethod
    def parse_subreddits(cls, v: str) -> List[str]:
        """Parse comma-separated subreddits into list."""
        return [s.strip() for s in v.split(",") if s.strip()]
    
    # ========================================
    # Data Sources - Facebook
    # ========================================
    facebook_enabled: bool = Field(default=False, description="Enable Facebook collection")
    facebook_app_id: str = Field(default="", description="Facebook App ID")
    facebook_app_secret: str = Field(default="", description="Facebook App Secret")
    facebook_access_token: Optional[str] = Field(default=None, description="Facebook Access Token")

    # ========================================
    # Database - DuckDB
    # ========================================
    duckdb_path: str = Field(default="data/trends.duckdb", description="DuckDB file path")
    duckdb_memory_limit: str = Field(default="4GB", description="DuckDB memory limit")

    # ========================================
    # Vector Store - Qdrant
    # ========================================
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API key")
    qdrant_collection: str = Field(
        default="trends_embeddings", description="Qdrant collection name"
    )

    # ========================================
    # MLflow
    # ========================================
    mlflow_tracking_uri: str = Field(
        default="http://localhost:5000", description="MLflow tracking URI"
    )
    mlflow_experiment_name: str = Field(
        default="trend-viral-engine", description="MLflow experiment name"
    )
    mlflow_artifact_location: str = Field(
        default="./mlruns", description="MLflow artifact location"
    )

    # ========================================
    # Model Configuration
    # ========================================
    model_type: str = Field(default="lightgbm", description="Model type")
    model_calibration: str = Field(default="isotonic", description="Calibration method")
    model_threshold: float = Field(default=0.5, description="Classification threshold")
    model_retrain_threshold: int = Field(
        default=100, description="Min samples to trigger retrain"
    )
    min_samples_for_training: int = Field(
        default=500, description="Min samples for initial training"
    )

    # ========================================
    # Feature Engineering
    # ========================================
    embedding_model_text: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        description="Text embedding model",
    )
    embedding_model_vision: str = Field(
        default="openai/clip-vit-base-patch32", description="Vision embedding model"
    )
    embedding_dim: int = Field(default=384, description="Embedding dimension")

    # ========================================
    # Content Generation
    # ========================================
    video_width: int = Field(default=1080, description="Video width in pixels")
    video_height: int = Field(default=1920, description="Video height in pixels")
    video_fps: int = Field(default=30, description="Video frames per second")
    video_duration_min: int = Field(default=20, description="Min video duration (seconds)")
    video_duration_max: int = Field(default=30, description="Max video duration (seconds)")
    tts_enabled: bool = Field(default=True, description="Enable text-to-speech")
    tts_model: str = Field(
        default="tts_models/multilingual/multi-dataset/your_tts", description="TTS model"
    )
    tts_language: str = Field(default="fr", description="TTS language code")

    # ========================================
    # Scheduling
    # ========================================
    ingestion_interval_minutes: int = Field(
        default=10, description="Ingestion interval in minutes"
    )
    feature_update_interval_minutes: int = Field(
        default=15, description="Feature update interval in minutes"
    )
    training_schedule: str = Field(default="0 2 * * *", description="Training cron schedule")
    content_generation_daily: int = Field(
        default=3, description="Number of contents to generate daily"
    )

    # ========================================
    # Selection Strategy
    # ========================================
    top_k_default: int = Field(default=10, description="Default top K value")
    diversity_weight: float = Field(default=0.3, description="Diversity weight in selection")
    exploration_rate: float = Field(default=0.1, description="Exploration rate for bandits")

    # ========================================
    # Monitoring - Prometheus
    # ========================================
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    prometheus_retention: str = Field(default="15d", description="Prometheus retention period")

    # ========================================
    # Monitoring - Grafana
    # ========================================
    grafana_port: int = Field(default=3000, description="Grafana port")
    grafana_admin_user: str = Field(default="admin", description="Grafana admin username")
    grafana_admin_password: str = Field(default="admin", description="Grafana admin password")

    # ========================================
    # Storage Paths
    # ========================================
    data_raw_path: Path = Field(default=Path("data/raw"), description="Raw data path")
    data_features_path: Path = Field(
        default=Path("data/features"), description="Features data path"
    )
    data_labels_path: Path = Field(default=Path("data/labels"), description="Labels data path")
    data_feedback_path: Path = Field(
        default=Path("data/feedback"), description="Feedback data path"
    )
    output_path: Path = Field(default=Path("outputs"), description="Output path")
    models_path: Path = Field(default=Path("models"), description="Models path")

    # ========================================
    # Performance
    # ========================================
    max_workers: int = Field(default=4, description="Max concurrent workers")
    batch_size: int = Field(default=32, description="Batch size for processing")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")

    # ========================================
    # Prefect
    # ========================================
    prefect_api_url: str = Field(
        default="http://localhost:4200/api", description="Prefect API URL"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.data_raw_path,
            self.data_features_path,
            self.data_labels_path,
            self.data_feedback_path,
            self.output_path,
            self.models_path,
            Path("logs"),
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings


# Global settings instance
settings = get_settings()
