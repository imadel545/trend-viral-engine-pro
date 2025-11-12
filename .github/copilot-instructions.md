# Instructions pour les Agents IA - Trend & Viral Engine Pro

## 🎯 Vue d'ensemble du projet

**Trend & Viral Engine Pro** est une plateforme ML de détection de tendances virales et génération automatique de contenu vidéo. Architecture microservices avec pipeline ML (ingestion → features → scoring → sélection → génération).

### Stack principal
- **Backend**: FastAPI (Python 3.10+), asyncio pour les opérations concurrentes
- **ML**: LightGBM (baseline), PyTorch Lightning (futur), scikit-learn pour calibration
- **LLM**: Groq API (GPT-OSS 120B) pour génération de scripts
- **Vidéo**: MoviePy + FFmpeg pour génération MP4
- **Storage**: Parquet (DuckDB), Qdrant (embeddings vectoriels)
- **MLOps**: MLflow (tracking), Prometheus + Grafana (monitoring)
- **Orchestration**: Prefect pour workflows

## 🏗️ Architecture critique

### Pipeline de données (à connaître absolument)
```
IngestionService (10min) → FeatureService → ScoringService (LightGBM) → SelectionService → GeneratorService
                              ↓                                                                    ↓
                         data/features/                                                      outputs/
```

**Points clés**:
- Chaque service est un singleton (pattern `get_*_service()` dans `src/services/*/service.py`)
- Données stockées en Parquet avec timestamp dans le nom: `{source}_{YYYYMMDD_HHMMSS}.parquet`
- Les services sont **async** quand ils font des appels réseau (ingestion, generator)

### Configuration (src/core/config.py)
- **TOUT** passe par `Settings` de Pydantic avec `.env` (jamais de hardcoding)
- Clés API obligatoires: `GROQ_API_KEY` (génération), optionnelles: Reddit, TikTok
- Utiliser `settings.ensure_directories()` au démarrage pour créer data/raw, data/features, etc.

### Services pattern
Chaque service suit ce pattern:
```python
# src/services/{name}/service.py
class {Name}Service:
    def __init__(self):
        self.logger = logger.bind(service="{name}")
    
    # Méthodes async si I/O réseau, sync sinon

# src/services/{name}/__init__.py
_instance = None
def get_{name}_service() -> {Name}Service:
    global _instance
    if _instance is None:
        _instance = {Name}Service()
    return _instance
```

## 💻 Workflows développeur

### Setup initial
```bash
# 1. Configuration
cp .env.example .env
# Éditer .env avec GROQ_API_KEY obligatoire

# 2. Installation
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# 3. Test
python test_installation.py
pytest  # tests unitaires
```

### Commandes courantes
```bash
# Démarrer l'API (développement)
uvicorn src.api.main:app --reload

# Avec Docker (production-like)
./start.sh  # ou make start

# Tests
make test          # tous les tests
make test-unit     # uniquement unitaires
pytest -k test_ingestion  # un test spécifique

# Nettoyage données
make clean
```

### Debugging
- Logs dans `logs/trend-engine-{date}.log` (rotation journalière via Loguru)
- API docs interactive: http://localhost:8000/docs
- MLflow UI: http://localhost:5000
- Prometheus: http://localhost:9090
- Pour tester un service: `python -c "from src.services.{name} import get_{name}_service; import asyncio; ..."`

## 📋 Conventions du projet

### Structure des fichiers
```
src/services/{service}/
├── __init__.py       # Singleton factory
├── service.py        # Logique principale
└── models.py         # Pydantic models (optionnel)
```

### Nommage
- **Services**: `{Name}Service` (CamelCase)
- **Factories**: `get_{name}_service()` (snake_case)
- **Fichiers Parquet**: `{source}_{timestamp}.parquet` avec `collected_at`, `source` columns
- **Endpoints API**: `/api/v1/{resource}` (versionné)

### Gestion d'erreurs
- Retry avec backoff exponentiel: `@backoff.on_exception(backoff.expo, Exception, max_tries=3)`
- Logging avant raise: `self.logger.error(f"Error: {e}")` puis `raise`
- Fallbacks pour services externes (voir `ScriptGenerator._fallback_script()`)

