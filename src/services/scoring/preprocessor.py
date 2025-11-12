"""
Feature Preprocessing for Scoring Service.

Handles dtype filtering and feature alignment between training and inference.
Critical for resolving dtypes error (P2) and training/inference mismatch (P1).
"""

from typing import List, Optional

import pandas as pd
from loguru import logger


class FeaturePreprocessor:
    """
    Preprocess features before scoring to ensure compatibility with ML models.
    
    Key responsibilities:
    1. Filter non-numeric columns (object, datetime)
    2. Ensure feature alignment with training data
    3. Handle missing features gracefully
    """
    
    def __init__(self, allowed_prefixes: Optional[List[str]] = None):
        """
        Initialize preprocessor.
        
        Args:
            allowed_prefixes: List of allowed column prefixes (e.g., ['emb_', 'temporal_'])
                            If None, defaults to embeddings and temporal features
        """
        self.logger = logger.bind(service="preprocessor")
        self.allowed_prefixes = allowed_prefixes or ["emb_", "temporal_"]
    
    def filter_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter to keep only numeric columns with allowed prefixes.
        
        This solves P2 (dtypes error) by removing object/datetime columns
        before passing to LightGBM.predict_proba().
        
        Args:
            df: Input DataFrame with mixed column types
            
        Returns:
            DataFrame with only numeric feature columns
        """
        # Get all numeric columns
        numeric_cols = df.select_dtypes(include=["int", "float", "bool"]).columns.tolist()
        
        # Filter by allowed prefixes
        feature_cols = [
            col for col in numeric_cols 
            if any(col.startswith(prefix) for prefix in self.allowed_prefixes)
        ]
        
        # Log filtering stats
        filtered_out = len(df.columns) - len(feature_cols)
        self.logger.info(
            f"Filtered {len(feature_cols)}/{len(df.columns)} columns "
            f"({filtered_out} removed: non-numeric or wrong prefix)"
        )
        
        if not feature_cols:
            self.logger.error("No feature columns found after filtering!")
            raise ValueError(
                f"No columns match prefixes {self.allowed_prefixes}. "
                f"Available: {df.columns.tolist()[:10]}"
            )
        
        return df[feature_cols]
    
    def align_with_training(
        self, 
        df: pd.DataFrame, 
        training_columns: List[str],
        fill_missing: float = 0.0
    ) -> pd.DataFrame:
        """
        Align inference features with training features.
        
        Ensures exact column match (order and names) with training data.
        Adds missing columns with fill_missing value, removes extra columns.
        
        Args:
            df: Input DataFrame
            training_columns: List of column names from training
            fill_missing: Value to fill for missing columns
            
        Returns:
            DataFrame aligned with training columns
        """
        current_cols = set(df.columns)
        training_cols = set(training_columns)
        
        # Find missing and extra columns
        missing_cols = training_cols - current_cols
        extra_cols = current_cols - training_cols
        
        if missing_cols:
            self.logger.warning(f"Adding {len(missing_cols)} missing columns with {fill_missing}")
            for col in missing_cols:
                df[col] = fill_missing
        
        if extra_cols:
            self.logger.info(f"Removing {len(extra_cols)} extra columns")
        
        # Return in exact training order
        return df[training_columns]
    
    def validate_features(self, df: pd.DataFrame, expected_count: int = 387) -> bool:
        """
        Validate feature count and types.
        
        Args:
            df: DataFrame to validate
            expected_count: Expected number of features
            
        Returns:
            True if valid, False otherwise
        """
        if len(df.columns) != expected_count:
            self.logger.warning(
                f"Feature count mismatch: got {len(df.columns)}, expected {expected_count}"
            )
            return False
        
        # Check all columns are numeric
        non_numeric = df.select_dtypes(exclude=["int", "float", "bool"]).columns
        if len(non_numeric) > 0:
            self.logger.error(f"Found {len(non_numeric)} non-numeric columns: {list(non_numeric)[:5]}")
            return False
        
        self.logger.info(f"✓ Features validated: {len(df.columns)} numeric columns")
        return True
    
    def preprocess(
        self, 
        df: pd.DataFrame, 
        training_columns: Optional[List[str]] = None,
        validate: bool = True
    ) -> pd.DataFrame:
        """
        Full preprocessing pipeline.
        
        Args:
            df: Input DataFrame
            training_columns: Optional list of training columns for alignment
            validate: Whether to validate after preprocessing
            
        Returns:
            Preprocessed DataFrame ready for scoring
        """
        # Step 1: Filter numeric with allowed prefixes
        df_processed = self.filter_numeric(df)
        
        # Step 2: Align with training if columns provided
        if training_columns:
            df_processed = self.align_with_training(df_processed, training_columns)
        
        # Step 3: Validate
        if validate:
            is_valid = self.validate_features(df_processed, expected_count=len(df_processed.columns))
            if not is_valid:
                self.logger.warning("Validation failed, but continuing...")
        
        return df_processed


def get_preprocessor(allowed_prefixes: Optional[List[str]] = None) -> FeaturePreprocessor:
    """
    Factory function to get FeaturePreprocessor instance.
    
    Args:
        allowed_prefixes: List of allowed column prefixes
        
    Returns:
        FeaturePreprocessor instance
    """
    return FeaturePreprocessor(allowed_prefixes=allowed_prefixes)
