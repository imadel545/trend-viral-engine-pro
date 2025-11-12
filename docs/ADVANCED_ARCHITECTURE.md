# 🚀 Architecture ML/DL Ultra-Avancée - Trend & Viral Engine Pro

**Date**: 3 novembre 2025  
**Status**: Production-Ready avec algorithmes state-of-the-art

---

## 📊 Vue d'ensemble

Cette architecture implémente les **meilleures pratiques ML/DL du monde** pour la prédiction de contenus viraux avec un taux de précision de classe mondiale (AUC cible ≥ 0.90).

### Stack Technique

```
┌─────────────────────────────────────────────────────────────┐
│  FEATURE ENGINEERING (Advanced Extractors)                  │
├─────────────────────────────────────────────────────────────┤
│  • Wavelet Transform (PyWavelets)                           │
│  • Fourier Transform (FFT)                                  │
│  • TSFresh (Comprehensive Time Series)                      │
│  • Multimodal Embeddings (CLIP + Sentence-Transformers)     │
│  • Graph Features (NetworkX)                                │
│  • Meta-Features (Higher-order statistics)                  │
│  • Cross-Features (Polynomial interactions)                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ENSEMBLE MODELS (Stacked)                                  │
├─────────────────────────────────────────────────────────────┤
│  Base Models:                                               │
│  • LightGBM (Gradient Boosting)                             │
│  • XGBoost (Extreme Gradient Boosting)                      │
│  • CatBoost (Categorical Boosting)                          │
│  • TabNet (Deep Tabular - optional)                         │
│                                                             │
│  Meta-Learner:                                              │
│  • Logistic Regression / LightGBM                           │
│  • Isotonic Calibration                                     │
│                                                             │
│  AutoML:                                                    │
│  • Optuna Hyperparameter Optimization                       │
│  • TPE Sampler (Tree-structured Parzen Estimator)          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  SELECTION ALGORITHMS (Advanced)                            │
├─────────────────────────────────────────────────────────────┤
│  • DPP (Determinantal Point Process)                        │
│  • Thompson Sampling (Bayesian Bandits)                     │
│  • LinUCB (Contextual Bandits)                              │
│  • Multi-Objective Optimization (Pareto)                    │
│  • Hybrid Ensemble (Voting)                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  EXPLAINABILITY & MONITORING                                │
├─────────────────────────────────────────────────────────────┤
│  • SHAP (Feature Importance)                                │
│  • Evidently (Drift Detection)                              │
│  • A/B Testing Framework                                    │
│  • Production Monitoring (Latency, AUC, Error Rate)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Composants Critiques

### 1. Feature Engineering Ultra-Avancé

#### 1.1 Wavelet Transform
**Fichier**: `src/services/features/advanced_extractors.py` → `WaveletFeatureExtractor`

**Objectif**: Analyse temps-fréquence pour détecter patterns temporels complexes

**Features extraites**:
- Coefficients wavelet multi-échelles (Daubechies db4)
- Statistiques par niveau: mean, std, energy, entropy
- 3 niveaux de décomposition → ~16 features

**Usage**:
```python
extractor = WaveletFeatureExtractor(wavelet='db4', levels=3)
df_enriched = extractor.extract(df)
```

#### 1.2 Fourier Transform
**Fichier**: `src/services/features/advanced_extractors.py` → `FourierFeatureExtractor`

**Objectif**: Extraction de composantes fréquentielles dominantes

**Features extraites**:
- Top 10 magnitudes FFT
- Top 10 phases FFT
- Détection de périodicités

**Usage**:
```python
extractor = FourierFeatureExtractor(n_components=10)
df_enriched = extractor.extract(df)
```

#### 1.3 TSFresh
**Fichier**: `src/services/features/advanced_extractors.py` → `TSFreshFeatureExtractor`

**Objectif**: Extraction automatique de 100+ features time series

**Features extraites**:
- Statistical moments (mean, variance, skewness, kurtosis)
- Absolute sum of changes
- Longest strike above mean
- Auto-correlation features

**Usage**:
```python
extractor = TSFreshFeatureExtractor(minimal=True)
df_enriched = extractor.extract(df)
```

#### 1.4 Multimodal Embeddings
**Fichier**: `src/services/features/advanced_extractors.py` → `MultimodalEmbeddingExtractor`

**Objectif**: Représentations vectorielles denses pour texte et images

**Modèles utilisés**:
- **Texte**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dims)
- **Vision**: `openai/clip-vit-base-patch32` (512 dims) - optionnel

**Usage**:
```python
extractor = MultimodalEmbeddingExtractor()
df_enriched = extractor.extract_text_embeddings(df)
```

#### 1.5 Graph Features
**Fichier**: `src/services/features/advanced_extractors.py` → `GraphFeatureExtractor`

**Objectif**: Capturer relations entre topics

**Features extraites**:
- PageRank (influence globale)
- Betweenness centrality (rôle de pont)
- Closeness centrality (proximité aux autres)
- Degree centrality (nombre de connexions)

**Usage**:
```python
extractor = GraphFeatureExtractor(window_size=24)
df_enriched = extractor.extract(df)
```

#### 1.6 Meta-Features
**Fichier**: `src/services/features/advanced_extractors.py` → `MetaFeatureExtractor`

**Objectif**: Features sur features (statistiques d'ordre supérieur)

**Features extraites**:
- Mean/std/min/max/median/IQR des features numériques
- Sparsity (proportion de zéros)

#### 1.7 Cross-Features
**Fichier**: `src/services/features/advanced_extractors.py` → `CrossFeatureExtractor`

**Objectif**: Capturer interactions non-linéaires

**Features extraites**:
- Produits croisés (slope × acceleration)
- Ratios (slope / acceleration)
- Polynômes (slope²)

---

### 2. Ensemble Models

#### 2.1 Stacked Ensemble
**Fichier**: `src/services/scoring/ensemble_models.py` → `StackedEnsembleClassifier`

**Architecture**:
```
Input Features
     ↓
