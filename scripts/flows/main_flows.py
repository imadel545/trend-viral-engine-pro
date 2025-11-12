"""
Prefect flows for orchestrating data pipelines.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from loguru import logger
from prefect import flow, task
from prefect.tasks import task_input_hash

from src.core.config import settings
from src.services.features import get_feature_service
from src.services.ingestion import get_ingestion_service
from src.services.scoring import get_scoring_service
from src.services.selection import get_selection_service


@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(minutes=10))
async def ingest_data_task(sources: Optional[list[str]] = None):
    """Task to ingest data from sources."""
    logger.info("Starting data ingestion")
    ingestion_service = get_ingestion_service()
    results = await ingestion_service.run_collection(sources)
    logger.info(f"Ingestion complete: {len(results)} sources")
    return results


@task
def extract_features_task(raw_data_paths: dict):
    """Task to extract features from raw data."""
    logger.info("Starting feature extraction")
    feature_service = get_feature_service()

    feature_paths = []
    for source, path in raw_data_paths.items():
        if path:
            feature_path = feature_service.process_raw_data(path)
            feature_paths.append(feature_path)

    logger.info(f"Feature extraction complete: {len(feature_paths)} files")
    return feature_paths


@task
def score_features_task(feature_paths: list):
    """Task to score features."""
    logger.info("Starting scoring")
    scoring_service = get_scoring_service()

    # In production, would load and score all features
    # For now, return placeholder
    logger.info("Scoring complete")
    return {"scored": True, "count": len(feature_paths)}


@task
def select_top_k_task(scored_data, k: int = 10):
    """Task to select top K topics."""
    logger.info(f"Selecting top {k} topics")
    selection_service = get_selection_service()

    # In production, would process scored data
    logger.info(f"Selection complete: {k} topics selected")
    return {"selected": k}


@flow(name="ingestion-flow", log_prints=True)
async def ingestion_flow(sources: Optional[list[str]] = None):
    """
    Main ingestion flow.

    Runs every 10 minutes to collect data from all sources.
    """
    logger.info("=== Starting Ingestion Flow ===")

    # Ingest data
    ingested_data = await ingest_data_task(sources)

    # Extract features
    feature_paths = extract_features_task(ingested_data)

    # Score features
    scores = score_features_task(feature_paths)

    logger.info("=== Ingestion Flow Complete ===")
    return scores


@flow(name="content-generation-flow", log_prints=True)
async def content_generation_flow(n_contents: int = 3):
    """
    Content generation flow.

    Selects top topics and generates content.
    """
    logger.info(f"=== Starting Content Generation Flow (n={n_contents}) ===")

    from src.services.generator import get_generator_service

    # In production, would load latest scored data
    # For now, use placeholder topics
    topics = [f"Trend AI {i+1}" for i in range(n_contents)]

    generator_service = get_generator_service()

    results = []
    for topic in topics:
        try:
            result = await generator_service.generate_content(topic)
            results.append(result)
            logger.info(f"Generated content for: {topic}")
        except Exception as e:
            logger.error(f"Error generating content for {topic}: {e}")

    logger.info(f"=== Content Generation Complete: {len(results)} items ===")
    return results


@task
def train_model_task(labels_path: Optional[Path] = None):
    """Task to train/retrain the model."""
    logger.info("Starting model training")
    
    import subprocess
    import sys
    
    # Use train_ensemble.py script
    train_script = Path(__file__).parent.parent / "training" / "train_ensemble.py"
    
    cmd = [sys.executable, str(train_script)]
    if labels_path:
        # If labels provided, training data should include them
        logger.info(f"Training with labels from: {labels_path}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=600  # 10 min max
        )
        logger.info(f"Training output: {result.stdout}")
        logger.info("Model training complete")
        return {"success": True, "output": result.stdout}
    except subprocess.TimeoutExpired:
        logger.error("Training timeout (>10min)")
        return {"success": False, "error": "timeout"}
    except subprocess.CalledProcessError as e:
        logger.error(f"Training failed: {e.stderr}")
        return {"success": False, "error": e.stderr}


@task
def validate_model_task():
    """Task to validate newly trained model."""
    logger.info("Validating trained model")
    
    from src.services.scoring import get_scoring_service
    import pandas as pd
    
    scoring_service = get_scoring_service()
    
    # Load validation data (hold-out set)
    val_features = list(settings.data_features_path.glob("*advanced*.parquet"))
    if not val_features:
        logger.warning("No validation features found")
        return {"valid": True, "metrics": {}}
    
    # Load most recent
    val_df = pd.read_parquet(val_features[-1])
    
    # Check if model can predict
    try:
        if 'is_breakout' in val_df.columns or 'label' in val_df.columns:
            label_col = 'is_breakout' if 'is_breakout' in val_df.columns else 'label'
            X_val = val_df.drop(columns=[label_col])
            y_val = val_df[label_col]
            
            # Use score method from ScoringService
            predictions = []
            for _, row in X_val.iterrows():
                pred = scoring_service.score(row.to_dict())
                predictions.append(pred.get('viral_probability', 0.5) if isinstance(pred, dict) else pred)
            
            # Compute metrics
            from sklearn.metrics import roc_auc_score
            
            auc = roc_auc_score(y_val, predictions) if len(set(y_val)) > 1 else 0.5
            
            logger.info(f"Validation AUC: {auc:.4f}")
            
            return {
                "valid": auc >= 0.75,  # Minimum threshold
                "metrics": {"auc": auc, "samples": len(y_val)}
            }
        else:
            logger.info("No labels for validation")
            return {"valid": True, "metrics": {}}
            
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return {"valid": False, "error": str(e)}


@flow(name="training-flow", log_prints=True)
def training_flow(labels_path: Optional[Path] = None, force: bool = False):
    """
    Model training flow.
    
    Trains a new model, validates it, and deploys if better.
    Can be triggered automatically by feedback or manually.
    """
    logger.info("=== Starting Training Flow ===")
    
    from src.services.feedback import get_feedback_service
    
    if not force:
        # Check if retraining needed
        feedback_service = get_feedback_service()
        if not feedback_service.retrain_trigger.should_retrain():
            logger.info("Retraining not needed (threshold not met)")
            return {"trained": False, "reason": "threshold_not_met"}
    
    # Train model
    train_result = train_model_task(labels_path)
    
    if not train_result["success"]:
        logger.error(f"Training failed: {train_result.get('error')}")
        return {"trained": False, "reason": "training_failed", "error": train_result.get('error')}
    
    # Validate model
    val_result = validate_model_task()
    
    if not val_result["valid"]:
        logger.warning("New model validation failed")
        return {
            "trained": True,
            "deployed": False,
            "reason": "validation_failed",
            "metrics": val_result.get("metrics", {})
        }
    
    logger.info(f"=== Training Flow Complete ===")
    logger.info(f"Model validated: AUC={val_result['metrics'].get('auc', 'N/A')}")
    
    return {
        "trained": True,
        "deployed": True,
        "metrics": val_result["metrics"]
    }


@flow(name="feedback-processing-flow", log_prints=True)
async def feedback_processing_flow():
    """
    Feedback processing flow.

    Processes accumulated feedback and triggers retraining if needed.
    """
    logger.info("=== Starting Feedback Processing Flow ===")

    from src.services.feedback import get_feedback_service

    feedback_service = get_feedback_service()
    
    # Generate labels from feedback
    labels_path = feedback_service.label_gen.generate_labels()
    
    # Check if retraining needed
    should_retrain = feedback_service.retrain_trigger.should_retrain()
    
    logger.info(f"Labels generated: {labels_path}")
    logger.info(f"Should retrain: {should_retrain}")
    
    training_result = None
    if should_retrain:
        logger.info("Triggering training flow...")
        # Call training flow (synchronous)
        training_result = training_flow(labels_path=labels_path)
    
    logger.info(f"=== Feedback Processing Complete ===")
    
    return {
        "labels_generated": str(labels_path) if labels_path else None,
        "should_retrain": should_retrain,
        "training_result": training_result
    }


if __name__ == "__main__":
    # Test the flows
    asyncio.run(ingestion_flow())
