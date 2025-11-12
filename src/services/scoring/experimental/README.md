# 🧪 Experimental Models

⚠️ **EXPERIMENTAL** - Not used in production

This folder contains advanced ML models that are **not currently deployed** in the production pipeline. They are kept for research purposes and potential future enhancements.

---

## 📦 Models Included

### 1️⃣ TabNetClassifier

**Deep tabular learning with attention mechanism**

```python
from src.services.scoring.experimental.ensemble_models import TabNetClassifier

model = TabNetClassifier(input_dim=400, output_dim=1)
model.train(X_train, y_train)
predictions = model.predict_proba(X_test)
```

**Requirements**:

- PyTorch ≥ 1.10 (~2GB installation)
- SHAP (explainability)

**Use case**: Complex non-linear feature interactions

**Performance**: Unknown (not benchmarked on real data)

---

### 2️⃣ AutoMLClassifier

**Automated hyperparameter tuning with Optuna**

```python
from src.services.scoring.experimental.ensemble_models import AutoMLClassifier

model = AutoMLClassifier(n_trials=100)
model.train(X_train, y_train)
best_params = model.get_best_params()
```

**Requirements**:

- Optuna ≥ 3.0

**Use case**: Finding optimal model configuration

**Warning**: Very compute-intensive (100 trials × cross-validation)

---

### 3️⃣ StackedEnsembleClassifier

**Multi-layer stacking ensemble**

```python
from src.services.scoring.experimental.ensemble_models import StackedEnsembleClassifier

model = StackedEnsembleClassifier()
model.train(X_train, y_train)
predictions = model.predict_proba(X_test)
```

**Use case**: Meta-learning on base models (LGB, XGB, CatBoost)

**Difference from production ensemble**:

- Production: `EnsembleVotingModel` (simple soft voting)
- Experimental: Multi-layer stacking with meta-learner

---

## 🚀 Installation

**Heavy dependencies** (optional):

```bash
# For TabNet
pip install torch==2.0.0 torchvision torchaudio
pip install shap

# For AutoML
pip install optuna

# All experimental features
pip install -r requirements-experimental.txt
```

⚠️ **Warning**: PyTorch installation is ~2GB and requires GPU for performance.

---

## 📊 Status

| Model                     | Production Ready | Tested   | Performance | Maintenance |
| ------------------------- | ---------------- | -------- | ----------- | ----------- |
| TabNetClassifier          | ❌ No            | ⚠️ Basic | Unknown     | Low         |
| AutoMLClassifier          | ❌ No            | ⚠️ Basic | Slow        | Low         |
| StackedEnsembleClassifier | ❌ No            | ⚠️ Basic | Unknown     | Low         |

**Recommendation**: Use production `EnsembleVotingModel` from `advanced_ensemble.py`

---

## 🔄 Migration to Production

If you want to promote an experimental model to production:

1. **Benchmark on real data**

   - Compare AUC with production ensemble (current: 1.0 overfitted)
   - Measure latency (target: <20ms)
   - Check memory usage (target: <2GB)

2. **Add comprehensive tests**

   - Unit tests (coverage ≥85%)
   - Integration tests
   - Property-based tests

3. **Document thoroughly**

   - API documentation
   - Performance characteristics
   - Failure modes

4. **Update ScoringService**

   - Add model loading logic in `service.py`
   - Add feature flag in `config.py`
   - Ensure backward compatibility

5. **Deploy gradually**
   - A/B test (5% → 50% → 100%)
   - Monitor metrics closely
   - Have rollback plan ready

---

## 📝 Usage in Tests

Currently used **only** in:

- `scripts/test_ml_components.py:25`

Example:

```python
from src.services.scoring.experimental.ensemble_models import TabNetClassifier

# Basic usage
model = TabNetClassifier()
# ... testing code ...
```

---

## ⚠️ Important Notes

1. **Not Production-Ready**: These models have minimal testing and no production deployment
2. **Heavy Dependencies**: PyTorch adds ~2GB to installation
3. **Maintenance**: Low priority, may become outdated
4. **Performance**: Unknown on real viral trends data
5. **Documentation**: Basic only, not comprehensive

**For production viral prediction, use**:

```python
from src.services.scoring.advanced_ensemble import EnsembleVotingModel  # ✅ Production
```

---

**Last Updated**: 6 Novembre 2025  
**Maintainer**: Trend & Viral Engine Team  
**Status**: Archived / Experimental
