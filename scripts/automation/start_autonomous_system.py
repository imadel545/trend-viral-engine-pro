"""
Démarre le système autonome complet de Trend & Viral Engine Pro.

Ce script configure et lance tous les composants nécessaires:
- Serveur Prefect (orchestration)
- Deployments des flows (ingestion, génération, feedback/training)
- Monitoring (optionnel)

Usage:
    python scripts/automation/start_autonomous_system.py
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

from loguru import logger

# Ajouter le root au path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.config import settings


def check_prefect_server():
    """Vérifie si le serveur Prefect est actif."""
    try:
        import httpx
        response = httpx.get("http://localhost:4200/api/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def start_prefect_server():
    """Démarre le serveur Prefect en arrière-plan."""
    logger.info("Démarrage du serveur Prefect...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "prefect", "server", "start"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Attendre que le serveur soit prêt (max 30s)
    for i in range(30):
        time.sleep(1)
        if check_prefect_server():
            logger.success("✅ Serveur Prefect démarré (http://localhost:4200)")
            return process
        
        if i % 5 == 0:
            logger.info(f"Attente du serveur Prefect... ({i}s)")
    
    logger.error("❌ Timeout: Serveur Prefect non démarré")
    process.terminate()
    return None


def deploy_flows():
    """Déploie tous les flows Prefect."""
    logger.info("Déploiement des flows Prefect...")
    
    deployment_script = ROOT_DIR / "scripts" / "flows" / "deployments.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(deployment_script)],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        logger.success("✅ Flows déployés avec succès")
        logger.info(result.stdout)
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erreur de déploiement: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout lors du déploiement")
        return False


def start_worker():
    """Démarre un worker Prefect pour exécuter les flows."""
    logger.info("Démarrage du worker Prefect...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "prefect", "agent", "start", "-q", "default"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(3)
    
    if process.poll() is None:
        logger.success("✅ Worker Prefect démarré")
        return process
    else:
        logger.error("❌ Échec du démarrage du worker")
        return None


def print_system_status():
    """Affiche le statut du système."""
    print("\n" + "=" * 70)
    print("🚀 SYSTÈME AUTONOME TREND & VIRAL ENGINE PRO")
    print("=" * 70)
    
    print("\n📊 COMPOSANTS ACTIFS:")
    print("  ✓ Serveur Prefect    : http://localhost:4200")
    print("  ✓ Worker Prefect     : Queue 'default'")
    print("  ✓ API FastAPI        : http://localhost:8000 (démarrer séparément)")
    
    print("\n⚙️  FLOWS PLANIFIÉS:")
    print("  • ingestion-every-10min       : Toutes les 10 minutes")
    print("  • content-generation-daily    : 3x/jour (6h, 12h, 18h)")
    print("  • feedback-processing-nightly : Chaque nuit à 2h")
    print("  • training-on-demand          : Déclenché automatiquement")
    
    print("\n🔄 PIPELINE AUTONOME:")
    print("  1. Ingestion automatique (10 min)")
    print("  2. Extraction de features")
    print("  3. Scoring ML des tendances")
    print("  4. Génération de contenu (3x/jour)")
    print("  5. Collecte de feedback")
    print("  6. Ré-entraînement automatique (si seuil atteint)")
    
    print("\n📁 DONNÉES:")
    print(f"  • Raw data       : {settings.data_raw_path}")
    print(f"  • Features       : {settings.data_features_path}")
    print(f"  • Feedback       : {settings.data_feedback_path}")
    print(f"  • Models         : {settings.models_path}")
    
    print("\n🎛️  MONITORING:")
    print(f"  • MLflow         : {settings.mlflow_tracking_uri}")
    print(f"  • Prometheus     : http://localhost:{settings.prometheus_port}")
    print(f"  • Logs           : logs/")
    
    print("\n🛠️  COMMANDES UTILES:")
    print("  • Dashboard Prefect  : http://localhost:4200")
    print("  • Démarrer API       : uvicorn src.api.main:app --reload")
    print("  • Tester training    : python scripts/training/train_ensemble.py")
    print("  • Générer rapport    : python scripts/monetization/generate_viral_report.py")
    
    print("\n💡 ARRÊTER LE SYSTÈME:")
    print("  • Ctrl+C dans ce terminal pour arrêter worker + serveur")
    print("  • Ou manuellement: prefect server stop")
    
    print("\n" + "=" * 70)
    print()


def main():
    """Point d'entrée principal."""
    logger.info("🚀 Démarrage du système autonome...")
    
    # 1. Vérifier/démarrer serveur Prefect
    if check_prefect_server():
        logger.info("✅ Serveur Prefect déjà actif")
        server_process = None
    else:
        server_process = start_prefect_server()
        if not server_process:
            logger.error("❌ Impossible de démarrer le système")
            return 1
    
    # 2. Déployer les flows
    if not deploy_flows():
        logger.error("❌ Échec du déploiement des flows")
        if server_process:
            server_process.terminate()
        return 1
    
    # 3. Démarrer le worker
    worker_process = start_worker()
    if not worker_process:
        logger.error("❌ Échec du démarrage du worker")
        if server_process:
            server_process.terminate()
        return 1
    
    # 4. Afficher le statut
    print_system_status()
    
    # 5. Garder les processus actifs
    logger.info("✅ Système autonome opérationnel! (Ctrl+C pour arrêter)")
    
    try:
        # Attendre indéfiniment
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Arrêt du système...")
        
        if worker_process:
            worker_process.terminate()
            worker_process.wait(timeout=5)
        
        if server_process:
            server_process.terminate()
            server_process.wait(timeout=5)
        
        logger.success("✅ Système arrêté proprement")
        return 0


if __name__ == "__main__":
    sys.exit(main())
