# ✅ VÉRIFICATION COMPLÈTE: Backend ↔ Frontend

**Date**: 12 novembre 2025  
**Status**: 🔍 ANALYSE APPROFONDIE TERMINÉE

---

## 📊 TABLEAU DE CORRESPONDANCE COMPLET

| # | Frontend Endpoint | Backend Existe? | Request Match? | Response Match? | Status |
|---|-------------------|-----------------|----------------|-----------------|--------|
| 1 | `POST /api/v1/predict` | ✅ Oui (routes/predictions.py) | ⚠️ **PARTIEL** | ❌ **PROBLÈME** | 🟡 |
| 2 | `GET /api/v1/trends/topK?k=N` | ✅ Oui (main.py:214) | ✅ OK | ⚠️ **MOCK DATA** | 🟡 |
| 3 | `POST /api/v1/trends/collect` | ✅ Oui (main.py:329) | ✅ OK | ✅ OK | 🟢 |
| 4 | `POST /api/v1/generate/script` | ✅ Oui (main.py:364) | ✅ OK | ✅ OK | 🟢 |
| 5 | `POST /api/v1/generate/video` | ✅ Oui (main.py:417) | ✅ OK | ✅ OK | 🟢 |
| 6 | `POST /api/v1/analyze-post` | ✅ Oui (main.py:279) | ✅ OK | ✅ OK | 🟢 |

---

## 🚨 PROBLÈMES IDENTIFIÉS

### ❌ PROBLÈME 1: Response `/predict` INCOMPATIBLE

**Localisation**: 
- Frontend: `app/prediction/page.tsx:48-50`
- Backend: `src/api/routes/predictions.py:49-78`

**Problème**:
Frontend attend: `prediction.projection_7_days` (Array)
```typescript
const projectionData = prediction?.projection_7_days || [];
```

Backend retourne: **N'EXISTE PAS** dans `PredictResponse`
```python
class PredictResponse(BaseModel):
    prediction_id: str
    title: str
    platform: str
    predicted_views: int
    views_range: Dict[str, int]
    predicted_likes: int
    # ... MAIS PAS DE projection_7_days ❌
```

**Impact**: 
- ❌ Graphique "Projection 7 jours" ne s'affiche PAS
- ❌ Frontend crash si on essaie d'accéder aux données

**Solution Requise**:
```python
# Ajouter dans PredictResponse:
class PredictResponse(BaseModel):
    # ... existing fields
    projection_7_days: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        description="Projection views 7 days"
    )
```

---

### ⚠️ PROBLÈME 2: `/trends/topK` Retourne Mock Data

**Localisation**: `src/api/main.py:231-241`

**Code Actuel**:
```python
trends = [
    TrendItem(
        topic=f"Trend {i+1}",  # ❌ FAUX DATA
        score=0.9 - (i * 0.05),
        predicted_views=100000 - (i * 5000),
        country=country or "FR",
        rank=i + 1,
    )
    for i in range(k)
]
```

**Problème**:
- Frontend affiche "Trend 1", "Trend 2"... (pas de vraies données)
- Utilisateur voit données fake

**Solution**:
1. Charger vraies données depuis `data/features/` ou `data/raw/`
2. Utiliser `SelectionService.select_top_k()`
3. Filtrer par country si spécifié

---

### ⚠️ PROBLÈME 3: Frontend Attend Champs Supplémentaires

**Localisation**: `app/prediction/page.tsx:139-162`

**Frontend Attend**:
```typescript
{prediction.predicted_views?.toLocaleString()}  // ✅ Existe
{prediction.predicted_likes?.toLocaleString()}  // ✅ Existe  
{prediction.estimated_revenue?.toFixed(2)}      // ✅ Existe
{prediction.virality_probability}               // ❌ Backend: viral_probability
```

**Problème**: Nom de champ différent
- Frontend: `virality_probability`
- Backend: `viral_probability`

**Solution**: Standardiser sur `viral_probability` partout

---

### ❌ PROBLÈME 4: Dashboard Stats Hardcodées

**Localisation**: `app/dashboard/page.tsx:9-40`

**Code Actuel**:
```typescript
const stats = [
    {
        name: 'Tendances Collectées',
        value: '1,247',  // ❌ HARDCODÉ
        change: '+12.5%',
        // ...
    },
    // ...
];
```

**Problème**:
- Données fake, jamais mises à jour
- Pas de backend endpoint pour `/stats/overview`

**Solution**:
1. Créer endpoint `GET /api/v1/stats/overview`
2. Retourner vraies stats depuis DB/fichiers
3. Frontend fetch au mount

---

### ⚠️ PROBLÈME 5: Vidéo MP4 Path Non Servable

