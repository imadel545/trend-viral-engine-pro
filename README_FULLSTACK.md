# 🚀 Trend & Viral Engine Pro - Fullstack

**Plateforme IA complète** de prédiction de contenu viral avec interface moderne.

---

## 📦 Structure du Projet

```
Trend & Viral Engine Pro/
├── 🔧 Backend (FastAPI)
│   ├── src/
│   │   ├── api/              # API REST
│   │   ├── services/         # Services métier
│   │   └── core/             # Configuration
│   ├── data/                 # Données (Parquet)
│   ├── models/               # Modèles ML
│   └── requirements.txt
│
├── 🎨 Frontend (Next.js 14)
│   ├── app/                  # Pages
│   ├── components/
│   │   ├── ui/              # Button, Card, Input, Badge
│   │   └── features/        # PredictionForm, Results
│   ├── lib/
│   │   ├── models.ts        # Domain Models OOP
│   │   ├── api.ts           # API Services
│   │   ├── stores.ts        # Zustand State
│   │   └── design-system.ts # Design Tokens
│   └── hooks/               # Custom Hooks
│
└── 📝 Documentation
    ├── QUICKSTART.md
    ├── ARCHITECTURE_OOP_ADVANCED.md
    └── frontend/GUIDE_UI_UX.md
```

---

## ⚡ Démarrage Ultra-Rapide

### Option 1 : Script Automatique (Recommandé)

```bash
./start_fullstack.sh
```

**🎉 C'est tout !** Backend + Frontend lancés automatiquement.

### Option 2 : Manuel

**Terminal 1 - Backend :**

```bash
source venv/bin/activate
uvicorn src.api.main:app --reload
```

**Terminal 2 - Frontend :**

```bash
cd frontend
npm run dev
```

---

## 🌐 URLs

| Service            | URL                          | Description           |
| ------------------ | ---------------------------- | --------------------- |
| 🖥️ **Frontend**    | http://localhost:3000        | Interface utilisateur |
| 🔌 **Backend API** | http://localhost:8000        | API REST              |
| 📚 **API Docs**    | http://localhost:8000/docs   | Swagger UI            |
| ❤️ **Health**      | http://localhost:8000/health | Status serveur        |

---

## 🏗️ Stack Technique

### Backend

- **Framework**: FastAPI (Python 3.10+)
- **ML**: LightGBM, PyTorch Lightning, scikit-learn
- **LLM**: Groq API (GPT-OSS 120B)
- **Storage**: Parquet (DuckDB), Qdrant (embeddings)
- **MLOps**: MLflow, Prometheus, Grafana

### Frontend

- **Framework**: Next.js 14 + TypeScript
- **State**: Zustand (stores)
- **UI**: Tailwind CSS + Framer Motion
- **Charts**: Recharts (interactifs)
- **HTTP**: Axios + React Query
- **Icons**: Lucide React

---

## 🎨 Fonctionnalités UI/UX

### Design Avancé

- ✨ **Glassmorphism** (backdrop-blur)
- 🌈 **Gradients** dynamiques (7 presets)
- 🎭 **Animations** Framer Motion (8 presets)
- 🌓 **Dark/Light mode** avec toggle
- 📱 **Responsive** (mobile-first)

### Composants

- 🔘 **Button** : 6 variants, ripple effect, loading
- 🃏 **Card** : Glassmorphism, hover animations
- 📝 **Input** : Validation, password toggle, icons
- 🏷️ **Badge** : 5 variants, pulse animation

### Features

- 📊 **Charts interactifs** (projection 7 jours, radar)
- 🎯 **Platform selector** animé (TikTok, Instagram, YouTube, Reddit)
- 💡 **Recommendations** IA avec copy-to-clipboard
- 🔥 **Viral badge** pulsant pour contenu à fort potentiel

---

## 🔌 API Endpoints

### Prédictions

```bash
# Prédire un contenu
POST /api/v1/predict
{
  "title": "Top 10 AI Tools",
  "platform": "tiktok",
  "follower_count": 50000
}

# Comparer plateformes
POST /api/v1/compare
{
  "title": "Amazing AI Demo",
  "platforms": ["tiktok", "instagram", "youtube"],
  "follower_counts": {
    "tiktok": 50000,
    "instagram": 75000,
    "youtube": 25000
  }
}
```

### Tendances

```bash
# Top K tendances
GET /api/v1/trends/topK?k=10

# Lancer une collecte
POST /api/v1/trends/collect
{
  "sources": ["google_trends"]
}
```

---

## 📊 Architecture OOP

### Backend (Python)

```python
# Services avec Singleton Pattern
from src.services.scoring import get_scoring_service

service = get_scoring_service()
predictions = service.score(data)

# Patterns implémentés
- Singleton (services)
- Observer (notifications)
- Factory (models)
- Decorator (@cached, @retry, @monitored)
```

### Frontend (TypeScript)

