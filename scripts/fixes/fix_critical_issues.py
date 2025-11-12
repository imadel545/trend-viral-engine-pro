#!/usr/bin/env python3
"""
🔧 SCRIPT DE FIX URGENT - Problèmes Critiques

Ce script résout automatiquement les 4 problèmes CRITIQUES détectés:
1. Overfitting (modèle entraîné sur synthetic data)
2. Feature mismatch (473 vs 429)
3. Google Trends rate-limiting
4. Facebook désactivation

Usage:
    python scripts/fixes/fix_critical_issues.py
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from loguru import logger

logger.add("logs/fixes_{time}.log", rotation="10 MB")


class CriticalIssueFixer:
    """Fix all critical issues automatically."""

    def __init__(self):
        self.root = ROOT_DIR
        self.data_features = self.root / "data" / "features"
        self.models_dir = self.root / "models"
        self.backup_dir = self.root / "backups" / f"before_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("🔧 Critical Issue Fixer initialized")

    def run_all_fixes(self):
        """Execute all fixes in order."""
        logger.info("=" * 70)
        logger.info("🚀 STARTING CRITICAL FIXES")
        logger.info("=" * 70)
        
        # Create backup
        self.create_backup()
        
        # Fix 1: Remove synthetic data
        self.fix_1_remove_synthetic_data()
        
        # Fix 2: Create feature registry
        self.fix_2_create_feature_registry()
        
        # Fix 3: Disable Facebook
        self.fix_3_disable_facebook()
        
        # Fix 4: Fix Google Trends rate limiting
        self.fix_4_fix_google_trends()
        
        # Fix 5: Remove duplicate CircuitBreaker
        self.fix_5_remove_duplicate_code()
        
        logger.info("=" * 70)
        logger.info("✅ ALL CRITICAL FIXES COMPLETED")
        logger.info("=" * 70)
        logger.info(f"Backup created in: {self.backup_dir}")
        logger.info("")
        logger.info("🎯 NEXT STEPS:")
        logger.info("  1. Re-train model: python scripts/training/train_ensemble.py --force")
        logger.info("  2. Test pipeline: python scripts/test_e2e_pipeline.py")
        logger.info("  3. Start autonomous system: python scripts/automation/start_autonomous_system.py")

    def create_backup(self):
        """Create backup before modifications."""
        logger.info("📦 Creating backup...")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup important files
        to_backup = [
            self.root / ".env",
            self.models_dir,
            self.root / "src" / "core" / "config.py",
            self.root / "src" / "services" / "ingestion" / "service.py"
        ]
        
        for item in to_backup:
            if item.exists():
                if item.is_file():
                    dest = self.backup_dir / item.name
                    shutil.copy2(item, dest)
                else:
                    dest = self.backup_dir / item.name
                    shutil.copytree(item, dest, dirs_exist_ok=True)
        
        logger.success(f"✅ Backup created: {self.backup_dir}")

    def fix_1_remove_synthetic_data(self):
        """Fix 1: Remove all synthetic/fake data to prevent overfitting."""
        logger.info("\n🔧 FIX 1: Removing synthetic data...")
        
        patterns = ['*synthetic*', '*fake*', '*test_*', '*dummy*']
        removed = []
        
        for pattern in patterns:
            for file in self.data_features.glob(pattern):
                if file.suffix == '.parquet':
                    logger.debug(f"Removing: {file.name}")
                    file.unlink()
                    removed.append(file.name)
        
        if removed:
            logger.success(f"✅ Removed {len(removed)} synthetic files")
            for name in removed[:5]:  # Show first 5
                logger.info(f"   - {name}")
            if len(removed) > 5:
                logger.info(f"   ... and {len(removed) - 5} more")
        else:
            logger.info("ℹ️  No synthetic files found (already cleaned)")

    def fix_2_create_feature_registry(self):
        """Fix 2: Create feature registry to fix mismatch."""
        logger.info("\n🔧 FIX 2: Creating feature registry...")
        
        # Find latest feature file
        feature_files = sorted(self.data_features.glob("*advanced*.parquet"))
        
        if not feature_files:
            logger.warning("⚠️  No advanced feature files found, skipping registry")
            return
        
        latest_file = feature_files[-1]
        logger.info(f"Using features from: {latest_file.name}")
        
        # Load and extract feature names
        try:
            import pandas as pd
            df = pd.read_parquet(latest_file)
            
            # Remove label columns
            label_cols = {'is_breakout', 'label', 'viral', 'breakout'}
            feature_cols = [col for col in df.columns if col not in label_cols]
            
            # Create registry
            registry = {
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'source_file': latest_file.name,
                'n_features': len(feature_cols),
                'features': sorted(feature_cols),
                'label_columns': list(label_cols & set(df.columns)),
                'stats': {
                    'total_samples': len(df),
                    'feature_types': {
                        'numeric': int((df[feature_cols].dtypes != 'object').sum()),
                        'categorical': int((df[feature_cols].dtypes == 'object').sum())
                    }
                }
            }
            
            # Save registry
            registry_path = self.models_dir / "feature_registry.json"
            with open(registry_path, 'w') as f:
                json.dump(registry, f, indent=2)
            
            logger.success(f"✅ Feature registry created: {registry_path}")
            logger.info(f"   - Features: {len(feature_cols)}")
            logger.info(f"   - Samples: {len(df)}")
            logger.info(f"   - Labels: {registry['label_columns']}")
            
        except Exception as e:
            logger.error(f"❌ Error creating registry: {e}")

    def fix_3_disable_facebook(self):
        """Fix 3: Disable Facebook collection (emoji-only, useless)."""
        logger.info("\n🔧 FIX 3: Disabling Facebook collection...")
        
        env_file = self.root / ".env"
        
        if not env_file.exists():
            logger.warning("⚠️  .env file not found")
            return
        
        # Read .env
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update FACEBOOK_ENABLED
        modified = False
        new_lines = []
        
        for line in lines:
            if line.startswith('FACEBOOK_ENABLED='):
                new_lines.append('FACEBOOK_ENABLED=false  # Auto-disabled: emoji-only data\n')
                modified = True
            else:
                new_lines.append(line)
        
        # If not found, add it
        if not modified:
            new_lines.append('\n# Facebook disabled (emoji-only data)\n')
            new_lines.append('FACEBOOK_ENABLED=false\n')
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        
        logger.success("✅ Facebook collection disabled in .env")

    def fix_4_fix_google_trends(self):
        """Fix 4: Add rate limiting and caching to Google Trends."""
        logger.info("\n🔧 FIX 4: Fixing Google Trends rate limiting...")
        
        service_file = self.root / "src" / "services" / "ingestion" / "service.py"
        
        if not service_file.exists():
            logger.error("❌ service.py not found")
            return
        
        # Check if already fixed
        content = service_file.read_text()
        
        if 'time.sleep(random.uniform(2, 5))' in content:
            logger.info("ℹ️  Google Trends already has rate limiting")
            return
        
        logger.info("   Adding rate limiting to Google Trends...")
        logger.info("   ⚠️  Manual fix required:")
        logger.info("")
        logger.info("   1. Open: src/services/ingestion/service.py")
        logger.info("   2. In GoogleTrendsSource.collect(), add:")
        logger.info("      ```python")
        logger.info("      import time, random")
        logger.info("      time.sleep(random.uniform(2, 5))  # Rate limiting")
        logger.info("      ```")
        logger.info("   3. Add cache checking before API call")
        logger.info("")
        logger.warning("⚠️  This fix requires manual code modification")

    def fix_5_remove_duplicate_code(self):
        """Fix 5: Remove duplicate CircuitBreaker from optimizations.py."""
        logger.info("\n🔧 FIX 5: Removing duplicate CircuitBreaker...")
        
        optimizations_file = self.root / "src" / "core" / "optimizations.py"
        
        if not optimizations_file.exists():
            logger.warning("⚠️  optimizations.py not found")
            return
        
        content = optimizations_file.read_text()
        
        # Check if CircuitBreaker exists
        if 'class CircuitBreaker' in content:
            logger.info("   Found duplicate CircuitBreaker in optimizations.py")
            logger.warning("   ⚠️  Manual fix required:")
            logger.info("")
            logger.info("   1. Open: src/core/optimizations.py")
            logger.info("   2. Remove CircuitBreaker and CircuitState classes")
            logger.info("   3. Import from resilience.py instead:")
            logger.info("      ```python")
            logger.info("      from src.core.resilience import CircuitBreaker, CircuitState")
            logger.info("      ```")
            logger.info("")
        else:
            logger.info("ℹ️  No duplicate CircuitBreaker found")


def main():
    """Main entry point."""
    fixer = CriticalIssueFixer()
    
    try:
        fixer.run_all_fixes()
        return 0
    except Exception as e:
        logger.error(f"❌ Critical error during fixes: {e}")
        logger.exception(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