┌─────────┬─────────┬──────────┬─────────┐
│ LightGBM│ XGBoost │ CatBoost │ TabNet  │ ← Base Models
└────┬────┴────┬────┴─────┬────┴────┬────┘
     │         │          │         │
     └─────────┴──────────┴─────────┘
              ↓
     [Predictions Stack]
              ↓
     Logistic Regression  ← Meta-Learner
              ↓
     Isotonic Calibration
              ↓
        Final Prediction
```

**Hyperparamètres optimisés**:
- **LightGBM**: num_leaves=31, learning_rate=0.05, max_depth=7
- **XGBoost**: max_depth=7, eta=0.05, subsample=0.8
- **CatBoost**: depth=7, learning_rate=0.05, l2_leaf_reg=3

**Performance attendue**:
- AUC: 0.85-0.92 (selon qualité des données)
- Latence: ~50ms par batch de 100 prédictions

**Usage**:
```python
from src.services.scoring.enhanced_service import get_enhanced_scoring_service

service = get_enhanced_scoring_service()

# Training
metrics = service.train_ensemble(
    X_train, y_train,
    use_lightgbm=True,
    use_xgboost=True,
    use_catboost=True,
    use_tabnet=False,  # GPU recommended
)

# Prediction
results = service.score(X_test, explain=True)
```

#### 2.2 AutoML avec Optuna
**Fichier**: `src/services/scoring/ensemble_models.py` → `AutoMLClassifier`

**Objectif**: Optimisation automatique des hyperparamètres

**Algorithme**: Tree-structured Parzen Estimator (TPE)

**Paramètres optimisés** (LightGBM):
- boosting_type: gbdt, dart
- num_leaves: 20-100
- learning_rate: 0.01-0.1 (log scale)
- max_depth: 5-15
- feature_fraction, bagging_fraction: 0.6-1.0
- L1/L2 regularization: 1e-8 to 10.0 (log scale)

**Usage**:
```python
service = get_enhanced_scoring_service()

results = service.train_automl(
    X_train, y_train,
    n_trials=50,      # 50 essais
    timeout=3600,     # 1 heure max
)

print(f"Best AUC: {results['best_auc']:.4f}")
print(f"Best params: {results['best_params']}")
```

---

### 3. Selection Algorithms

#### 3.1 DPP (Determinantal Point Process)
**Fichier**: `src/services/selection/advanced_selectors.py` → `DPPSelector`

**Objectif**: Sélection diverse maximisant le déterminant de la matrice de kernel

**Formule**:
```
L = diag(q) * K * diag(q)
```
où:
- `q` = quality scores (p_breakout_24h normalisé)
- `K` = similarity kernel (RBF sur embeddings)

**Avantages**:
- Garantit diversité via propriétés du déterminant
- Balance qualité et diversité
- Évite redondance de contenu

**Usage**:
```python
selector = DPPSelector(kernel_type="rbf", gamma=1.0)
selected = selector.select(scored_df, k=10, embedding_cols=['text_emb_0', 'text_emb_1', ...])
```

#### 3.2 Thompson Sampling
**Fichier**: `src/services/selection/advanced_selectors.py` → `ThompsonSamplingSelector`

**Objectif**: Exploration-exploitation Bayésienne

**Algorithme**:
1. Maintenir distribution Beta(α, β) pour chaque topic
2. Sampler une valeur aléatoire de chaque Beta
3. Sélectionner topics avec samples les plus élevés
4. Update distributions avec feedback

**Avantages**:
- Exploration optimale (Thompson Sampling est optimal)
- S'adapte au feedback en temps réel
- Converge vers meilleurs choix

**Usage**:
```python
selector = ThompsonSamplingSelector(alpha_prior=1.0, beta_prior=1.0)
selected = selector.select(scored_df, k=10)

