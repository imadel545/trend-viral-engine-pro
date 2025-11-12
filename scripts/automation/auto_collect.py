"""
🤖 AUTOMATION - Collection automatique toutes les 6h

Lance le pipeline complet:
1. Collection (Google Trends, Reddit, YouTube)
2. Feature extraction
3. Scoring ML
4. Détection early trends
5. Sauvegarde prédictions

Usage:
    # Test run (1 fois)
    python scripts/automation/auto_collect.py --once
    
    # Mode daemon (boucle infinie, 6h interval)
    python scripts/automation/auto_collect.py --daemon
    
    # Mode cron (pour crontab)
    0 */6 * * * cd /path && python scripts/automation/auto_collect.py --cron
"""

import argparse
import asyncio
import time
from datetime import datetime
from pathlib import Path

import schedule
from loguru import logger

from src.services.ingestion import get_ingestion_service
from src.services.features import get_feature_service
from src.services.scoring import get_scoring_service


async def run_full_pipeline():
    """
    Pipeline complet: collecte → features → score → early detection.
    
    Returns:
        dict: Résultats du pipeline
    """
    
    print("\n" + "=" * 80)
    print(f"🚀 AUTO-COLLECTION PIPELINE")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")
    
    results = {
        "start_time": datetime.now(),
        "success": False,
        "errors": []
    }
    
    try:
        # ═══════════════════════════════════════════════════════════
        # PHASE 1: COLLECTION
        # ═══════════════════════════════════════════════════════════
        print("📥 PHASE 1: Collection de données")
        print("─" * 80)
        
        ingestion = get_ingestion_service()
        raw_data = await ingestion.run_collection()
        
        results["raw_data_files"] = raw_data
        results["sources_collected"] = len(raw_data)
        
        print(f"✅ Collection terminée: {len(raw_data)} sources")
        for source, path in raw_data.items():
            if path:
                print(f"  • {source}: {path.name}")
        print()
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 2: FEATURE EXTRACTION
        # ═══════════════════════════════════════════════════════════
        print("🔧 PHASE 2: Extraction de features")
        print("─" * 80)
        
        feature_service = get_feature_service()
        feature_files = []
        
        for source, path in raw_data.items():
            if path and path.exists():
                try:
                    feature_path = feature_service.process_raw_data(path)
                    feature_files.append(feature_path)
                    print(f"✅ Features extraites: {feature_path.name}")
                except Exception as e:
                    logger.error(f"Erreur extraction features {source}: {e}")
                    results["errors"].append(f"Feature extraction {source}: {str(e)}")
        
        results["feature_files"] = feature_files
        print(f"\n✅ Extraction terminée: {len(feature_files)} fichiers")
        print()
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 3: SCORING ML
        # ═══════════════════════════════════════════════════════════
        print("🤖 PHASE 3: Scoring ML")
        print("─" * 80)
        
        scoring_service = get_scoring_service()
        
        # Charger le dernier fichier de features
        if feature_files:
            latest_features = feature_files[-1]
            
            import pandas as pd
            df_features = pd.read_parquet(latest_features)
            
            try:
                # Score avec le modèle
                df_scored = scoring_service.score(df_features)
                
                # Sauvegarder scores
                scored_path = latest_features.parent / f"scored_{latest_features.stem}.parquet"
                df_scored.to_parquet(scored_path, engine='pyarrow')
                
                results["scored_file"] = scored_path
                results["trends_scored"] = len(df_scored)
                
                print(f"✅ Scoring terminé: {len(df_scored)} trends")
                print(f"   Scores range: {df_scored['p_breakout_24h'].min():.3f} - {df_scored['p_breakout_24h'].max():.3f}")
                
            except Exception as e:
                logger.warning(f"Scoring échoué (modèle pas encore entraîné?): {e}")
                results["errors"].append(f"Scoring: {str(e)}")
        
        print()
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 4: EARLY TREND DETECTION
        # ═══════════════════════════════════════════════════════════
        print("🔮 PHASE 4: Détection early trends")
        print("─" * 80)
        
        try:
            # Importer le detector
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            
            from analysis.detect_early_trends import EarlyTrendDetector
            
            detector = EarlyTrendDetector()
            df_latest = detector.load_latest_data()
            early_trends = detector.detect(df_latest, top_n=20)
            
            # Sauvegarder prédictions
            predictions_path = detector.save_predictions(early_trends)
            
            # Générer rapport
            report_text = detector.generate_report(early_trends)
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            report_path = reports_dir / f"early_trends_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            results["predictions_file"] = predictions_path
            results["report_file"] = report_path
            results["early_trends_count"] = len(early_trends)
            
            print(f"✅ Early trends détectées: {len(early_trends)}")
            print(f"   Prédictions: {predictions_path}")
            print(f"   Rapport: {report_path}")
            
        except Exception as e:
            logger.warning(f"Early detection échoué: {e}")
            results["errors"].append(f"Early detection: {str(e)}")
        
        print()
        
        # ═══════════════════════════════════════════════════════════
        # RÉSUMÉ
        # ═══════════════════════════════════════════════════════════
        results["success"] = True
        results["end_time"] = datetime.now()
        results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()
        
        print("=" * 80)
        print("✅ PIPELINE TERMINÉ AVEC SUCCÈS")
        print("=" * 80)
        print(f"⏱️  Durée: {results['duration']:.1f}s")
        print(f"📊 Sources: {results.get('sources_collected', 0)}")
        print(f"🔧 Features: {len(results.get('feature_files', []))}")
        print(f"🤖 Trends scorées: {results.get('trends_scored', 0)}")
        print(f"🔮 Early trends: {results.get('early_trends_count', 0)}")
        
        if results["errors"]:
            print(f"\n⚠️  Erreurs: {len(results['errors'])}")
            for err in results["errors"]:
                print(f"   • {err}")
        
        print("\n💡 PROCHAINES ÉTAPES:")
        print("  1. Consultez le rapport: reports/early_trends_*.txt")
        print("  2. Vérifiez les prédictions: data/predictions/*.json")
        print("  3. Créez du contenu sur les top 5 trends")
        print("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Pipeline échoué: {e}")
        import traceback
        traceback.print_exc()
        results["success"] = False
        results["errors"].append(str(e))
    
    return results


