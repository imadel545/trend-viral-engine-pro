#!/usr/bin/env python3
"""
PRODUCTION PIPELINE - Solution Professionnelle Sans Triche
Prédiction virale RÉELLE avec données de qualité et validation rigoureuse.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)
from sklearn.model_selection import StratifiedKFold

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.features import get_feature_service
from src.services.ingestion import get_ingestion_service
from src.services.scoring.advanced_ensemble import EnsembleVotingModel


class ProductionPipeline:
    """Pipeline production sans triche - Qualité > Quantité."""
    
    def __init__(self):
        self.logger = logger.bind(pipeline="production")
        
    async def collect_massive_data(self, target_samples: int = 3000) -> Path:
        """Collecte MASSIVE de données Reddit réelles."""
        self.logger.info(f"🔥 COLLECTE MASSIVE: objectif {target_samples} posts RÉELS")
        
        ingestion = get_ingestion_service()
        all_data = []
        
        while len(all_data) < target_samples:
            try:
                # Collection SEULEMENT Reddit (skip Google Trends qui bloque)
                try:
                    results = await ingestion.run_collection(sources=['reddit'])
                    reddit_file = results.get('reddit')
                except Exception as collect_error:
                    # Si erreur Google Trends, continue quand même
                    self.logger.warning(f"Collection error (ignoré): {collect_error}")
                    # Check si fichier Reddit créé malgré l'erreur
                    recent_files = sorted(Path("data/raw").glob("reddit_*.parquet"), 
                                        key=lambda x: x.stat().st_mtime)
                    reddit_file = recent_files[-1] if recent_files else None
                
                if reddit_file and reddit_file.exists():
                    df = pd.read_parquet(reddit_file)
                    all_data.append(df)
                    
                    total = sum(len(d) for d in all_data)
                    self.logger.info(f"   Batch: +{len(df)} posts | Total: {total}/{target_samples}")
                
                await asyncio.sleep(5)  # Pause entre batches
                
            except Exception as e:
                self.logger.warning(f"Batch failed: {e}")
                await asyncio.sleep(10)
        
        # Fusionner et dédupliquer
        df_all = pd.concat(all_data, ignore_index=True)
        df_all = df_all.drop_duplicates(subset=['post_id'] if 'post_id' in df_all.columns else None)
        
        # Labels intelligents (top 15% = viral pour être plus strict)
        if 'score' in df_all.columns:
            threshold = df_all['score'].quantile(0.85)
            df_all['is_breakout'] = (df_all['score'] > threshold).astype(int)
            
            viral_count = df_all['is_breakout'].sum()
            viral_score_avg = df_all[df_all['is_breakout']==1]['score'].mean()
            
            self.logger.success(f"✅ Collecté: {len(df_all)} posts")
            self.logger.success(f"   Viraux: {viral_count} ({100*viral_count/len(df_all):.1f}%)")
            self.logger.success(f"   Score viral moyen: {viral_score_avg:.0f}")
        
        # Sauvegarder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = Path(f'data/raw/reddit_massive_{timestamp}.parquet')
        df_all.to_parquet(output)
        
        return output
    
    def validate_data_quality(self, features_file: Path) -> Dict[str, float]:
        """Validation STRICTE de qualité des données."""
        self.logger.info("🔍 VALIDATION QUALITÉ DES DONNÉES")
        
        df = pd.read_parquet(features_file)
        
        # Métriques qualité
        numeric_cols = df.select_dtypes(include=['int', 'float']).columns
        numeric_cols = [c for c in numeric_cols if c not in ['is_breakout', 'label']]
        
        # 1. Variance
        variances = df[numeric_cols].var()
        low_var_pct = (variances < 0.01).sum() / len(numeric_cols) * 100
        
        # 2. Missing values
        missing_pct = df[numeric_cols].isnull().sum().sum() / (len(df) * len(numeric_cols)) * 100
        
        # 3. Duplicates
        dup_pct = df.duplicated().sum() / len(df) * 100
        
        # 4. Label distribution
        label_col = 'is_breakout' if 'is_breakout' in df.columns else 'label'
        label_dist = df[label_col].value_counts(normalize=True).to_dict()
        
        # 5. Correlations suspicieuses
        if label_col in df.columns:
            corrs = []
            for col in numeric_cols:
                try:
                    corr = abs(df[col].corr(df[label_col]))
                    if corr > 0.95:  # Leakage potentiel
                        corrs.append((col, corr))
                except:
                    pass
        
        quality = {
            'samples': len(df),
            'features': len(numeric_cols),
            'low_variance_pct': low_var_pct,
            'missing_pct': missing_pct,
            'duplicate_pct': dup_pct,
            'label_balance': label_dist,
            'suspicious_features': len(corrs)
        }
        
        # Affichage
        self.logger.info("="*70)
        self.logger.info(f"   Samples: {quality['samples']}")
        self.logger.info(f"   Features: {quality['features']}")
        self.logger.info(f"   Low variance: {quality['low_variance_pct']:.1f}%")
        self.logger.info(f"   Missing: {quality['missing_pct']:.2f}%")
        self.logger.info(f"   Duplicates: {quality['duplicate_pct']:.2f}%")
        self.logger.info(f"   Label balance: {quality['label_balance']}")
        self.logger.info(f"   Suspicious: {quality['suspicious_features']} features")
        
        # Warnings
        if quality['low_variance_pct'] > 10:
            self.logger.warning(f"⚠️  Trop de features low-variance ({quality['low_variance_pct']:.1f}%)")
        
        if quality['suspicious_features'] > 0:
            self.logger.error(f"🔴 {quality['suspicious_features']} features avec correlation >0.95 (DATA LEAKAGE!)")
            for feat, corr in corrs:
                self.logger.error(f"    {feat}: {corr:.4f}")
        
        self.logger.info("="*70)
        
        return quality
    
    def train_with_cv(self, features_file: Path, n_folds: int = 5) -> Dict[str, float]:
        """Training avec Cross-Validation STRICTE (pas de triche)."""
        self.logger.info(f"🤖 TRAINING avec {n_folds}-Fold Cross-Validation")
        
        # Load data
        df = pd.read_parquet(features_file)
        
        # Prepare
        label_col = 'is_breakout' if 'is_breakout' in df.columns else 'label'
        y = df[label_col]
        
        numeric_cols = df.select_dtypes(include=['int', 'float']).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c not in ['is_breakout', 'label']]
        X = df[numeric_cols]
        
        # Remove low-variance features
        variances = X.var()
        good_features = variances[variances >= 0.01].index.tolist()
        X = X[good_features]
        
        self.logger.info(f"   Features: {len(good_features)} (removed {len(numeric_cols) - len(good_features)} low-var)")
        
        # Cross-validation
        cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
        
        cv_scores = {
            'auc': [],
            'accuracy': [],
            'precision': [],
            'recall': [],
            'f1': []
        }
        
        for fold, (train_idx, val_idx) in enumerate(cv.split(X, y)):
            self.logger.info(f"\n   Fold {fold+1}/{n_folds}")
            
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Train model
            model = EnsembleVotingModel()
            
            # IMPORTANT: class_weight pour gérer imbalance SANS SMOTE
            from sklearn.utils.class_weight import compute_class_weight
            classes = np.unique(y_train)
            weights = compute_class_weight('balanced', classes=classes, y=y_train)
            class_weights = dict(zip(classes, weights))
            
            metrics = model.train(
                X_train, y_train,
                test_size=0.2,
                class_weights=class_weights
            )
            
            # Predict on validation
            y_pred = model.predict(X_val)
            y_proba = model.predict_proba(X_val)
            
            # Metrics
            auc = roc_auc_score(y_val, y_proba)
            acc = accuracy_score(y_val, y_pred)
            prec = precision_score(y_val, y_pred, zero_division=0)
            rec = recall_score(y_val, y_pred, zero_division=0)
            f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
            
            cv_scores['auc'].append(auc)
            cv_scores['accuracy'].append(acc)
            cv_scores['precision'].append(prec)
            cv_scores['recall'].append(rec)
            cv_scores['f1'].append(f1)
            
            self.logger.info(f"      AUC: {auc:.4f}, Recall: {rec:.4f}, Precision: {prec:.4f}")
        
        # Moyenne et std
        final_metrics = {}
        for metric, scores in cv_scores.items():
            mean = np.mean(scores)
            std = np.std(scores)
            final_metrics[f'{metric}_mean'] = mean
            final_metrics[f'{metric}_std'] = std
            
            self.logger.success(f"   {metric.upper()}: {mean:.4f} ± {std:.4f}")
        
        # Train final model on ALL data
        self.logger.info("\n   Training FINAL model on all data...")
        final_model = EnsembleVotingModel()
        
        classes = np.unique(y)
        weights = compute_class_weight('balanced', classes=classes, y=y)
        class_weights = dict(zip(classes, weights))
        
        final_model.train(X, y, test_size=0.2, class_weights=class_weights)
        
        # Save
        model_path = Path('models/production_cv_model.pkl')
        final_model.save(model_path)
        self.logger.success(f"✅ Model saved: {model_path}")
        
        return final_metrics
    
    async def run(self):
        """Pipeline complet production."""
        self.logger.info("="*70)
        self.logger.info("🚀 PRODUCTION PIPELINE - QUALITÉ PROFESSIONNELLE")
        self.logger.info("="*70)
        
        try:
            # 1. Collecte massive
            raw_file = await self.collect_massive_data(target_samples=3000)
            
            # 2. Features
            self.logger.info("\n🔧 GÉNÉRATION FEATURES")
            features_service = get_feature_service()
            features_file = features_service.process_raw_data(raw_file)
            
            # 3. Validation qualité
            quality = self.validate_data_quality(features_file)
            
            if quality['suspicious_features'] > 0:
                self.logger.error("🔴 DATA LEAKAGE DÉTECTÉ! Arrêt du pipeline.")
                return
            
            # 4. Training avec CV
            metrics = self.train_with_cv(features_file, n_folds=5)
            
            # 5. Summary
            self.logger.info("\n" + "="*70)
            self.logger.success("✅ PIPELINE COMPLETE - MODÈLE PRODUCTION-READY")
            self.logger.info("="*70)
            self.logger.info(f"   AUC: {metrics['auc_mean']:.4f} ± {metrics['auc_std']:.4f}")
            self.logger.info(f"   Recall: {metrics['recall_mean']:.4f} ± {metrics['recall_std']:.4f}")
            self.logger.info(f"   Precision: {metrics['precision_mean']:.4f} ± {metrics['precision_std']:.4f}")
            self.logger.info(f"   F1: {metrics['f1_mean']:.4f} ± {metrics['f1_std']:.4f}")
            self.logger.info("="*70)
            
            # Validation finale
            if metrics['auc_mean'] < 0.65:
                self.logger.warning("⚠️  AUC faible - Besoin de plus de données ou features")
            elif metrics['auc_mean'] > 0.95:
                self.logger.error("🔴 AUC trop élevé - Possible overfitting!")
            else:
                self.logger.success("✅ Métriques réalistes - Modèle fiable")
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise


async def main():
    """Entry point."""
    pipeline = ProductionPipeline()
    await pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())