```typescript
// Domain Models avec business logic
const prediction = new Prediction(data);
prediction.isHighROI(); // true si ROI > 100%
prediction.getFormattedRevenue(); // "72,630€"

// API Services (Singleton)
const service = getPredictionService();
const result = await service.predict(request);

// Zustand Stores
const { predict, loading } = usePredictionStore();
await predict(title, platform, followers);
```

---

## 🧪 Tests

### Backend

```bash
# Tests unitaires
pytest

# Tests E2E
python test_real_viral_production.py

# Coverage
pytest --cov=src tests/
```

### Frontend

```bash
cd frontend

# Build (TypeScript check)
npm run build

# Lint
npm run lint

# Type check
npm run type-check
```

---

## 📈 Exemple d'Utilisation

### 1. Prédire un Contenu

```typescript
// Frontend
const { predict } = usePredictionStore();

await predict(
  "Top 10 des tendances IA en 2025",
  "tiktok",
  50000 // followers
);

// Résultat
// ✅ 180,000 vues prédites
// ✅ 14,400 likes
// ✅ 72,630€ de revenu estimé
// ✅ ROI: 145,160%
// ✅ Probabilité virale: 70%
```

### 2. Comparer Plateformes

```typescript
const { compare } = useComparisonStore();

await compare("Amazing AI Demo", ["tiktok", "instagram", "youtube"], {
  tiktok: 50000,
  instagram: 75000,
  youtube: 25000,
});

// Résultat
// 🏆 Meilleure plateforme: Instagram (ROI 52,355%)
// 📊 Total: 110,250 vues
// 💰 Total: 44,485€
```

---

## 🛠️ Configuration

### Variables d'Environnement

Copier `.env.example` vers `.env` :

```bash
# LLM API (obligatoire)
GROQ_API_KEY=votre_clé_groq

# Plateformes (optionnel)
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
TIKTOK_ACCESS_TOKEN=...
INSTAGRAM_ACCESS_TOKEN=...
```

### Paramètres ML

Fichier `src/core/config.py` :

```python
model_type: str = "lightgbm"  # ou "ensemble", "production"
viral_threshold: float = 0.7
prediction_confidence: float = 0.8
```

---

## 📚 Documentation Complète

| Document                                                     | Description                     |
| ------------------------------------------------------------ | ------------------------------- |
| [QUICKSTART.md](QUICKSTART.md)                               | Guide de démarrage rapide       |
| [ARCHITECTURE_OOP_ADVANCED.md](ARCHITECTURE_OOP_ADVANCED.md) | Architecture backend détaillée  |
| [frontend/GUIDE_UI_UX.md](frontend/GUIDE_UI_UX.md)           | Guide UI/UX frontend            |
| [docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md)                   | Configuration OAuth plateformes |
| [ROADMAP_SPRINTS.md](ROADMAP_SPRINTS.md)                     | Roadmap développement           |

---

## 🎯 Métriques du Projet

| Composant             | Lignes de Code | Technologies                         |
| --------------------- | -------------- | ------------------------------------ |
| Backend               | ~5,000         | FastAPI, LightGBM, PyTorch           |
| Frontend Architecture | 1,010          | TypeScript OOP (Models, API, Stores) |
| Frontend UI/UX        | 1,700          | React, Framer Motion, Recharts       |
| **Total**             | **~7,700**     | **Fullstack professionnel**          |

---

## ✅ Checklist Fonctionnalités

### Backend ✅

- [x] API REST (16 endpoints)
- [x] Prédiction ML (LightGBM + Ensemble)
- [x] Multi-plateformes (TikTok, Instagram, YouTube, Reddit)
- [x] Génération scripts (Groq LLM)
- [x] MLflow tracking
- [x] Prometheus metrics
- [x] Docker support

### Frontend ✅

- [x] Architecture OOP (Models, Services, Stores)
- [x] Design System (40+ variants)
- [x] Custom Hooks (14 hooks)
- [x] Composants UI avancés (Button, Card, Input, Badge)
- [x] PredictionForm avec platform selector
- [x] PredictionResults avec charts
- [x] Dark/Light mode
- [x] Responsive design
- [x] Animations Framer Motion
- [x] Glassmorphism
- [x] Charts interactifs

---

## 🚀 Déploiement

### Backend (Docker)

```bash
docker-compose up -d
```

### Frontend (Vercel)

```bash
cd frontend
vercel deploy --prod
```

---

## 📝 Licence

Propriétaire - Trend & Viral Engine Pro

---

## 🤝 Support

Pour toute question ou problème :

1. Vérifier [QUICKSTART.md](QUICKSTART.md)
2. Consulter les logs : `logs/backend.log`, `logs/frontend.log`
3. Tester l'API : http://localhost:8000/docs

---

**🎉 Projet Fullstack Complet Prêt à l'Emploi !**

Lancez avec : `./start_fullstack.sh` 🚀