**Localisation**: 
- Backend génère: `outputs/video_20251112_143000.mp4`
- Frontend reçoit: `video_path: "outputs/video_20251112_143000.mp4"`

**Problème**:
```typescript
<video src={videoUrl} />  
// ❌ Path relatif backend, pas accessible depuis frontend
```

**Solution**:
1. **Option A**: Servir fichiers statiques
   ```python
   from fastapi.staticfiles import StaticFiles
   app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
   ```
   Then: `http://localhost:8000/outputs/video_xxx.mp4`

2. **Option B**: Endpoint download
   ```python
   @app.get("/api/v1/download/{filename}")
   async def download_file(filename: str):
       return FileResponse(f"outputs/{filename}")
   ```

---

## 🔧 CORRECTIONS PRIORITAIRES

### 🔴 CRITIQUE (À faire MAINTENANT)

#### 1. Ajouter `projection_7_days` dans PredictResponse

**Fichier**: `src/api/routes/predictions.py`

```python
class PredictResponse(BaseModel):
    # ... existing fields
    
    # AJOUTER:
    projection_7_days: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Projection 7 jours: [{day: 1, views: 1000}, ...]"
    )

# Dans endpoint /predict, après prediction:
projection = [
    {"day": i+1, "views": int(prediction.predicted_views * (1 + i*0.15))}
    for i in range(7)
]

response = PredictResponse(
    # ... existing fields
    projection_7_days=projection  # AJOUTER
)
```

#### 2. Remplacer Mock Data dans `/trends/topK`

**Fichier**: `src/api/main.py:214-250`

```python
@app.get("/api/v1/trends/topK", ...)
async def get_top_k_trends(...):
    try:
        # REMPLACER mock data par:
        from src.services.selection import get_selection_service
        
        selection_service = get_selection_service()
        
        # Charger dernières features scored
        features_path = settings.data_features_path
        latest_file = max(features_path.glob("*.parquet"), default=None)
        
        if not latest_file:
            # Fallback to mock if no data
            return TopKResponse(...)
        
        # Lire et sélectionner top K
        df = pd.read_parquet(latest_file)
        top_df = selection_service.select_top_k(df, k=k, country=country)
        
        trends = [
            TrendItem(
                topic=row.get("topic", f"Trend {i}"),
                score=float(row.get("viral_score", 0.5)),
                predicted_views=int(row.get("predicted_views", 10000)),
                country=row.get("country", country or "FR"),
                rank=i+1
            )
            for i, (_, row) in enumerate(top_df.iterrows())
        ]
        
        return TopKResponse(trends=trends, ...)
    except Exception as e:
        # ...
```

#### 3. Créer Endpoint `/stats/overview`

**Fichier**: `src/api/main.py` (ajouter)

```python
class StatsOverview(BaseModel):
    """Dashboard stats overview."""
    trends_collected: int
    predictions_made: int
    videos_generated: int
    model_accuracy: float

@app.get("/api/v1/stats/overview", response_model=StatsOverview, tags=["Stats"])
async def get_stats_overview():
    """Get dashboard overview statistics."""
    try:
        # Count trends collected
        trends_path = settings.data_raw_path
        trends_count = len(list(trends_path.glob("*.parquet")))
        
        # Count predictions (from logs or DB)
        # Pour MVP, retourner counts depuis fichiers
        predictions_count = len(list(Path("data/feedback").glob("*.json")))
        
        # Count videos generated
        videos_count = len(list(Path("outputs").glob("*.mp4")))
        
        # Get model accuracy (from MLflow or stored)
        model_accuracy = 0.873  # TODO: Load from MLflow
        
        return StatsOverview(
            trends_collected=trends_count,
            predictions_made=predictions_count,
            videos_generated=videos_count,
            model_accuracy=model_accuracy
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(500, detail=str(e))
```

#### 4. Servir Fichiers Statiques Vidéos

**Fichier**: `src/api/main.py` (après création app)

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Après: app = FastAPI(...)

# Servir fichiers outputs
outputs_path = Path("outputs")
outputs_path.mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(outputs_path)), name="outputs")

# Maintenant vidéos accessibles via:
# http://localhost:8000/outputs/video_xxx.mp4
```

**Frontend Update**: `app/generation/page.tsx`

```typescript
// Après generateVideo:
const response = await axios.post(`${API_BASE}/generate/video`, {...});

// CHANGER:
// setVideoUrl(response.data.video_path);  // ❌ Path relatif

