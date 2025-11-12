"""
Feedback Service - Collect metrics and trigger retraining.
Handles the learning loop.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

from src.core.config import settings


class FeedbackCollector:
    """Collect performance metrics."""

    def __init__(self):
        self.logger = logger.bind(service="feedback")

    def record_feedback(
        self,
        content_id: str,
        views: int,
        likes: int,
        comments: int = 0,
        watch_time: float = 0.0,
        shares: int = 0,
    ) -> Path:
        """Record feedback for published content."""
        feedback = {
            "content_id": content_id,
            "views": views,
            "likes": likes,
            "comments": comments,
            "watch_time": watch_time,
            "shares": shares,
            "engagement_rate": (likes + comments + shares) / max(views, 1),
            "recorded_at": datetime.now().isoformat(),
        }

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = settings.data_feedback_path / f"feedback_{content_id}_{timestamp}.json"

        filepath.write_text(json.dumps(feedback, indent=2), encoding="utf-8")
        self.logger.info(f"Feedback recorded for {content_id}: {views} views, {likes} likes")

        return filepath

    def batch_record(self, feedbacks: List[Dict[str, Any]]) -> List[Path]:
        """Record multiple feedbacks."""
        paths = []
        for feedback in feedbacks:
            path = self.record_feedback(**feedback)
            paths.append(path)
        return paths


class LabelGenerator:
    """Generate labels from feedback for training."""

    def __init__(self):
        self.logger = logger.bind(service="labels")

    def generate_labels(self, feedback_dir: Optional[Path] = None) -> Path:
        """Generate training labels from feedback."""
        feedback_dir = feedback_dir or settings.data_feedback_path

        # Load all feedback files
        feedback_files = list(feedback_dir.glob("feedback_*.json"))
        self.logger.info(f"Found {len(feedback_files)} feedback files")

        if not feedback_files:
            self.logger.warning("No feedback files found")
            return None

        feedbacks = []
        for filepath in feedback_files:
            with open(filepath) as f:
                feedbacks.append(json.load(f))

        df = pd.DataFrame(feedbacks)

        # Generate labels
        # Breakout = high views or high engagement
        df["is_breakout"] = (
            (df["views"] > df["views"].quantile(0.75)) |
            (df["engagement_rate"] > df["engagement_rate"].quantile(0.75))
        ).astype(int)

        # Save labels
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = settings.data_labels_path / f"labels_{timestamp}.parquet"

        df.to_parquet(output_path, engine="pyarrow", compression="snappy", index=False)
        self.logger.info(f"Generated {len(df)} labels -> {output_path}")

        return output_path


class RetrainingTrigger:
    """Trigger model retraining when conditions are met."""

    def __init__(self):
        self.logger = logger.bind(service="retrain")

    def should_retrain(self) -> bool:
        """Check if retraining should be triggered."""
        # Check number of new feedback samples
        feedback_files = list(settings.data_feedback_path.glob("feedback_*.json"))
        
        # Count only unique content_ids to avoid duplicates
        content_ids = set()
        for f in feedback_files:
            try:
                import json
                with open(f, 'r') as file:
                    data = json.load(file)
                    content_ids.add(data.get('content_id'))
            except Exception:
                continue
        
        n_samples = len(content_ids)

        if n_samples >= settings.model_retrain_threshold:
            self.logger.info(f"Retraining threshold met: {n_samples} unique samples")
            return True

        self.logger.debug(f"Retraining threshold not met: {n_samples} < {settings.model_retrain_threshold}")
        return False

    async def trigger_retrain(self) -> bool:
        """Trigger retraining process."""
        if not self.should_retrain():
            self.logger.info("Retraining conditions not met")
            return False

        try:
            # Generate labels
            label_gen = LabelGenerator()
            labels_path = label_gen.generate_labels()

            if labels_path is None:
                return False

            # Trigger training (would call training script)
            self.logger.info("Retraining triggered")
            # In production, this would trigger the training flow
            # await run_training_flow(labels_path)

            return True

        except Exception as e:
            self.logger.error(f"Error triggering retrain: {e}")
            return False


class FeedbackService:
    """Main feedback service."""

    def __init__(self):
        self.logger = logger.bind(service="feedback")
        self.collector = FeedbackCollector()
        self.label_gen = LabelGenerator()
        self.retrain_trigger = RetrainingTrigger()

    def submit_feedback(self, **kwargs) -> Dict[str, Any]:
        """Submit feedback and check for retraining."""
        # Record feedback
        filepath = self.collector.record_feedback(**kwargs)

        # Check if retraining needed
        should_retrain = self.retrain_trigger.should_retrain()

        return {
            "feedback_saved": str(filepath),
            "should_retrain": should_retrain,
        }

    async def process_feedback_batch(self) -> Dict[str, Any]:
        """Process accumulated feedback and potentially retrain."""
        # Generate labels
        labels_path = self.label_gen.generate_labels()

        # Trigger retraining if needed
        retrained = await self.retrain_trigger.trigger_retrain()

        return {
            "labels_generated": str(labels_path) if labels_path else None,
            "retrained": retrained,
        }


# Singleton
_feedback_service: Optional[FeedbackService] = None


def get_feedback_service() -> FeedbackService:
    """Get or create feedback service instance."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