# Update avec feedback
selector.update(topic="crypto", success=True)
```

#### 3.3 LinUCB (Contextual Bandits)
**Fichier**: `src/services/selection/advanced_selectors.py` → `LinUCBSelector`

**Objectif**: Bandits contextuels avec Upper Confidence Bound

**Formule**:
```
UCB(x) = θᵀx + α * √(xᵀA⁻¹x)
```
où:
- `θ` = paramètres estimés
- `x` = features contextuelles (embeddings)
- `A` = design matrix
- `α` = coefficient d'exploration

**Avantages**:
- Personnalisation basée sur contexte
- Confidence bounds théoriques
- Convergence garantie

**Usage**:
```python
selector = LinUCBSelector(alpha=1.0, dim=10)
selected = selector.select(scored_df, k=10, context_cols=['text_emb_0', ...])

# Update avec contexte et reward
selector.update(context=np.array([...]), reward=1.0)
```

#### 3.4 Multi-Objective
**Fichier**: `src/services/selection/advanced_selectors.py` → `MultiObjectiveSelector`

**Objectif**: Optimiser plusieurs objectifs simultanément (score ET views)

**Algorithme**: Pareto frontier

**Avantages**:
- Optimise plusieurs KPIs
- Trouve solutions non-dominées
- Permet trade-offs configurables

**Usage**:
```python
selector = MultiObjectiveSelector(
    objectives=["p_breakout_24h", "predicted_views_24h"],
    weights=[0.6, 0.4]
)
selected = selector.select(scored_df, k=10)
```

#### 3.5 Hybrid Selector
**Fichier**: `src/services/selection/advanced_selectors.py` → `HybridSelector`

**Objectif**: Combiner plusieurs stratégies par voting

**Algorithme**:
1. Exécuter chaque stratégie indépendamment
2. Voter avec poids configurables
3. Sélectionner items avec votes les plus élevés

**Usage**:
```python
selector = HybridSelector(
    use_dpp=True,
    use_thompson=True,
    use_multi_objective=True,
    strategy_weights={
        'dpp': 0.4,
        'thompson': 0.3,
        'multi_objective': 0.3,
    }
)
selected = selector.select(scored_df, k=10)
```

---

### 4. Explainability & Monitoring

#### 4.1 SHAP Explainer
**Fichier**: `src/services/monitoring/explainability.py` → `SHAPExplainer`

**Objectif**: Interpréter prédictions du modèle

**Features**:
- TreeExplainer pour LightGBM/XGBoost/CatBoost (rapide)
- KernelExplainer pour ensemble (plus lent)
- Feature importance globale
- Explication par instance

**Usage**:
```python
explainer = SHAPExplainer(model, model_type="ensemble")
explainer.fit(X_background, max_samples=100)

# Global explanations
explanations = explainer.explain(X_test, max_samples=10)
print(explanations['feature_importance'])

# Instance explanation
instance_exp = explainer.explain_instance(X_test.iloc[0], feature_names=X.columns)
print(instance_exp['explanation'])
```

#### 4.2 Drift Detection
**Fichier**: `src/services/monitoring/explainability.py` → `DriftDetector`

**Objectif**: Détecter drift dans données ou target

**Méthodes**:
- Data Drift (Evidently)
- Target Drift
- Data Quality metrics

**Usage**:
```python
detector = DriftDetector(reference_data=X_train)

drift_report = detector.detect_data_drift(
    current_data=X_production,
    output_path=Path("drift_report.html")
)

print(f"Drifted features: {drift_report['n_drifted_features']}")
print(f"Features: {drift_report['drifted_features']}")
```

#### 4.3 A/B Testing
**Fichier**: `src/services/monitoring/explainability.py` → `ABTestFramework`

**Objectif**: Comparer modèles en production

**Features**:
- Assignation déterministe (hash-based)
- Analyse statistique (t-test)
- Calcul effet size (Cohen's d)
- Confidence intervals

**Usage**:
```python
ab_test = ABTestFramework()

