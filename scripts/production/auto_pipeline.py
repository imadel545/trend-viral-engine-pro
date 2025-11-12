#!/usr/bin/env python3
"""
Production Pipeline - Collecte + Features + Training Automatique
Système autonome pour prédiction virale professionnelle.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import settings
from src.services.features import get_feature_service
from src.services.ingestion import get_ingestion_service
from src.services.scoring.advanced_ensemble import EnsembleVotingModel


class ProductionPipeline:
    """Pipeline complet de production."""
    
    def __init__(self):
        self.logger = logger.bind(pipeline="production")
        self.ingestion = get_ingestion_service()
        self.features = get_feature_service()
        
    async def collect_data(self, min_samples: int = 1000) -> Path:
        """Collecte Reddit jusqu'à avoir min_samples."""
        self.logger.info(f"🔥 COLLECTE: objectif {min_samples} posts")
        
        all_data = []
        batch_size = 200
        
        while len(all_data) < min_samples:
            # Collecte par batch
            results = await self.ingestion.run_collection(sources=['reddit'])
            reddit_file = results.get('reddit')
            
            if reddit_file and reddit_file.exists():
                df = pd.read_parquet(reddit_file)
                all_data.append(df)
                self.logger.info(f"   Batch: +{len(df)} posts (total: {sum(len(d) for d in all_data)})")
            
            await asyncio.sleep(2)  # Pause entre batches
        
        # Fusionner
        df_all = pd.concat(all_data, ignore_index=True)
        df_all = df_all.drop_duplicates(subset=['post_id'] if 'post_id' in df_all.columns else None)
        
        # Créer labels (top 20% = viral)
        if 'score' in df_all.columns:
            threshold = df_all['score'].quantile(0.80)
            df_all['is_breakout'] = (df_all['score'] > threshold).astype(int)
            
            viral_count = df_all['is_breakout'].sum()
            self.logger.success(f"✅ Collecté: {len(df_all)} posts ({viral_count} viraux)")
        
        # Sauvegarder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = Path('data/raw') / f'reddit_production_{timestamp}.parquet'
        df_all.to_parquet(output)
        
        return output
    
    def generate_features(self, raw_file: Path) -> Path:
        """Génère features avancées."""
        self.logger.info(f"🔧 FEATURES: {raw_file.name}")
        
        features_file = self.features.process_raw_data(raw_file)
        
        df = pd.read_parquet(features_file)
        self.logger.success(f"✅ Features: {df.shape}")
        
        return features_file
    
    def train_model(self, features_file: Path) -> dict:
        """Train ensemble model."""
        self.logger.info(f"🤖 TRAINING: {features_file.name}")
        
        # Load data
        df = pd.read_parquet(features_file)
        
        # Prepare features
        y = df['is_breakout'] if 'is_breakout' in df.columns else df['label']
        numeric_cols = df.select_dtypes(include=['int', 'float']).columns.tolist()
        for label_col in ['is_breakout', 'label']:
            if label_col in numeric_cols:
                numeric_cols.remove(label_col)
        
        X = df[numeric_cols]
        
        # Train
        model = EnsembleVotingModel()
        metrics = model.train(X, y, test_size=0.2)
        
        # Save
        model_path = Path('models/production_model.pkl')
        model.save(model_path)
        
        self.logger.success(f"✅ Model AUC: {metrics['ensemble']['auc']:.4f}")
        
        return metrics
    
    async def run_full_pipeline(self, min_samples: int = 1000):
        """Exécute pipeline complet."""
        self.logger.info("="*70)
        self.logger.info("🚀 PRODUCTION PIPELINE START")
        self.logger.info("="*70)
        
        try:
            # 1. Collecte
            raw_file = await self.collect_data(min_samples)
            
            # 2. Features
            features_file = self.generate_features(raw_file)
            
            # 3. Training
            metrics = self.train_model(features_file)
            
            # 4. Summary
            self.logger.info("="*70)
            self.logger.success("✅ PIPELINE COMPLETE")
            self.logger.info("="*70)
            self.logger.info(f"   Model AUC: {metrics['ensemble']['auc']:.4f}")
            self.logger.info(f"   Accuracy: {metrics['ensemble']['accuracy']:.4f}")
            self.logger.info(f"   Precision: {metrics['ensemble']['precision']:.4f}")
            self.logger.info(f"   Recall: {metrics['ensemble']['recall']:.4f}")
            self.logger.info("="*70)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise


async def main():
    """Entry point."""
    pipeline = ProductionPipeline()
    
    # Lancer pipeline (objectif: 2000+ samples)
    await pipeline.run_full_pipeline(min_samples=2000)


if __name__ == "__main__":
    asyncio.run(main())