### ML patterns
- **Training**: `LightGBMModel.train()` avec split 80/20, early stopping (50 rounds)
- **Calibration**: Isotonic par défaut (`settings.model_calibration`)
- **Metrics**: AUC ≥ 0.80 cible, logged dans MLflow
- **Models**: sauvegardés dans `models/baseline_model.pkl` (pickle)
- **Retraining**: déclenché si `≥ 100` nouveaux samples dans `data/feedback/`

### Async/Sync
- **Async**: Ingestion (HTTP calls), Generator (LLM API), API endpoints
- **Sync**: Feature extraction, Scoring (modèle local), Video generation (MoviePy)
- Utiliser `asyncio.run()` pour appeler async depuis sync

## 🔌 Intégrations externes

### Groq LLM (critique)
- Endpoint: `https://api.groq.com/openai/v1/chat/completions`
- Model: `settings.groq_model` (défaut: `openai/gpt-oss-120b`)
- Prompt structure: System message + User message (voir `ScriptGenerator._build_prompt()`)
- Response parsing: JSON avec fallback manuel si échec

### Reddit (optionnel)
- Via `praw` library
- Authentification: `client_id`, `client_secret`, `user_agent` dans `.env`
- Rate limiting: géré par `praw`, mais ajouter retry avec backoff

### Google Trends
- Via `pytrends` library (pas d'API key requise)
- Régions: configurables via `settings.google_trends_regions` (liste)

## 🚀 Points d'extension

### Ajouter un nouveau service
1. Créer `src/services/{name}/`
2. Implémenter `{Name}Service` dans `service.py`
3. Créer factory `get_{name}_service()` dans `__init__.py`
4. Ajouter tests dans `tests/test_{name}.py`
5. Intégrer dans `src/api/main.py` si endpoint nécessaire

### Ajouter une source de données
1. Hériter de `DataSource` dans `src/services/ingestion/service.py`
2. Implémenter `async def collect(self, **kwargs) -> List[Dict[str, Any]]`
3. Ajouter dans `IngestionService.run_collection()`
4. Configurer dans `src/core/config.py` (clés API, etc.)

### Modifier le modèle ML
1. Changer params dans `LightGBMModel.train()` (src/services/scoring/service.py)
2. Ou créer nouvelle classe héritant de `ScoringModel`
3. Update `get_scoring_service()` factory
4. Re-train: `python scripts/training/train_baseline.py`

## ⚠️ Pièges courants

1. **Ne jamais** commit `.env` (dans `.gitignore`)
2. **Toujours** utiliser `settings.{param}` (pas de hardcoding)
3. **Vérifier** que `GROQ_API_KEY` existe avant génération (sinon crash)
4. **Ne pas** bloquer la event loop: pas de `time.sleep()` dans async, utiliser `asyncio.sleep()`
5. **MoviePy** nécessite FFmpeg installé système (pas pip)
6. **Parquet** nécessite `pyarrow` engine (spécifié explicitement)
7. **Services singletons**: ne pas créer manuellement, utiliser factories

## 📊 État actuel (Phase MVP)

### ✅ Implémenté
- Infrastructure Docker Compose
- API FastAPI avec endpoints: `/health`, `/score`, `/generate`, `/trends/topK`
- IngestionService (Google Trends, Reddit)
- Configuration centralisée (Pydantic Settings)
- Tests unitaires (structure)

### 🚧 En cours
- FeatureService (extraction embeddings multimodaux)
- ScoringService (modèle baseline LightGBM)
- GeneratorService (scripts LLM + vidéos MoviePy)
- SelectionService (Top K + diversité)

### 📝 À faire
- FeedbackService (boucle d'apprentissage)
- Prefect flows (orchestration automatique)
- Monitoring (métriques Prometheus custom)
- Tests d'intégration complets

## 📚 Références rapides

- **Architecture détaillée**: `docs/architecture.md`
- **Guide démarrage**: `QUICKSTART.md`
- **Exemple d'env**: `.env.example`
- **Tests d'install**: `python test_installation.py`
- **API docs**: http://localhost:8000/docs (après lancement)