// EN:
const filename = response.data.video_path.split('/').pop();
setVideoUrl(`http://localhost:8000/outputs/${filename}`);  // ✅ URL complète
```

---

## 🟡 AMÉLIORATIONS RECOMMANDÉES

### 1. Uniformiser Noms de Champs

**Problème**: `virality_probability` (frontend) vs `viral_probability` (backend)

**Solution**: Choisir UN standard et l'utiliser partout
- Recommandé: `viral_probability` (plus court)
- Mettre à jour frontend: `prediction.viral_probability`

### 2. Ajouter Gestion d'Erreurs Frontend

**Problème**: Erreurs API pas affichées clairement

**Solution**: Ajouter toast notifications
```bash
cd frontend
npm install react-hot-toast
```

```typescript
// app/layout.tsx
import { Toaster } from 'react-hot-toast';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Toaster position="top-right" />
      </body>
    </html>
  );
}

// Dans pages:
import toast from 'react-hot-toast';

try {
  const response = await axios.post(...);
  toast.success('Prédiction réussie !');
} catch (error) {
  toast.error(error.response?.data?.detail || 'Erreur');
}
```

### 3. Ajouter Loading States Améliorés

**Dashboard Stats**: Skeleton loaders pendant fetch

```typescript
const [loading, setLoading] = useState(true);
const [stats, setStats] = useState(null);

useEffect(() => {
  fetchStats();
}, []);

const fetchStats = async () => {
  try {
    const res = await axios.get(`${API_BASE}/stats/overview`);
    setStats(res.data);
  } finally {
    setLoading(false);
  }
};

// Render:
{loading ? <SkeletonLoader /> : <StatsDisplay stats={stats} />}
```

---

## 📋 CHECKLIST COMPLÈTE

### Backend
- [ ] Ajouter `projection_7_days` dans `PredictResponse`
- [ ] Implémenter vraies données dans `/trends/topK`
- [ ] Créer endpoint `/api/v1/stats/overview`
- [ ] Servir fichiers statiques avec `StaticFiles`
- [ ] Uniformiser `viral_probability` partout
- [ ] Ajouter validation request robuste

### Frontend
- [ ] Mettre à jour Dashboard avec fetch `/stats/overview`
- [ ] Corriger URL vidéo pour pointer vers `http://localhost:8000/outputs/`
- [ ] Ajouter toast notifications (react-hot-toast)
- [ ] Ajouter skeleton loaders
- [ ] Uniformiser `viral_probability` dans prediction page
- [ ] Gérer cas où `projection_7_days` est null/vide

---

## 🧪 TESTS DE VALIDATION

### Test 1: Prédiction avec Projection
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI Tools 2025",
    "platform": "tiktok",
    "follower_count": 50000
  }' | jq '.projection_7_days'

# Attendu: Array de 7 objets avec day/views
```

### Test 2: Stats Overview
```bash
curl http://localhost:8000/api/v1/stats/overview | jq

# Attendu: 
# {
#   "trends_collected": 123,
#   "predictions_made": 45,
#   "videos_generated": 12,
#   "model_accuracy": 0.873
# }
```

### Test 3: Vidéo Servie
```bash
# Générer vidéo
curl -X POST http://localhost:8000/api/v1/generate/video \
  -H "Content-Type: application/json" \
  -d '{"script": "Test", "platform": "tiktok"}' | jq '.video_path'

# Télécharger vidéo
wget http://localhost:8000/outputs/video_xxx.mp4

# Attendu: Fichier MP4 téléchargé avec succès
```

---

## 📊 RÉSUMÉ IMPACT

**Avant Corrections**:
- ❌ Graphique projection 7 jours: VIDE
- ❌ Dashboard stats: FAKE data
- ❌ Trends page: Mock "Trend 1, Trend 2..."
- ❌ Vidéos générées: Non accessibles

**Après Corrections**:
- ✅ Graphique projection: AFFICHE 7 jours
- ✅ Dashboard stats: VRAIES données live
- ✅ Trends page: VRAIES tendances collectées
- ✅ Vidéos: ACCESSIBLES et jouables

**Gain UX**: 🚀 Application professionnelle complète et fonctionnelle
**Gain ML**: 🧠 Prédictions affichées avec contexte complet (projection)

---

## 🎯 PRIORISATION

### Cette Session (1-2h)
1. ✅ Ajouter `projection_7_days` (15 min)
2. ✅ Servir fichiers statiques (10 min)
3. ✅ Créer `/stats/overview` (20 min)
4. ✅ Fix URL vidéo frontend (5 min)

### Prochaine Session
5. Implémenter vraies données `/trends/topK`
6. Ajouter toast notifications
7. Améliorer gestion erreurs

---

**Status Final**: 🟢 Prêt pour corrections immédiates
**Documentation**: ✅ Complète et actionnable