def run_once():
    """Lance le pipeline une fois."""
    logger.info("🚀 Mode: Single run")
    result = asyncio.run(run_full_pipeline())
    return 0 if result["success"] else 1


def run_daemon(interval_hours: int = 6):
    """Lance le pipeline en mode daemon (boucle infinie)."""
    
    logger.info(f"🤖 Mode: Daemon (interval: {interval_hours}h)")
    logger.info("   Press Ctrl+C to stop")
    logger.info("")
    
    def job():
        asyncio.run(run_full_pipeline())
    
    # Première run immédiate
    job()
    
    # Schedule les runs suivants
    schedule.every(interval_hours).hours.do(job)
    
    logger.info(f"⏰ Prochaine run: dans {interval_hours}h")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\n⏹️  Daemon arrêté par l'utilisateur")
        return 0


def run_cron():
    """Mode cron (une run puis exit)."""
    logger.info("📅 Mode: Cron job")
    return run_once()


def main():
    parser = argparse.ArgumentParser(
        description="Automation: Collection automatique de tendances"
    )
    
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--once',
        action='store_true',
        help="Run une fois puis exit"
    )
    group.add_argument(
        '--daemon',
        action='store_true',
        help="Mode daemon (boucle infinie)"
    )
    group.add_argument(
        '--cron',
        action='store_true',
        help="Mode cron (pour crontab)"
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=6,
        help="Interval en heures (mode daemon, défaut: 6)"
    )
    
    args = parser.parse_args()
    
    # Par défaut: mode once
    if not any([args.once, args.daemon, args.cron]):
        args.once = True
    
    if args.once:
        return run_once()
    elif args.daemon:
        return run_daemon(args.interval)
    elif args.cron:
        return run_cron()


if __name__ == "__main__":
    exit(main())