# Create experiment
ab_test.create_experiment(
    experiment_id="model_v2_vs_v1",
    variant_a="model_v1",
    variant_b="model_v2",
    traffic_split=0.5
)

# Assign users
variant = ab_test.assign_variant("model_v2_vs_v1", user_id="user123")

# Record results
ab_test.record_result("model_v2_vs_v1", variant, metric_value=0.85)

# Analyze
analysis = ab_test.analyze_experiment("model_v2_vs_v1")
print(f"Winner: {analysis['winner']}")
print(f"Lift: {analysis['lift']:.2f}%")
```

#### 4.4 Production Monitoring
**Fichier**: `src/services/monitoring/explainability.py` → `ProductionMonitor`

**Métriques trackées**:
- Latency (p50, p95, p99)
- AUC (avec feedback)
- Error rate
- Throughput

**Alertes**:
- AUC drop > 5%
- Latency > 500ms
- Error rate > 1%

**Usage**:
```python
monitor = ProductionMonitor(metrics_path=Path("data/metrics"))

# Log prediction
monitor.log_prediction(
    prediction_id="pred_123",
    features={"slope": 0.5, "views": 1000},
    prediction=0.85,
    latency_ms=45.2
)

# Log feedback
monitor.log_feedback(
    prediction_id="pred_123",
    actual_outcome=True
)

# Compute metrics
metrics = monitor.compute_metrics()
alerts = monitor.check_alerts(metrics)
```

---

## 🔧 Workflow Complet

### Étape 1: Extraction de Features
```bash
python scripts/training/train_advanced.py --model features
```

### Étape 2: Entraînement Ensemble
```bash
python scripts/training/train_advanced.py --model ensemble
```

### Étape 3: Optimisation AutoML (optionnel)
```bash
python scripts/training/train_advanced.py --model automl --n-trials 100 --timeout 7200
```

### Étape 4: Utilisation en Production
```python
from src.services.features.enhanced_service import get_enhanced_feature_service
from src.services.scoring.enhanced_service import get_enhanced_scoring_service
from src.services.selection.enhanced_service import get_enhanced_selection_service

# Extract features
feature_service = get_enhanced_feature_service()
df_features = feature_service.process_raw_data(raw_path, save=False)

# Score
scoring_service = get_enhanced_scoring_service()
df_scored = scoring_service.score(df_features, explain=True)

# Select top K
selection_service = get_enhanced_selection_service()
selected = selection_service.select_top_k(
    df_scored,
    k=10,
    strategy="hybrid"
)

# Get recommendations
recommendations = selection_service.get_recommendations(df_scored)
```

---

## 📈 Performance Attendue

| Métrique | Baseline | Avancé | Classe Mondiale |
|----------|----------|--------|-----------------|
| **AUC** | 0.75-0.80 | 0.85-0.90 | **0.90-0.95** |
| **Precision@10** | 0.60 | 0.75 | **0.85** |
| **Diversity Score** | 0.40 | 0.65 | **0.75** |
| **Latency (ms)** | 100 | 50 | **< 30** |

---

## 🚦 Prochaines Étapes

### Améliorations Court Terme
1. ✅ Collecter ≥ 500 samples labellisés
2. ✅ Entraîner ensemble complet
3. ⏳ A/B test en production
4. ⏳ Monitoring drift

### Améliorations Long Terme
1. 🔄 Temporal Fusion Transformer (forecasting)
2. 🔄 GNN pour relations topic avancées
3. 🔄 Active learning pour labellisation efficace
4. 🔄 Reinforcement Learning pour optimisation continue

---

## 📚 Références

- **DPP**: Kulesza & Taskar (2012) - "Determinantal Point Processes for Machine Learning"
- **Thompson Sampling**: Chapelle & Li (2011) - "An Empirical Evaluation of Thompson Sampling"
- **LinUCB**: Li et al. (2010) - "A Contextual-Bandit Approach to Personalized News Article Recommendation"
- **SHAP**: Lundberg & Lee (2017) - "A Unified Approach to Interpreting Model Predictions"
- **Ensemble Methods**: Zhou (2012) - "Ensemble Methods: Foundations and Algorithms"

---

**Auteur**: Trend & Viral Engine Pro Team  
**Version**: 1.0.0  
**Dernière mise à jour**: 3 novembre 2025
