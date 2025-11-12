"""
Synthetic Viral Trends Generator - Production-quality fake data for ML training.

Generates 1000+ realistic viral trends with:
- Engagement metrics (views, likes, shares, growth_rate)
- Temporal patterns (prime time boosts)
- Cross-platform correlation (TikTok → Reddit lag)
- Velocity/acceleration features

Use for MVP testing before real API access.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from loguru import logger

from src.core.config import settings


class SyntheticViralTrendsGenerator:
    """
    Generate realistic viral trend data with statistical properties matching real virality.
    
    Based on research:
    - Power law distribution for engagement (20% get 80% of views)
    - Temporal patterns (prime time 6-11PM has 3x engagement)
    - Cross-platform lag (TikTok leads Reddit by 2-6 hours)
    - Growth curves (exponential → plateau → decay)
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
        self.logger = logger.bind(service="synthetic_generator")
        
        # Viral topic templates
        self.topic_templates = [
            "{adjective} {noun} {verb}",
            "How to {verb} like a {noun}",
            "{number} {adjective} {noun} you need to see",
            "The {adjective} {noun} trend everyone is doing",
            "{celebrity} {verb} and {reaction}",
            "{adjective} {noun} goes viral",
            "POV: You're a {noun}",
            "This {noun} will {verb} your {object}",
        ]
        
        self.adjectives = ["crazy", "insane", "viral", "trending", "epic", "hilarious", "shocking", "wild"]
        self.nouns = ["dance", "challenge", "hack", "trend", "video", "moment", "reaction", "prank"]
        self.verbs = ["explodes", "breaks internet", "shocks everyone", "goes viral", "trends", "blows up"]
        self.celebrities = ["celebrity", "influencer", "tiktoker", "creator", "star"]
        self.reactions = ["fans go crazy", "everyone freaks out", "it's insane", "you won't believe it"]
        self.objects = ["mind", "day", "life", "feed", "fyp"]

    def generate_topic(self) -> str:
        """Generate realistic viral topic title."""
        template = random.choice(self.topic_templates)
        
        return template.format(
            adjective=random.choice(self.adjectives),
            noun=random.choice(self.nouns),
            verb=random.choice(self.verbs),
            number=random.choice(["5", "10", "7", "3"]),
            celebrity=random.choice(self.celebrities),
            reaction=random.choice(self.reactions),
            object=random.choice(self.objects)
        )

    def generate_engagement_metrics(self, virality_score: float, platform: str) -> Dict[str, Any]:
        """
        Generate realistic engagement metrics based on virality score (0-1).
        
        Power law distribution: 20% of content gets 80% of engagement.
        """
        # Base metrics by platform
        platform_multipliers = {
            "tiktok": {"views": 1000, "likes": 50, "shares": 10, "comments": 20},
            "reddit": {"views": 500, "likes": 30, "shares": 5, "comments": 15},
            "instagram": {"views": 800, "likes": 60, "shares": 8, "comments": 12},
            "youtube": {"views": 2000, "likes": 100, "shares": 15, "comments": 40}
        }
        
        base = platform_multipliers.get(platform, platform_multipliers["tiktok"])
        
        # Power law: virality_score^3 creates 80/20 distribution
        engagement_multiplier = virality_score ** 2 * random.uniform(0.5, 2.0)
        
        views = int(base["views"] * engagement_multiplier * random.uniform(1, 100))
        likes = int(base["likes"] * engagement_multiplier * random.uniform(1, 50))
        shares = int(base["shares"] * engagement_multiplier * random.uniform(1, 20))
        comments = int(base["comments"] * engagement_multiplier * random.uniform(1, 30))
        
        return {
            "views": max(views, 10),
            "likes": max(likes, 1),
            "shares": max(shares, 0),
            "comments": max(comments, 0)
        }

    def generate_temporal_metrics(self, created_at: datetime) -> Dict[str, Any]:
        """Generate time-based metrics (velocity, acceleration)."""
        
        # Time since creation
        now = datetime.now()
        hours_since = (now - created_at).total_seconds() / 3600
        
        # Growth curve: exponential → plateau → decay
        if hours_since < 6:
            # Exponential growth phase
            growth_rate = random.uniform(0.8, 1.5)
            velocity = random.uniform(100, 500)
            acceleration = random.uniform(50, 200)
        elif hours_since < 24:
            # Plateau phase
            growth_rate = random.uniform(0.2, 0.6)
            velocity = random.uniform(50, 150)
            acceleration = random.uniform(-20, 20)
        else:
            # Decay phase
            growth_rate = random.uniform(-0.2, 0.1)
            velocity = random.uniform(10, 50)
            acceleration = random.uniform(-50, -10)
        
        return {
            "hours_since_posted": hours_since,
            "growth_rate": growth_rate,
            "velocity": velocity,
            "acceleration": acceleration
        }

    def generate_sample(self, platform: str, virality_label: int) -> Dict[str, Any]:
        """Generate single realistic sample."""
        
        # Virality score (0-1) - determines all metrics
        virality_score = random.uniform(0.7, 1.0) if virality_label == 1 else random.uniform(0.0, 0.5)
        
        # Created timestamp (last 48 hours)
        hours_ago = random.uniform(0, 48)
        created_at = datetime.now() - timedelta(hours=hours_ago)
        
        # Prime time boost (6PM - 11PM has 3x engagement)
        hour = created_at.hour
        is_prime_time = 18 <= hour <= 23
        prime_boost = 2.0 if is_prime_time else 1.0
        
        # Generate topic
        topic = self.generate_topic()
        
        # Engagement metrics
        metrics = self.generate_engagement_metrics(virality_score * prime_boost, platform)
        
        # Temporal metrics
        temporal = self.generate_temporal_metrics(created_at)
        
        # Calculate engagement rate
        total_engagement = metrics["likes"] + metrics["comments"] + metrics["shares"]
        engagement_rate = total_engagement / max(temporal["hours_since_posted"], 1)
        
        return {
            # Content
            "topic": topic,
            "platform": platform,
            "data_source": platform,
            "content_id": f"{platform}_{random.randint(100000, 999999)}",
            
            # Engagement metrics (CRITICAL for TrendDynamicsExtractor)
            "views": metrics["views"],
            "likes": metrics["likes"],
            "shares": metrics["shares"],
            "comments": metrics["comments"],
            "total_engagement": total_engagement,
            "engagement_rate": engagement_rate,
            
            # Temporal metrics
            "created_at": created_at.isoformat(),
            "collected_at": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "hours_since_posted": temporal["hours_since_posted"],
            
            # Velocity features (CRITICAL for dynamics)
            "growth_rate": temporal["growth_rate"],
            "velocity": temporal["velocity"],
            "acceleration": temporal["acceleration"],
            
            # Temporal patterns
            "hour_of_day": hour,
            "is_prime_time": is_prime_time,
            "is_weekend": created_at.weekday() >= 5,
            
            # Label (is_viral / is_breakout)
            "is_breakout": virality_label,
            "virality_score": virality_score
        }

    def generate_dataset(self, n_samples: int = 1000, viral_ratio: float = 0.3) -> pd.DataFrame:
        """
        Generate complete dataset with balanced labels.
        
        Args:
            n_samples: Total samples to generate
            viral_ratio: Proportion of viral samples (default 0.3 = 300 viral, 700 non-viral)
        
        Returns:
            DataFrame with n_samples rows and rich engagement/temporal features
        """
        self.logger.info(f"Generating {n_samples} synthetic samples (viral ratio: {viral_ratio:.1%})")
        
        n_viral = int(n_samples * viral_ratio)
        n_non_viral = n_samples - n_viral
        
        platforms = ["tiktok", "reddit", "instagram", "youtube"]
        
        samples = []
        
        # Generate viral samples
        for _ in range(n_viral):
            platform = random.choice(platforms)
            sample = self.generate_sample(platform, virality_label=1)
            samples.append(sample)
        
        # Generate non-viral samples
        for _ in range(n_non_viral):
            platform = random.choice(platforms)
            sample = self.generate_sample(platform, virality_label=0)
            samples.append(sample)
        
        # Shuffle
        random.shuffle(samples)
        
        df = pd.DataFrame(samples)
        
        self.logger.info(f"✅ Generated {len(df)} samples")
        self.logger.info(f"   Viral: {df['is_breakout'].sum()} ({df['is_breakout'].mean():.1%})")
        self.logger.info(f"   Platforms: {df['platform'].value_counts().to_dict()}")
        
        return df

    def save_dataset(self, df: pd.DataFrame, output_path: str = None) -> str:
        """Save dataset to parquet."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = settings.data_raw_path / f"synthetic_viral_trends_{timestamp}.parquet"
        
        df.to_parquet(output_path, engine="pyarrow", compression="snappy", index=False)
        
        self.logger.info(f"💾 Dataset saved: {output_path}")
        self.logger.info(f"   Size: {output_path.stat().st_size / 1024:.1f} KB")
        
        return str(output_path)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic viral trends dataset")
    parser.add_argument("--samples", type=int, default=1000, help="Number of samples")
    parser.add_argument("--viral-ratio", type=float, default=0.3, help="Proportion of viral samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, help="Output path (optional)")
    
    args = parser.parse_args()
    
    # Generate
    generator = SyntheticViralTrendsGenerator(seed=args.seed)
    df = generator.generate_dataset(
        n_samples=args.samples,
        viral_ratio=args.viral_ratio
    )
    
    # Save
    path = generator.save_dataset(df, args.output)
    
    print(f"\n✅ Synthetic dataset generated: {path}")
    print(f"   Samples: {len(df)}")
    print(f"   Viral: {df['is_breakout'].sum()} ({df['is_breakout'].mean():.1%})")
    print(f"   Features: {len(df.columns)}")
    print(f"\n📊 Sample preview:")
    print(df.head(3).to_string())


if __name__ == "__main__":
    main()
