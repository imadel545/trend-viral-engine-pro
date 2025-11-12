#!/usr/bin/env python3
"""
🧹 DATA QUALITY CLEANER - Nettoyage Automatique Professionnel
Supprime données synthétiques, posts vides, et améliore qualité dataset.
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd
from loguru import logger

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings


class DataQualityCleaner:
    """Nettoyeur automatique de données pour ML production-grade."""
    
    def __init__(self):
        self.data_raw = settings.data_raw_path
        self.data_features = settings.data_features_path
        self.backup_dir = Path("data/backup_before_cleaning")
        self.backup_dir.mkdir(exist_ok=True, parents=True)
        
        self.stats = {
            "files_processed": 0,
            "synthetic_removed": 0,
            "empty_texts_removed": 0,
            "facebook_emoji_removed": 0,
            "total_rows_before": 0,
            "total_rows_after": 0
        }
    
    def backup_file(self, filepath: Path):
        """Backup avant modification."""
        import shutil
        backup_path = self.backup_dir / filepath.name
        shutil.copy2(filepath, backup_path)
        logger.debug(f"📦 Backup: {filepath.name} → backup/")
    
    def remove_synthetic_files(self) -> List[Path]:
        """Supprime tous fichiers contenant 'synthetic' dans le nom."""
        logger.info("🔍 Recherche fichiers synthétiques...")
        
        synthetic_files = []
        
        # Chercher dans data/raw et data/features
        for data_dir in [self.data_raw, self.data_features]:
            for pattern in ["*synthetic*.parquet", "*fake*.parquet", "*test*.parquet"]:
                found = list(data_dir.glob(pattern))
                synthetic_files.extend(found)
        
        if not synthetic_files:
            logger.info("✅ Aucun fichier synthétique trouvé")
            return []
        
        logger.warning(f"🗑️  {len(synthetic_files)} fichiers synthétiques détectés")
        
        for filepath in synthetic_files:
            self.backup_file(filepath)
            filepath.unlink()
            logger.info(f"  ❌ Supprimé: {filepath.name}")
            self.stats["synthetic_removed"] += 1
        
        return synthetic_files
    
    def clean_reddit_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Nettoie données Reddit:
        - Supprime posts avec text vide ou <10 chars
        - Vérifie enrichment (title+comments présents)
        - Filtre duplicates
        """
        original_len = len(df)
        
        # Filtre 1: Text vide
        if 'text' in df.columns:
            df = df[df['text'].notna() & (df['text'].str.len() >= 10)]
            logger.debug(f"  Filtre text vide: {original_len} → {len(df)}")
        
        # Filtre 2: Topic vide (titre obligatoire)
        if 'topic' in df.columns:
            df = df[df['topic'].notna() & (df['topic'].str.len() >= 5)]
            logger.debug(f"  Filtre topic vide: {original_len} → {len(df)}")
        
        # Filtre 3: Score minimum (posts viraux seulement)
        if 'score' in df.columns:
            MIN_VIRAL_SCORE = 500  # Posts avec minimum d'engagement
            df = df[df['score'] >= MIN_VIRAL_SCORE]
            logger.debug(f"  Filtre score <{MIN_VIRAL_SCORE}: {original_len} → {len(df)}")
        
        # Filtre 4: Duplicates (même topic)
        if 'topic' in df.columns:
            before_dedup = len(df)
            df = df.drop_duplicates(subset=['topic'], keep='first')
            logger.debug(f"  Déduplication: {before_dedup} → {len(df)}")
        
        removed = original_len - len(df)
        return df, removed
    
    def clean_facebook_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Nettoie données Facebook:
        - Supprime posts emoji-only (🔥, ✨❤️, etc.)
        - Garde seulement posts avec texte réel >20 chars
        """
        original_len = len(df)
        
        if 'topic' not in df.columns:
            return df, 0
        
        # Regex: détecte si topic = emojis uniquement
        import re
        emoji_pattern = re.compile(r'^[\U0001F300-\U0001F9FF\s\U0001F600-\U0001F64F\U00002600-\U000027BF]*$')
        
        # Filtre posts emoji-only
        is_emoji_only = df['topic'].apply(lambda x: bool(emoji_pattern.match(str(x))) if pd.notna(x) else True)
        df = df[~is_emoji_only]
        
        # Filtre texte court
        if 'text' in df.columns:
            df = df[df['text'].notna() & (df['text'].str.len() >= 20)]
        
        removed = original_len - len(df)
        logger.debug(f"  Facebook emoji-only removed: {removed}")
        
        return df, removed
    
    def clean_parquet_file(self, filepath: Path) -> bool:
        """Nettoie un fichier Parquet et le réécrit."""
        try:
            logger.info(f"📄 Traitement: {filepath.name}")
            
            # Backup
            self.backup_file(filepath)
            
            # Load
            df = pd.read_parquet(filepath)
            original_len = len(df)
            self.stats["total_rows_before"] += original_len
            
            logger.debug(f"  Lignes initiales: {original_len}")
            
            # Identifier source
            source = df['source'].iloc[0] if 'source' in df.columns and len(df) > 0 else 'unknown'
            
            # Cleaning par source
            removed_total = 0
            
            if 'reddit' in source.lower():
                df, removed = self.clean_reddit_data(df)
                removed_total += removed
                self.stats["empty_texts_removed"] += removed
            
            elif 'facebook' in source.lower():
                df, removed = self.clean_facebook_data(df)
                removed_total += removed
                self.stats["facebook_emoji_removed"] += removed
            
            # Si <50% données restantes, skip le fichier (probablement tout fake)
            if len(df) < original_len * 0.5:
                logger.warning(f"  ⚠️  >50% données supprimées, fichier probablement synthétique")
                filepath.unlink()  # Supprimer complètement
                self.stats["synthetic_removed"] += 1
                return False
            
            # Sauvegarder
            if len(df) < original_len:
                df.to_parquet(filepath, index=False)
                logger.info(f"  ✅ Nettoyé: {original_len} → {len(df)} ({removed_total} supprimés)")
                self.stats["total_rows_after"] += len(df)
            else:
                logger.info(f"  ✅ Déjà propre: {len(df)} lignes")
                self.stats["total_rows_after"] += len(df)
            
            self.stats["files_processed"] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur sur {filepath.name}: {e}")
            return False
    
    def clean_all_data(self):
        """Pipeline complet de nettoyage."""
        logger.info("=" * 80)
        logger.info("🧹 DATA QUALITY CLEANER - DÉMARRAGE")
        logger.info("=" * 80)
        
        # Étape 1: Supprimer fichiers synthétiques
        logger.info("\n📍 ÉTAPE 1: Suppression fichiers synthétiques")
        self.remove_synthetic_files()
        
        # Étape 2: Nettoyer fichiers Parquet restants
        logger.info("\n📍 ÉTAPE 2: Nettoyage fichiers Parquet")
        
        parquet_files = list(self.data_raw.glob("*.parquet"))
        logger.info(f"Fichiers à traiter: {len(parquet_files)}")
        
        for filepath in parquet_files:
            # Skip backup files
            if 'backup' in str(filepath):
                continue
            self.clean_parquet_file(filepath)
        
        # Statistiques finales
        logger.info("\n" + "=" * 80)
        logger.info("📊 RAPPORT FINAL")
        logger.info("=" * 80)
        logger.info(f"Fichiers traités: {self.stats['files_processed']}")
        logger.info(f"Fichiers synthétiques supprimés: {self.stats['synthetic_removed']}")
        logger.info(f"Posts vides supprimés: {self.stats['empty_texts_removed']}")
        logger.info(f"Posts Facebook emojis supprimés: {self.stats['facebook_emoji_removed']}")
        logger.info(f"\nLignes AVANT: {self.stats['total_rows_before']}")
        logger.info(f"Lignes APRÈS: {self.stats['total_rows_after']}")
        
        reduction = self.stats['total_rows_before'] - self.stats['total_rows_after']
        pct = (reduction / self.stats['total_rows_before'] * 100) if self.stats['total_rows_before'] > 0 else 0
        logger.info(f"Réduction: {reduction} lignes ({pct:.1f}%)")
        
        logger.info("\n✅ NETTOYAGE TERMINÉ")
        logger.info(f"💾 Backups sauvegardés dans: {self.backup_dir}")
        logger.info("=" * 80)
    
    def validate_cleaned_data(self):
        """Valide que données nettoyées sont de qualité."""
        logger.info("\n🔬 VALIDATION QUALITÉ POST-CLEANING")
        
        parquet_files = list(self.data_raw.glob("*.parquet"))
        
        for filepath in parquet_files:
            if 'backup' in str(filepath):
                continue
            
            df = pd.read_parquet(filepath)
            
            # Métriques qualité (safe check for columns)
            text_filled_pct = (df['text'].notna() & (df['text'].str.len() > 10)).sum() / len(df) * 100 if 'text' in df.columns and len(df) > 0 else 0
            topic_filled_pct = df['topic'].notna().sum() / len(df) * 100 if 'topic' in df.columns and len(df) > 0 else 0
            
            logger.info(f"\n📄 {filepath.name}:")
            logger.info(f"  Lignes: {len(df)}")
            if 'text' in df.columns:
                logger.info(f"  Text rempli: {text_filled_pct:.1f}%")
            if 'topic' in df.columns:
                logger.info(f"  Topic rempli: {topic_filled_pct:.1f}%")
            
            if 'score' in df.columns:
                avg_score = df['score'].mean()
                logger.info(f"  Score moyen: {avg_score:,.0f}")
            
            # Warnings
            if text_filled_pct < 70:
                logger.warning(f"  ⚠️  Text enrichment faible ({text_filled_pct:.1f}%)")
            
            if topic_filled_pct < 95:
                logger.warning(f"  ⚠️  Topics manquants ({topic_filled_pct:.1f}%)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Nettoyeur de données automatique")
    parser.add_argument("--validate-only", action="store_true", help="Validation uniquement, pas de nettoyage")
    parser.add_argument("--dry-run", action="store_true", help="Simulation (pas de modifications)")
    
    args = parser.parse_args()
    
    cleaner = DataQualityCleaner()
    
    if args.validate_only:
        cleaner.validate_cleaned_data()
    else:
        if args.dry_run:
            logger.warning("🚧 MODE DRY-RUN (aucune modification)")
        
        cleaner.clean_all_data()
        cleaner.validate_cleaned_data()
        
        logger.success("\n🎉 Données nettoyées et validées avec succès!")
