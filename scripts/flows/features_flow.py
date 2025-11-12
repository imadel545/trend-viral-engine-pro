"""
Features Extraction Flow - Extract features from raw data using FeatureService.
Reads parquet files from data/raw/ and creates features with embeddings in data/features/.
"""

from pathlib import Path

from src.core.config import settings
from src.core.logging import logger
from src.services.features import get_feature_service


def main():
    """Extract features from all raw data files."""
    logger.info("=" * 80)
    logger.info(" FEATURES EXTRACTION FLOW")
    logger.info("=" * 80)
    logger.info("")

    # Get feature service (includes Temporal + Embedding extractors by default)
    feature_service = get_feature_service()

    # Process all raw files with batch_process (uses embeddings)
    logger.info(f"Processing all files from {settings.data_raw_path}")
    output_paths = feature_service.batch_process()

    logger.info("")
    logger.info(f"✓ SUCCESS - Features extracted from {len(output_paths)} files:")
    for path in output_paths:
        logger.info(f"  - {path}")

    logger.info("")
    logger.info("Next step: Run training")
    logger.info("  python -m scripts.training.train_baseline --force")


if __name__ == "__main__":
    main()
