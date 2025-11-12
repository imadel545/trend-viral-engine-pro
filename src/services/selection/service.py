"""
Selection Service - Select top K topics for content generation.
Implements diversity, exploration, and ranking strategies.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger

from src.core.config import settings


class SelectionStrategy:
    """Base selection strategy."""

    def select(self, scored_df: pd.DataFrame, k: int) -> pd.DataFrame:
        """Select top K items."""
        raise NotImplementedError


class TopKScoreStrategy(SelectionStrategy):
    """Select top K by score."""

    def select(self, scored_df: pd.DataFrame, k: int) -> pd.DataFrame:
        """Select top K highest scores."""
        return scored_df.nlargest(k, "p_breakout_24h")


class DiversityStrategy(SelectionStrategy):
    """Select with diversity consideration."""

    def __init__(self, diversity_weight: float = 0.3):
        self.diversity_weight = diversity_weight
        self.logger = logger.bind(strategy="diversity")

    def select(self, scored_df: pd.DataFrame, k: int) -> pd.DataFrame:
        """Select top K with diversity."""
        if len(scored_df) <= k:
            return scored_df

        selected_indices = []
        remaining_indices = list(scored_df.index)

        # Select highest score first
        first_idx = scored_df["p_breakout_24h"].idxmax()
        selected_indices.append(first_idx)
        remaining_indices.remove(first_idx)

        # Select remaining with diversity
        for _ in range(k - 1):
            if not remaining_indices:
                break

            scores = []
            for idx in remaining_indices:
                # Base score
                base_score = scored_df.loc[idx, "p_breakout_24h"]

                # Diversity bonus (simplified - would use embeddings in production)
                diversity_bonus = self._calculate_diversity(idx, selected_indices, scored_df)

                # Combined score
                combined = (1 - self.diversity_weight) * base_score + self.diversity_weight * diversity_bonus
                scores.append((idx, combined))

            # Select best
            best_idx = max(scores, key=lambda x: x[1])[0]
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)

        return scored_df.loc[selected_indices]

    def _calculate_diversity(
        self, candidate_idx: int, selected_indices: List[int], df: pd.DataFrame
    ) -> float:
        """Calculate diversity score using cosine similarity of embeddings.
        
        Returns a diversity score between 0 and 1, where:
        - 1.0 = maximally diverse (dissimilar to all selected items)
        - 0.0 = not diverse (very similar to selected items)
        """
        # Extract embedding columns (emb_0, emb_1, ..., emb_383)
        emb_cols = [col for col in df.columns if col.startswith('emb_') and col[4:].isdigit()]
        
        if not emb_cols:
            # Fallback to random if no embeddings available
            self.logger.warning("No embedding columns found, using random diversity")
            return np.random.random()
        
        # Get candidate embedding
        candidate_emb = df.loc[candidate_idx, emb_cols].values
        
        if len(selected_indices) == 0:
            # First item is maximally diverse
            return 1.0
        
        # Calculate cosine similarity with all selected items
        similarities = []
        for selected_idx in selected_indices:
            selected_emb = df.loc[selected_idx, emb_cols].values
            
            # Cosine similarity: dot(a, b) / (||a|| * ||b||)
            norm_candidate = np.linalg.norm(candidate_emb)
            norm_selected = np.linalg.norm(selected_emb)
            
            if norm_candidate > 0 and norm_selected > 0:
                similarity = np.dot(candidate_emb, selected_emb) / (norm_candidate * norm_selected)
                similarities.append(similarity)
        
        if not similarities:
            return 1.0
        
        # Diversity = 1 - max_similarity (most diverse = least similar to any selected)
        max_similarity = max(similarities)
        diversity = 1.0 - max_similarity
        
        # Ensure diversity is in [0, 1] range (cosine can be negative for opposite vectors)
        diversity = max(0.0, min(1.0, diversity))
        
        return diversity


class ExplorationStrategy(SelectionStrategy):
    """Epsilon-greedy exploration."""

    def __init__(self, epsilon: float = 0.1):
        self.epsilon = epsilon
        self.logger = logger.bind(strategy="exploration")

    def select(self, scored_df: pd.DataFrame, k: int) -> pd.DataFrame:
        """Select with exploration."""
        n_explore = int(k * self.epsilon)
        n_exploit = k - n_explore

        # Exploit: top scores
        exploit_df = scored_df.nlargest(n_exploit, "p_breakout_24h")

        # Explore: random from remaining
        remaining = scored_df.drop(exploit_df.index)
        if len(remaining) > 0:
            explore_df = remaining.sample(n=min(n_explore, len(remaining)))
        else:
            explore_df = pd.DataFrame()

        return pd.concat([exploit_df, explore_df])


class SelectionService:
    """Main selection service."""

    def __init__(self):
        self.logger = logger.bind(service="selection")
        self.strategies = {
            "topk": TopKScoreStrategy(),
            "diversity": DiversityStrategy(settings.diversity_weight),
            "exploration": ExplorationStrategy(settings.exploration_rate),
        }
        self.default_strategy = "diversity"

    def select_top_k(
        self,
        scored_df: pd.DataFrame,
        k: Optional[int] = None,
        strategy: Optional[str] = None,
        country: Optional[str] = None,
    ) -> pd.DataFrame:
        """Select top K topics for content generation."""
        k = k or settings.top_k_default
        strategy = strategy or self.default_strategy

        self.logger.info(f"Selecting top {k} using {strategy} strategy")

        # Filter by country if specified
        if country and "country" in scored_df.columns:
            scored_df = scored_df[scored_df["country"] == country]
            self.logger.info(f"Filtered to {len(scored_df)} items for country={country}")

        # Apply strategy
        if strategy not in self.strategies:
            self.logger.warning(f"Unknown strategy {strategy}, using default")
            strategy = self.default_strategy

        selected = self.strategies[strategy].select(scored_df, k)

        self.logger.info(f"Selected {len(selected)} topics")
        return selected

    def get_recommendations(
        self, scored_df: pd.DataFrame, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get recommendations with metadata."""
        context = context or {}
        k = context.get("k", settings.top_k_default)
        country = context.get("country")

        selected = self.select_top_k(scored_df, k=k, country=country)

        recommendations = []
        for idx, row in selected.iterrows():
            recommendations.append({
                "topic": row.get("topic", ""),
                "score": float(row["p_breakout_24h"]),
                "predicted_views": int(row["predicted_views_24h"]),
                "country": row.get("country", ""),
                "rank": len(recommendations) + 1,
            })

        return recommendations


# Singleton
_selection_service: Optional[SelectionService] = None


def get_selection_service() -> SelectionService:
    """Get or create selection service instance."""
    global _selection_service
    if _selection_service is None:
        _selection_service = SelectionService()
    return _selection_service
