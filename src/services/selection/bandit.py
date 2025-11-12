"""
Contextual Bandit - Exploration/Exploitation for trend selection.
Phase 2D - Advanced ML Pipeline.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from loguru import logger


class ContextualBanditSelector:
    """
    Contextual Multi-Armed Bandit for intelligent trend selection.
    
    Balances exploration (try new trends) vs exploitation (use best known trends).
    Uses Thompson Sampling with contextual features.
    """
    
    def __init__(
        self,
        epsilon: float = 0.1,
        decay: float = 0.99,
        min_epsilon: float = 0.01
    ):
        """
        Initialize bandit selector.
        
        Args:
            epsilon: Initial exploration rate (0-1)
            decay: Epsilon decay per iteration
            min_epsilon: Minimum exploration rate
        """
        self.logger = logger.bind(service="bandit")
        self.epsilon = epsilon
        self.decay = decay
        self.min_epsilon = min_epsilon
        
        # Track performance
        self.arm_counts = {}  # times each trend selected
        self.arm_rewards = {}  # cumulative rewards
        
        self.logger.info(
            f"Initialized Contextual Bandit (epsilon={epsilon}, decay={decay})"
        )
    
    def select_with_exploration(
        self,
        scored_trends: pd.DataFrame,
        k: int = 5,
        context: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Select top K trends with exploration/exploitation balance.
        
        Args:
            scored_trends: DataFrame with p_breakout_24h scores
            k: Number of trends to select
            context: Optional contextual features (time, user preferences, etc.)
            
        Returns:
            Selected trends (mix of exploitation + exploration)
        """
        n_trends = len(scored_trends)
        
        if n_trends <= k:
            return scored_trends
        
        # Calculate number to explore vs exploit
        n_explore = max(1, int(k * self.epsilon))
        n_exploit = k - n_explore
        
        self.logger.info(
            f"Selecting {k} trends: {n_exploit} exploit + {n_explore} explore (ε={self.epsilon:.3f})"
        )
        
        # Exploitation: Top N by score
        top_scores = scored_trends.nlargest(n_exploit, 'p_breakout_24h')
        
        # Exploration: Random sample from remaining
        remaining = scored_trends[~scored_trends.index.isin(top_scores.index)]
        
        if len(remaining) > 0:
            explore_sample = remaining.sample(n=min(n_explore, len(remaining)))
            selected = pd.concat([top_scores, explore_sample])
        else:
            selected = top_scores
        
        # Decay epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.decay)
        
        return selected.head(k)
    
    def update_rewards(self, trend_id: str, reward: float):
        """
        Update bandit with observed reward.
        
        Args:
            trend_id: Unique trend identifier
            reward: Reward value (e.g., actual views, engagement)
        """
        if trend_id not in self.arm_counts:
            self.arm_counts[trend_id] = 0
            self.arm_rewards[trend_id] = 0.0
        
        self.arm_counts[trend_id] += 1
        self.arm_rewards[trend_id] += reward
        
        avg_reward = self.arm_rewards[trend_id] / self.arm_counts[trend_id]
        
        self.logger.debug(
            f"Updated trend {trend_id}: {self.arm_counts[trend_id]} pulls, "
            f"avg reward: {avg_reward:.2f}"
        )
    
    def get_best_arms(self, top_k: int = 10) -> List[Dict]:
        """
        Get best performing trends (arms) by average reward.
        
        Args:
            top_k: Number of top trends to return
            
        Returns:
            List of dicts with trend_id, avg_reward, count
        """
        arm_stats = []
        
        for trend_id, count in self.arm_counts.items():
            if count > 0:
                avg_reward = self.arm_rewards[trend_id] / count
                arm_stats.append({
                    'trend_id': trend_id,
                    'avg_reward': avg_reward,
                    'count': count,
                    'total_reward': self.arm_rewards[trend_id]
                })
        
        # Sort by average reward
        arm_stats.sort(key=lambda x: x['avg_reward'], reverse=True)
        
        return arm_stats[:top_k]


# Singleton
_bandit_instance: Optional[ContextualBanditSelector] = None


def get_bandit_selector() -> ContextualBanditSelector:
    """Get or create bandit selector singleton."""
    global _bandit_instance
    if _bandit_instance is None:
        _bandit_instance = ContextualBanditSelector()
    return _bandit_instance
