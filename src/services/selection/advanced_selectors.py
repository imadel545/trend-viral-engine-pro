"""
Advanced Selection Strategies - State-of-the-Art Selection Algorithms
Implémente DPP, Thompson Sampling, Contextual Bandits, et Multi-Objective Optimization.
"""

import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from scipy.spatial.distance import pdist, squareform
from scipy.stats import beta
from sklearn.metrics.pairwise import rbf_kernel, cosine_similarity

try:
    from sklearn.linear_model import Ridge
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available")


class DPPSelector:
    """Determinantal Point Process for diversity-aware selection."""
    
    def __init__(self, kernel_type: str = "rbf", gamma: float = 1.0):
        self.logger = logger.bind(selector="dpp")
        self.kernel_type = kernel_type
        self.gamma = gamma
        
    def _compute_kernel(self, X: np.ndarray, scores: np.ndarray) -> np.ndarray:
        """Compute quality-diversity kernel matrix."""
        # Similarity kernel
        if self.kernel_type == "rbf":
            K = rbf_kernel(X, gamma=self.gamma)
        elif self.kernel_type == "cosine":
            K = cosine_similarity(X)
        else:
            # Linear kernel
            K = X @ X.T
        
        # Incorporate quality scores
        # L = diag(q) * K * diag(q) where q is quality scores
        q = scores / scores.max()  # Normalize to [0,1]
        L = np.outer(q, q) * K
        
        return L
    
    def select(
        self,
        scored_df: pd.DataFrame,
        k: int,
        embedding_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Select diverse subset using DPP."""
        if len(scored_df) <= k:
            return scored_df
        
        # Extract embeddings
        if embedding_cols is None:
            # Try to find embedding columns
            embedding_cols = [c for c in scored_df.columns if c.startswith('text_emb_') or c.startswith('emb_')]
        
        if not embedding_cols or not all(c in scored_df.columns for c in embedding_cols):
            self.logger.warning("No embeddings found, using scores only")
            return scored_df.nlargest(k, "p_breakout_24h")
        
        # Get embeddings and scores
        X = scored_df[embedding_cols].values
        scores = scored_df["p_breakout_24h"].values
        
        # Compute kernel matrix
        L = self._compute_kernel(X, scores)
        
        # Greedy MAP inference for DPP
        selected_indices = []
        remaining_indices = list(range(len(scored_df)))
        
        # Initialize with highest score
        first_idx = np.argmax(scores)
        selected_indices.append(first_idx)
        remaining_indices.remove(first_idx)
        
        # Greedy selection
        for _ in range(k - 1):
            if not remaining_indices:
                break
            
            best_idx = None
            best_gain = -np.inf
            
            for idx in remaining_indices:
                # Compute marginal gain
                current_set = selected_indices + [idx]
                L_sub = L[np.ix_(current_set, current_set)]
                
                try:
                    gain = np.linalg.slogdet(L_sub)[1]  # Log determinant
                except:
                    gain = 0.0
                
                if gain > best_gain:
                    best_gain = gain
                    best_idx = idx
            
            if best_idx is not None:
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)
        
        result = scored_df.iloc[selected_indices]
        self.logger.info(f"DPP selected {len(result)} items with diversity")
        
        return result


class ThompsonSamplingSelector:
    """Thompson Sampling for exploration-exploitation."""
    
    def __init__(self, alpha_prior: float = 1.0, beta_prior: float = 1.0):
        self.logger = logger.bind(selector="thompson")
        self.alpha_prior = alpha_prior
        self.beta_prior = beta_prior
        
        # Store statistics for each topic
        self.topic_stats: Dict[str, Dict[str, int]] = {}
        
    def update(self, topic: str, success: bool) -> None:
        """Update statistics for a topic based on feedback."""
        if topic not in self.topic_stats:
            self.topic_stats[topic] = {"successes": 0, "failures": 0}
        
        if success:
            self.topic_stats[topic]["successes"] += 1
        else:
            self.topic_stats[topic]["failures"] += 1
    
    def select(self, scored_df: pd.DataFrame, k: int) -> pd.DataFrame:
        """Select using Thompson Sampling."""
        if len(scored_df) <= k:
            return scored_df
        
        scores = []
        
        for idx, row in scored_df.iterrows():
            topic = row.get("topic", "")
            base_score = row["p_breakout_24h"]
            
            # Get prior + observed statistics
            if topic in self.topic_stats:
                alpha = self.alpha_prior + self.topic_stats[topic]["successes"]
                beta_param = self.beta_prior + self.topic_stats[topic]["failures"]
            else:
                alpha = self.alpha_prior
                beta_param = self.beta_prior
            
            # Sample from Beta distribution
            thompson_score = beta.rvs(alpha, beta_param)
            
            # Combine with base score
            combined_score = 0.7 * base_score + 0.3 * thompson_score
            
            scores.append((idx, combined_score))
        
        # Select top K
        scores.sort(key=lambda x: x[1], reverse=True)
        selected_indices = [idx for idx, _ in scores[:k]]
        
        result = scored_df.loc[selected_indices]
        self.logger.info(f"Thompson Sampling selected {len(result)} items")
        
        return result


class LinUCBSelector:
    """Linear Upper Confidence Bound for contextual bandits."""
    
    def __init__(self, alpha: float = 1.0, dim: int = 10):
        self.logger = logger.bind(selector="linucb")
        self.alpha = alpha
        self.dim = dim
        
        # Model parameters
        self.A = np.identity(dim)  # Design matrix
        self.b = np.zeros(dim)     # Response vector
        self.theta = np.zeros(dim)  # Parameter estimate
        
    def update(self, context: np.ndarray, reward: float) -> None:
        """Update model with observed reward."""
        context = context.reshape(-1, 1)
        self.A += context @ context.T
        self.b += reward * context.flatten()
        
        try:
            self.theta = np.linalg.solve(self.A, self.b)
        except np.linalg.LinAlgError:
            self.theta = np.linalg.lstsq(self.A, self.b, rcond=None)[0]
    
    def select(
        self,
        scored_df: pd.DataFrame,
        k: int,
        context_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Select using LinUCB."""
        if len(scored_df) <= k:
            return scored_df
        
        # Extract context features
        if context_cols is None:
            context_cols = [c for c in scored_df.columns if c.startswith('text_emb_')][:self.dim]
        
        if not context_cols:
            self.logger.warning("No context features, falling back to greedy")
            return scored_df.nlargest(k, "p_breakout_24h")
        
        ucb_scores = []
        
        for idx, row in scored_df.iterrows():
            context = row[context_cols].values[:self.dim]
            
            # Pad if necessary
            if len(context) < self.dim:
                context = np.pad(context, (0, self.dim - len(context)))
            
            # Compute UCB
            expected_reward = self.theta @ context
            
            try:
                A_inv = np.linalg.inv(self.A)
                uncertainty = self.alpha * np.sqrt(context @ A_inv @ context)
            except:
                uncertainty = self.alpha
            
            ucb = expected_reward + uncertainty
            
            ucb_scores.append((idx, ucb))
        
        # Select top K by UCB
        ucb_scores.sort(key=lambda x: x[1], reverse=True)
        selected_indices = [idx for idx, _ in ucb_scores[:k]]
        
        result = scored_df.loc[selected_indices]
        self.logger.info(f"LinUCB selected {len(result)} items")
        
        return result


class MultiObjectiveSelector:
    """Multi-objective selection using Pareto frontier."""
    
    def __init__(
        self,
        objectives: List[str] = ["p_breakout_24h", "predicted_views_24h"],
        weights: Optional[List[float]] = None,
    ):
        self.logger = logger.bind(selector="multi_objective")
        self.objectives = objectives
        self.weights = weights or [1.0] * len(objectives)
        
    def _is_pareto_efficient(self, costs: np.ndarray) -> np.ndarray:
        """Find Pareto efficient points (maximize all objectives)."""
        is_efficient = np.ones(costs.shape[0], dtype=bool)
        
        for i, c in enumerate(costs):
            if is_efficient[i]:
                # Keep points that are not dominated
                is_efficient[is_efficient] = np.any(costs[is_efficient] >= c, axis=1)
                is_efficient[i] = True
        
        return is_efficient
    
    def select(self, scored_df: pd.DataFrame, k: int) -> pd.DataFrame:
        """Select using Pareto frontier."""
        if len(scored_df) <= k:
            return scored_df
        
        # Check objectives exist
        missing = [obj for obj in self.objectives if obj not in scored_df.columns]
        if missing:
            self.logger.warning(f"Missing objectives: {missing}, using p_breakout_24h only")
            return scored_df.nlargest(k, "p_breakout_24h")
        
        # Extract objective values (negate for minimization)
        objective_values = scored_df[self.objectives].values
        
        # Find Pareto frontier
        is_efficient = self._is_pareto_efficient(objective_values)
        pareto_df = scored_df[is_efficient].copy()
        
        self.logger.info(f"Found {len(pareto_df)} Pareto-efficient points")
        
        # If Pareto set is smaller than k, add next best by weighted score
        if len(pareto_df) < k:
            remaining = scored_df[~is_efficient].copy()
            
            # Compute weighted score
            weighted_scores = np.zeros(len(remaining))
            for i, (obj, weight) in enumerate(zip(self.objectives, self.weights)):
                # Normalize to [0,1]
                obj_vals = remaining[obj].values
                obj_min, obj_max = obj_vals.min(), obj_vals.max()
                if obj_max > obj_min:
                    norm_vals = (obj_vals - obj_min) / (obj_max - obj_min)
                else:
                    norm_vals = np.ones_like(obj_vals)
                
                weighted_scores += weight * norm_vals
            
            remaining['weighted_score'] = weighted_scores
            top_remaining = remaining.nlargest(k - len(pareto_df), 'weighted_score')
            
            result = pd.concat([pareto_df, top_remaining.drop(columns=['weighted_score'])])
        elif len(pareto_df) > k:
            # Too many Pareto points, select by weighted score
            weighted_scores = np.zeros(len(pareto_df))
            for i, (obj, weight) in enumerate(zip(self.objectives, self.weights)):
                obj_vals = pareto_df[obj].values
                obj_min, obj_max = obj_vals.min(), obj_vals.max()
                if obj_max > obj_min:
                    norm_vals = (obj_vals - obj_min) / (obj_max - obj_min)
                else:
                    norm_vals = np.ones_like(obj_vals)
                
                weighted_scores += weight * norm_vals
            
            pareto_df['weighted_score'] = weighted_scores
            result = pareto_df.nlargest(k, 'weighted_score').drop(columns=['weighted_score'])
        else:
            result = pareto_df
        
        self.logger.info(f"Multi-objective selected {len(result)} items")
        
        return result


class HybridSelector:
    """Hybrid selector combining multiple strategies."""
    
    def __init__(
        self,
        use_dpp: bool = True,
        use_thompson: bool = True,
        use_linucb: bool = False,
        use_multi_objective: bool = True,
        strategy_weights: Optional[Dict[str, float]] = None,
    ):
        self.logger = logger.bind(selector="hybrid")
        
        self.selectors = {}
        
        if use_dpp:
            self.selectors['dpp'] = DPPSelector()
        
        if use_thompson:
            self.selectors['thompson'] = ThompsonSamplingSelector()
        
        if use_linucb:
            self.selectors['linucb'] = LinUCBSelector()
        
        if use_multi_objective:
            self.selectors['multi_objective'] = MultiObjectiveSelector()
        
        # Default equal weights
        self.strategy_weights = strategy_weights or {
            name: 1.0 / len(self.selectors) for name in self.selectors
        }
        
    def select(
        self,
        scored_df: pd.DataFrame,
        k: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Select using hybrid approach."""
        if len(scored_df) <= k:
            return scored_df
        
        context = context or {}
        
        # Get selections from each strategy
        all_selections = {}
        
        for name, selector in self.selectors.items():
            try:
                if name == 'dpp':
                    selection = selector.select(scored_df, k)
                elif name == 'thompson':
                    selection = selector.select(scored_df, k)
                elif name == 'linucb':
                    selection = selector.select(scored_df, k)
                elif name == 'multi_objective':
                    selection = selector.select(scored_df, k)
                else:
                    continue
                
                all_selections[name] = set(selection.index)
                
            except Exception as e:
                self.logger.warning(f"Strategy {name} failed: {e}")
        
        if not all_selections:
            self.logger.warning("All strategies failed, using greedy")
            return scored_df.nlargest(k, "p_breakout_24h")
        
        # Aggregate selections with voting
        vote_counts = {}
        
        for name, indices in all_selections.items():
            weight = self.strategy_weights.get(name, 1.0)
            for idx in indices:
                vote_counts[idx] = vote_counts.get(idx, 0) + weight
        
        # Select top K by vote count
        sorted_indices = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
        selected_indices = [idx for idx, _ in sorted_indices[:k]]
        
        result = scored_df.loc[selected_indices]
        
        self.logger.info(f"Hybrid selector selected {len(result)} items using {len(all_selections)} strategies")
        
        return result
    
    def update_feedback(self, topic: str, success: bool, context: Optional[np.ndarray] = None, reward: Optional[float] = None) -> None:
        """Update strategies with feedback."""
        if 'thompson' in self.selectors:
            self.selectors['thompson'].update(topic, success)
        
        if 'linucb' in self.selectors and context is not None and reward is not None:
            self.selectors['linucb'].update(context, reward)
