# 🔐 OAuth Scripts - Token Generation & Validation

Scripts d'aide pour obtenir et valider les tokens OAuth des différentes plateformes.

## 📁 Scripts disponibles

### 🟠 Reddit - `reddit_test_credentials.py`

**Le plus simple - Commencez par ici !**

Test et validation des credentials Reddit.

```bash
# Test vos credentials actuels
python scripts/oauth/reddit_test_credentials.py

# Voir le guide de setup
python scripts/oauth/reddit_test_credentials.py --help
```

**Ce que ça fait** :

- ✅ Teste vos credentials Reddit depuis `.env`
- ✅ Récupère 5 posts de r/python pour valider
- ✅ Affiche un guide de troubleshooting si échec
- ✅ Donne les instructions pour créer une app Reddit

**Durée** : 2-5 minutes

---

### 🎵 TikTok - `tiktok_exchange_token.py`

Échange un authorization code contre un access token.

```bash
# Étape 1: Obtenir le code (ouvrir dans navigateur)
# Le script affichera l'URL complète pour vous

python scripts/oauth/tiktok_exchange_token.py
# → Copie l'URL affichée
# → Ouvre dans navigateur
# → Autorise l'app
# → Copie le 'code=' de l'URL de redirect

# Étape 2: Échanger le code (dans les 10 min!)
python scripts/oauth/tiktok_exchange_token.py VOTRE_CODE_ICI
```

**Ce que ça fait** :

- 🔄 Construit l'URL d'autorisation avec vos credentials
- 🔄 Échange le code contre access_token + refresh_token
- ✅ Teste le token avec l'API TikTok
- 📝 Affiche les valeurs à copier dans `.env`

**Durée** : 10-15 minutes (flow OAuth manuel)

---

### 📘 Facebook - `facebook_long_lived_token.py`

Convertit un token court (1h) en token longue durée (60 jours).

```bash
# Obtenir un short token via Graph API Explorer
# https://developers.facebook.com/tools/explorer/

# Échanger pour long-lived token
python scripts/oauth/facebook_long_lived_token.py EAAD...

# Optionnel: obtenir aussi les Page tokens (jamais expirent)
python scripts/oauth/facebook_long_lived_token.py EAAD... --pages
```

**Ce que ça fait** :

- 🔄 Convertit short token (1h) → long token (60 jours)
- 📄 Optionnel: récupère les Page tokens (permanents)
- ✅ Teste le token avec l'API Facebook
- 📝 Affiche la valeur à copier dans `.env`

**Durée** : 5-10 minutes

---

## 🚀 Quick Start (Ordre recommandé)

### 1️⃣ Reddit (5 min - Facile)

```bash
# Si vous n'avez pas encore d'app Reddit:
# 1. Aller sur https://www.reddit.com/prefs/apps
# 2. Créer une app type "script"
# 3. Copier CLIENT_ID et CLIENT_SECRET dans .env

# Tester
python scripts/oauth/reddit_test_credentials.py
```

**Résultat attendu** :

```
✅ Reddit Authentication SUCCESS!
Collected 5 posts from r/python
```

---

### 2️⃣ TikTok (15 min - Moyen)

```bash
# Lancer le script (affiche l'URL d'auth)
python scripts/oauth/tiktok_exchange_token.py

# Copier l'URL affichée → ouvrir dans navigateur
# Autoriser l'app
# Copier le 'code=' de l'URL redirect

# Échanger le code (< 10 min après l'avoir obtenu!)
python scripts/oauth/tiktok_exchange_token.py aw1y8h7f...
```

**Résultat attendu** :

```
✅ TikTok Access Token obtenu avec succès !
ACCESS_TOKEN: act.abc123...
📝 Ajoutez dans .env:
TIKTOK_ACCESS_TOKEN="act.abc123..."
```

---

### 3️⃣ Facebook (10 min - Moyen)

```bash
# Étape 1: Obtenir short token
# Aller sur: https://developers.facebook.com/tools/explorer/
# Sélectionner votre app
# Get Token → Get User Access Token
# Permissions: pages_read_engagement, pages_show_list, public_profile
# Copier le token (EAAD...)

# Étape 2: Convertir en long-lived
python scripts/oauth/facebook_long_lived_token.py EAAD... --pages
```

**Résultat attendu** :

```
✅ Facebook Long-Lived Token obtenu avec succès !
Expire dans: 5184000 secondes (60 jours)
📝 Remplacez dans .env:
FACEBOOK_ACCESS_TOKEN="EAAD..."
```

