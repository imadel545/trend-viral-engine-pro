# Trend & Viral Engine Pro

<div align="center">

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)

**Plateforme autonome de détection de tendances virales et génération automatique de contenu**

</div>

## 📋 Table des matières

- [Vue d'ensemble](#-vue-densemble)
- [Architecture](#-architecture)
- [Fonctionnalités](#-fonctionnalités)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [API Reference](#-api-reference)
- [Développement](#-développement)
- [Monitoring](#-monitoring)
- [Tests](#-tests)
- [Roadmap](#-roadmap)

## 🎯 Vue d'ensemble

**Trend & Viral Engine Pro** est une solution professionnelle qui :

- 🔍 **Observe** en quasi-temps réel les tendances sur TikTok, Google Trends, Reddit
- 🧠 **Détecte** les sujets susceptibles de devenir viraux (scoring ML avancé)
- 🎬 **Génère** automatiquement du contenu optimisé (scripts + vidéos + captions)
- 🚀 **Fournit** une API robuste pour une intégration facile
- 📊 **Apprend** en continu via une boucle de feedback

### Objectifs clés

- ⚡ Latence ingestion → score : **< 10 minutes**
- 🎯 AUC modèle baseline : **≥ 0.80**
- 📈 Hit-rate sujets viraux : **≥ 30%**
- 🎥 Production quotidienne : **3 vidéos/jour**
- ✅ Couverture tests : **≥ 80%**

## 🏗️ Architecture

```
┌─────────────────┐
│  Data Sources   │ TikTok, Google Trends, Reddit
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ IngestionService│ Collecte toutes les 10 min
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FeatureService  │ Extraction features + embeddings
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ScoringService  │ LightGBM + calibration
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│SelectionService │ Top K + diversité
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│GeneratorService │ Script (Groq) + Vidéo (MoviePy)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Content Output │ MP4 + Caption + Metadata
└────────┬────────┘
         │
         ▼
   Publication manuelle
         │
         ▼
┌─────────────────┐
│FeedbackService  │ Métriques → Ré-entraînement
└─────────────────┘
```

### Composants principaux

- **IngestionService** : Collecte des données de tendances
- **FeatureService** : Calcul de features temporelles et embeddings multimodaux
- **ScoringService** : Modèle ML pour scoring de viralité
- **SelectionService** : Sélection intelligente des meilleurs sujets
- **GeneratorService** : Génération de contenu (LLM + vidéo)
- **FeedbackService** : Boucle d'apprentissage continu
- **API Server** : Endpoints REST (FastAPI)

### Stack technologique

| Catégorie | Technologies |
|-----------|-------------|
| **Language** | Python 3.10+ |
| **API** | FastAPI, Uvicorn |
| **ML Baseline** | LightGBM, scikit-learn |
| **Deep Learning** | PyTorch Lightning, Transformers |
| **Embeddings** | Sentence-Transformers, OpenCLIP |
| **LLM** | Groq API (GPT-OSS 120B) |
| **Video** | MoviePy, FFmpeg |
| **TTS** | Coqui-TTS |
| **Orchestration** | Prefect |
| **Storage** | Parquet, DuckDB, Qdrant |
| **MLOps** | MLflow |
| **Monitoring** | Prometheus, Grafana |
| **Container** | Docker Compose |

## ✨ Fonctionnalités

### Phase 0 - MVP (Semaine 1)

- [x] Setup infrastructure (Docker Compose)
- [x] Ingestion basique (Google Trends, Reddit)
- [x] Stockage Parquet
- [x] API minimale (`/health`, `/score`)

### Phase 1 - Core Engine (Semaine 2)

- [ ] Feature extraction complète
- [ ] Modèle baseline LightGBM
- [ ] Scoring en temps réel
- [ ] Top K selection

### Phase 2 - Content Generation (Semaine 3)

- [ ] Génération de scripts via Groq LLM
- [ ] Génération de vidéos MP4
- [ ] Captions automatiques
- [ ] TTS intégration

### Phase 3 - Learning Loop (Semaine 4)

- [ ] Feedback pipeline
- [ ] Ré-entraînement automatique
- [ ] A/B testing
- [ ] Monitoring avancé

### Phase 4 - Advanced (Future)

- [ ] Modèle deep multimodal
- [ ] Bandits contextuels (LinUCB)
- [ ] Publication automatique
- [ ] UI Dashboard

## 🚀 Installation

### Prérequis

- Python 3.10+
- Docker & Docker Compose
- FFmpeg
- 8GB RAM minimum
- 20GB espace disque

### Installation rapide

```bash
# Cloner le repository
git clone <repo-url>
cd "Trend & Viral Engine Pro"

# Copier la configuration
cp .env.example .env

# Éditer .env avec vos clés API
nano .env

# Lancer avec Docker
docker-compose up -d

# Ou installation locale
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## ⚙️ Configuration

Créer un fichier `.env` basé sur `.env.example` :

```bash
# API Keys requises
GROQ_API_KEY=gsk_your_key_here
TIKTOK_API_KEY=your_tiktok_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret

# Configuration optionnelle
ENVIRONMENT=production
LOG_LEVEL=INFO
TOP_K_DEFAULT=10
```

## 📖 Utilisation

### Démarrage des services

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f api

# Arrêter
docker-compose down
```

### Exécution manuelle

```bash
# Lancer l'API
uvicorn src.api.main:app --reload

# Lancer un flow d'ingestion
python scripts/flows/ingestion_flow.py

# Entraîner le modèle
python scripts/training/train_baseline.py

# Générer du contenu
python scripts/generate_content.py --topic "IA tendance 2026"
```

## 🔌 API Reference

### Endpoints principaux

#### `GET /health`

Vérification de l'état du service.

```bash
curl http://localhost:8000/health
```

#### `POST /api/v1/score`

Scorer un sujet pour sa probabilité de viralité.

```bash
curl -X POST http://localhost:8000/api/v1/score \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "ai automation 2026",
    "hashtags": ["#ai", "#automation"],
    "country": "FR"
  }'
```

**Response:**
```json
{
  "score": 0.87,
  "predicted_views_24h": 125000,
  "confidence": 0.92,
  "features_used": ["slope", "acceleration", "embeddings"]
}
```

#### `GET /api/v1/trends/topK`

Récupérer les K meilleurs sujets.

```bash
curl "http://localhost:8000/api/v1/trends/topK?country=FR&k=10"
```

#### `POST /api/v1/generate`

Générer du contenu pour un sujet.

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "ai automation 2026",
    "format": "video",
    "duration": 25
  }'
```

#### `POST /api/v1/feedback`

Soumettre des métriques de performance.

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "abc123",
    "views": 50000,
    "likes": 2500,
    "watch_time": 0.75
  }'
```

### Documentation interactive

- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc

## 🛠️ Développement

### Structure du projet

```
trend-viral-engine-pro/
├── src/
│   ├── api/              # API FastAPI
│   ├── core/             # Configuration, logging
│   ├── services/         # Services métier
│   │   ├── ingestion/
│   │   ├── features/
│   │   ├── scoring/
│   │   ├── selection/
│   │   ├── generator/
│   │   └── feedback/
│   ├── models/           # Modèles ML
│   └── utils/            # Utilitaires
├── scripts/
│   ├── flows/            # Prefect flows
│   └── training/         # Scripts ML
├── tests/                # Tests unitaires
├── monitoring/           # Config Prometheus/Grafana
├── data/                 # Données (git-ignored)
├── models/               # Modèles entraînés
├── outputs/              # Contenu généré
└── docs/                 # Documentation
```

### Tests

```bash
# Tous les tests
pytest

# Tests unitaires seulement
pytest -m unit

# Avec couverture
pytest --cov=src --cov-report=html

# Tests d'intégration
pytest -m integration
```

### Code quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Linting
flake8 src/ tests/
pylint src/

# Type checking
mypy src/
```

## 📊 Monitoring

### Dashboards

- **Grafana** : http://localhost:3000 (admin/admin)
- **Prometheus** : http://localhost:9090
- **MLflow** : http://localhost:5000

### Métriques clés

- **Ingestion rate** : nombre de sujets/heure
- **API latency** : P95 latence endpoints
- **Model performance** : AUC, précision, recall
- **Content quality** : taux de succès génération
- **System health** : CPU, RAM, erreurs

## 🗺️ Roadmap

### Q4 2024
- ✅ Phase 0: Infrastructure
- 🔄 Phase 1: Core Engine
- 📋 Phase 2: Content Generation

### Q1 2025
- 📋 Phase 3: Learning Loop
- 📋 Modèle deep multimodal
- 📋 Bandits contextuels

### Q2 2025
- 📋 Publication automatique
- 📋 UI Dashboard premium
- 📋 API publique v1

## 📄 License

Proprietary - All rights reserved

## 🤝 Support

Pour toute question ou assistance :
- 📧 Email : support@trendengine.pro
- 📖 Documentation : http://docs.trendengine.pro

---

<div align="center">

**Trend & Viral Engine Pro** - Détectez les tendances avant qu'elles explosent 🚀

</div>
