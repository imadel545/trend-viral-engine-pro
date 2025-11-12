# 🚀 QUICK START GUIDE - Trend & Viral Engine Pro

## Démarrage rapide en 5 minutes

### Étape 1: Configuration initiale

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env et ajouter vos clés API
nano .env  # ou utilisez votre éditeur préféré
```

**Clés API requises:**

- `GROQ_API_KEY` - Obtenir sur https://console.groq.com
- `REDDIT_CLIENT_ID` et `REDDIT_CLIENT_SECRET` - Obtenir sur https://www.reddit.com/prefs/apps
- `TIKTOK_API_KEY` (optionnel) - Pour TikTok Creative Center

### Étape 2: Lancement avec Docker (Recommandé)

```bash
# Lancer tous les services
./start.sh  # Linux/Mac
# ou
start.bat   # Windows

# Vérifier que tout fonctionne
curl http://localhost:8000/health
```

### Étape 3: Installation locale (Alternative)

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances système requises
# IMPORTANT: ImageMagick est requis pour la génération vidéo (MoviePy)
# macOS
brew install imagemagick

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y imagemagick

# Vérifier l'installation
convert -version  # Devrait afficher la version d'ImageMagick

# Installer les dépendances Python
pip install -r requirements.txt

# Lancer l'API
uvicorn src.api.main:app --reload
```

### Étape 4: Test de l'installation

```bash
# Tester l'installation
python test_installation.py

# Lancer les tests unitaires
pytest
```

## Premiers pas

### 1. Collecter des données

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/admin/trigger-ingestion

# Via script Python
python -c "
from src.services.ingestion import get_ingestion_service
import asyncio
service = get_ingestion_service()
asyncio.run(service.run_collection())
"
```

### 2. Obtenir les tendances top K

```bash
# Top 10 tendances pour la France
curl "http://localhost:8000/api/v1/trends/topK?country=FR&k=10"
```

### 3. Scorer un sujet

```bash
curl -X POST http://localhost:8000/api/v1/score \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Intelligence Artificielle 2026",
    "country": "FR"
  }'
```

### 4. Générer du contenu

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "IA et automatisation",
    "duration": 25
  }'
```

Les fichiers générés seront dans le dossier `outputs/`:

- `video_*.mp4` - La vidéo
- `video_*.txt` - La caption
- `video_*.json` - Les métadonnées

### 5. Soumettre des métriques (Feedback)

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "video_20251102_120000",
    "views": 50000,
    "likes": 2500,
    "comments": 150,
    "watch_time": 0.75,
    "shares": 100
  }'
```

## Accès aux dashboards

| Service    | URL                             | Identifiants |
| ---------- | ------------------------------- | ------------ |
| API Docs   | http://localhost:8000/docs      | -            |
| Grafana    | http://localhost:3000           | admin/admin  |
| MLflow     | http://localhost:5000           | -            |
| Prometheus | http://localhost:9090           | -            |
| Qdrant     | http://localhost:6333/dashboard | -            |

## Commandes utiles

```bash
# Voir les logs
docker-compose logs -f api

# Redémarrer un service
docker-compose restart api

# Arrêter tous les services
docker-compose down

# Nettoyer les données
make clean

# Lancer les tests
make test

# Formater le code
make format
```

## Workflows automatiques

Les workflows suivants s'exécutent automatiquement:

1. **Ingestion** - Toutes les 10 minutes
2. **Génération de contenu** - 3x par jour (6h, 12h, 18h)
3. **Traitement feedback** - Chaque nuit à 2h

Gérer via Prefect UI: http://localhost:4200

## Troubleshooting

### Problème: L'API ne démarre pas

```bash
# Vérifier les logs
docker-compose logs api

# Reconstruire l'image
docker-compose build api
docker-compose up -d api
```

### Problème: Erreur d'import

```bash
# Vérifier l'installation
python test_installation.py

# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall
```

### Problème: Manque de données

```bash
# Déclencher manuellement l'ingestion
curl -X POST http://localhost:8000/api/v1/admin/trigger-ingestion
```

### Problème: Génération vidéo échoue

```bash
# Vérifier FFmpeg
ffmpeg -version

# Installer FFmpeg si nécessaire
# Mac: brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
# Windows: https://ffmpeg.org/download.html
```

## Prochaines étapes

1. 📖 Lire la [documentation complète](docs/getting-started.md)
2. 🏗️ Comprendre l'[architecture](docs/architecture.md)
3. 🔧 Configurer les [workflows Prefect](scripts/flows/)
4. 📊 Explorer les [dashboards Grafana](http://localhost:3000)
5. 🤖 Entraîner un [modèle personnalisé](scripts/training/)

## Support

- 📧 Email: support@trendengine.pro
- 📖 Documentation: docs/
- 🐛 Issues: GitHub Issues

---

**Trend & Viral Engine Pro** - Détectez les tendances avant qu'elles explosent 🚀