---

## ✅ Validation finale

Une fois tous les tokens configurés :

```bash
# Test complet de la pipeline
python scripts/data/test_collection_pipeline.py
```

**Résultat attendu** :

```
📊 SUMMARY
════════════════════════════════════
Success Rate: 4/4 (100%)

✅ Google Trends: 20 samples
✅ Reddit: 100 samples
✅ TikTok: 50 samples
✅ Facebook: 30 samples
```

---

## 📝 Template .env

Après avoir exécuté tous les scripts, votre `.env` devrait ressembler à :

```bash
# === REDDIT ===
REDDIT_CLIENT_ID="VotreClientID14chars"
REDDIT_CLIENT_SECRET="VotreSecret27chars"
REDDIT_USER_AGENT="TrendViralEngine/1.0 by /u/VotreUsername"
ENABLE_REDDIT=true

# === TIKTOK ===
TIKTOK_CLIENT_KEY="aw8qo6cgng..." # Existant
TIKTOK_CLIENT_SECRET="igarmm1yXZ..." # Existant
TIKTOK_ACCESS_TOKEN="act.abc123..." # ← Nouveau (script)
TIKTOK_REFRESH_TOKEN="rft.xyz789..." # ← Nouveau (script)
TIKTOK_ENABLED=true

# === FACEBOOK ===
FACEBOOK_APP_ID="votre_app_id" # Existant
FACEBOOK_APP_SECRET="votre_secret" # Existant
FACEBOOK_ACCESS_TOKEN="EAAD..." # ← Nouveau (script)
FACEBOOK_ENABLED=true

# === GOOGLE TRENDS ===
GOOGLE_TRENDS_ENABLED=true
GOOGLE_TRENDS_REGIONS=["FR","US","GB","CA","MA"]
```

---

## 🆘 Troubleshooting

### Reddit: "401 Unauthorized"

```bash
# Vérifier le type d'app
App type doit être "script" (pas "web app")

# Tester les credentials
python scripts/oauth/reddit_test_credentials.py

# Si échec, recréer l'app sur:
# https://www.reddit.com/prefs/apps
```

### TikTok: "Invalid authorization code"

```bash
# Le code expire en 10 minutes!
# Relancer le flow complet

# Vérifier le redirect URI
# Doit être exactement: http://localhost:8888/callback
```

### Facebook: "Invalid OAuth access token"

```bash
# Token court expiré (1h)
# Retourner sur Graph API Explorer
# Générer un nouveau token
# Relancer le script d'échange
```

---

## 🔄 Renouvellement des tokens

### Reddit

- ✅ Tokens **ne expirent jamais** (sauf révocation)
- Pas besoin de renouveler

### TikTok

- ⚠️ Access token expire (24h généralement)
- ✅ Utilisez le `TIKTOK_REFRESH_TOKEN` pour renouveler automatiquement
- Script de refresh automatique : TODO

### Facebook

- ⚠️ Long-lived token expire en 60 jours
- ⚠️ Page token **ne expire jamais**
- Recommandé: utiliser un Page token (option `--pages`)

---

## 📚 Documentation complète

Voir `docs/OAUTH_SETUP.md` pour :

- Guide détaillé de chaque plateforme
- Permissions OAuth requises
- Scopes et use cases
- Troubleshooting avancé
- Code examples

---

## 🔒 Sécurité

⚠️ **IMPORTANT** :

- ❌ Ne JAMAIS commit `.env` dans git
- ❌ Ne JAMAIS partager vos tokens publiquement
- ✅ `.env` est dans `.gitignore`
- ✅ Tokens stockés localement uniquement
- ✅ Utiliser des variables d'environnement en production

---

## 🎯 Prochaines étapes

Une fois les tokens validés :

1. **Collecter des vraies données** :

   ```bash
   python -m src.services.ingestion.advanced_collector --target 1000
   ```

2. **Extraire les features** :

   ```bash
   python scripts/features/extract_all.py
   ```

3. **Re-entraîner le modèle** :

   ```bash
   python scripts/training/train_ensemble.py
   ```

4. **Démarrer l'API** :
   ```bash
   uvicorn src.api.main:app --reload
   ```

---

**Créé par** : GitHub Copilot (mode autonome expert)  
**Date** : 5 novembre 2025  
**Projet** : Trend & Viral Engine Pro
