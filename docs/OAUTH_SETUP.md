# 🔐 OAuth Setup Guide - Trend & Viral Engine Pro

Guide complet pour configurer l'authentification OAuth avec les différentes plateformes de données.

---

## 📋 Vue d'ensemble

Ce guide vous permettra de collecter de **vraies données** depuis:

- ✅ **Reddit** (r/all, r/videos, r/funny, etc.)
- ✅ **TikTok** (trending, hashtags)
- ✅ **Facebook Graph API** (pages publiques, trending topics)
- ✅ **YouTube** (trending videos)

---

## 🔴 Reddit OAuth Setup

### Étape 1: Créer une application Reddit

1. **Connectez-vous** à Reddit: https://www.reddit.com
2. **Accédez aux apps**: https://www.reddit.com/prefs/apps
3. **Cliquez** sur "create another app..." (en bas de page)
4. **Remplissez le formulaire**:
   ```
   name:         Trend Engine Pro
   type:         script
   description:  ML trend detection engine
   about url:    (laisser vide)
   redirect uri: http://localhost:8080
   ```
5. **Cliquez** sur "create app"

### Étape 2: Récupérer les credentials

Vous verrez:

```
personal use script
<CLIENT_ID>           <- 14 caractères sous "personal use script"

secret
<CLIENT_SECRET>       <- ~27 caractères
```

### Étape 3: Configurer .env

Ajoutez dans `.env`:

```bash
REDDIT_CLIENT_ID=votre_client_id_14_chars
REDDIT_CLIENT_SECRET=votre_secret_27_chars
REDDIT_USER_AGENT=Trend Engine Pro/1.0 by /u/votre_username
```

### Étape 4: Tester la connexion

```bash
python << 'EOF'
import praw
import os
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# Test: récupérer top 5 posts de r/all
for submission in reddit.subreddit("all").hot(limit=5):
    print(f"✅ {submission.title[:50]}... ({submission.score} upvotes)")

print("\n✅ Reddit OAuth OK!")
EOF
```

### Limites Rate Limiting

- **60 requêtes/minute** (script type)
- **100 requêtes/minute** (web app type)
- Utiliser `praw` qui gère automatiquement le rate limiting

---

## 🎵 TikTok API Setup

### Étape 1: Créer un compte développeur

1. **Inscrivez-vous**: https://developers.tiktok.com/
2. **Créez une app**: https://developers.tiktok.com/apps
3. **Remplissez**:
   ```
   App Name:    Trend Engine Pro
   Type:        Research & Academic
   Category:    Data Analytics
   ```

### Étape 2: OAuth 2.0 Flow

TikTok utilise **OAuth 2.0 Authorization Code Flow**:

```python
# 1. Rediriger utilisateur vers URL d'autorisation
auth_url = (
    "https://www.tiktok.com/auth/authorize/"
    f"?client_key={CLIENT_KEY}"
    "&scope=user.info.basic,video.list"
    "&response_type=code"
    "&redirect_uri=http://localhost:8080/callback"
)
print(f"Visitez: {auth_url}")

# 2. Après autorisation, récupérer le code dans l'URL
code = input("Entrez le code: ")

# 3. Échanger le code contre un access token
import requests
token_response = requests.post(
    "https://open-api.tiktok.com/oauth/access_token/",
    params={
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }
)
access_token = token_response.json()["data"]["access_token"]
```

### Étape 3: Configurer .env

```bash
TIKTOK_CLIENT_KEY=votre_client_key
TIKTOK_CLIENT_SECRET=votre_secret
TIKTOK_ACCESS_TOKEN=votre_access_token  # Expire après 24h
```

### Étape 4: Refresh Token

Les tokens TikTok expirent après **24h**. Automatiser le refresh:

```python
def refresh_tiktok_token(refresh_token: str) -> str:
    response = requests.post(
        "https://open-api.tiktok.com/oauth/refresh_token/",
        params={
            "client_key": os.getenv("TIKTOK_CLIENT_KEY"),
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
    )
    return response.json()["data"]["access_token"]
```

### Limites Rate Limiting

- **100 requêtes/jour** (niveau gratuit)
- **1000 requêtes/jour** (niveau développeur vérifié)

---

## 📘 Facebook Graph API Setup

### Étape 1: Créer une app Facebook

1. **Accédez**: https://developers.facebook.com/
2. **Créez une app**: "My Apps" > "Create App"
3. **Type**: Business
4. **Nom**: Trend Engine Pro

### Étape 2: Ajouter le produit "Pages"

1. Dans le dashboard de votre app
2. **Add Product** > **Facebook Login**
3. **Paramètres** > Valid OAuth Redirect URIs: `http://localhost:8080/callback`

### Étape 3: Générer un Access Token

**Option A - User Access Token (courte durée)**:

1. **Graph API Explorer**: https://developers.facebook.com/tools/explorer/
2. **Sélectionnez** votre app
3. **Permissions**: `pages_read_engagement`, `pages_show_list`
4. **Generate Access Token**
5. **Copiez** le token (expire après 1-2h)

**Option B - Page Access Token (longue durée)**:

```bash
# 1. Échanger User Token contre Long-Lived User Token (60 jours)
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token" \
  -d "grant_type=fb_exchange_token" \
  -d "client_id=VOTRE_APP_ID" \
  -d "client_secret=VOTRE_APP_SECRET" \
  -d "fb_exchange_token=VOTRE_SHORT_LIVED_TOKEN"

# 2. Récupérer Page Access Token (jamais expire)
curl -X GET "https://graph.facebook.com/v18.0/me/accounts" \
  -d "access_token=VOTRE_LONG_LIVED_USER_TOKEN"
```

### Étape 4: Configurer .env

```bash
FACEBOOK_APP_ID=votre_app_id
FACEBOOK_APP_SECRET=votre_secret
FACEBOOK_ACCESS_TOKEN=votre_page_access_token
```

### Étape 5: Tester l'API

```python
import requests

response = requests.get(
    "https://graph.facebook.com/v18.0/me",
    params={"access_token": os.getenv("FACEBOOK_ACCESS_TOKEN")}
)
print(response.json())  # ✅ Infos de votre page
```

### Limites Rate Limiting

- **200 requêtes/heure/utilisateur**
- **4800 requêtes/jour** (app-level)

---

## 🎥 YouTube Data API v3 Setup

### Étape 1: Créer un projet Google Cloud

1. **Console**: https://console.cloud.google.com/
2. **Créer un projet**: "Trend Engine Pro"
3. **Activer l'API**: APIs & Services > Enable APIs > YouTube Data API v3

### Étape 2: Créer des credentials

1. **APIs & Services** > **Credentials**
2. **Create Credentials** > **API Key**
3. **Copiez** la clé générée

### Étape 3: Configurer .env

```bash
YOUTUBE_API_KEY=votre_api_key_40_chars
```

### Étape 4: Tester l'API

```python
from googleapiclient.discovery import build

youtube = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))

# Récupérer trending videos (US)
request = youtube.videos().list(
    part="snippet,statistics",
    chart="mostPopular",
    regionCode="US",
    maxResults=10
)
response = request.execute()

for video in response['items']:
    title = video['snippet']['title']
    views = video['statistics']['viewCount']
    print(f"✅ {title} ({views} views)")
```

### Limites Rate Limiting

- **10,000 unités/jour** (quota gratuit)
- 1 requête `videos.list` = 1 unité
- 1 requête `search.list` = 100 unités

---

## 🔧 Configuration Complète .env

Voici le template `.env` complet avec toutes les clés:

```bash
# =======================
# CORE SETTINGS
# =======================
ENVIRONMENT=development
LOG_LEVEL=INFO

# =======================
# GROQ LLM API (REQUIS)
# =======================
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# =======================
# REDDIT OAUTH
# =======================
REDDIT_CLIENT_ID=xxxxxxxxxxxxx  # 14 caractères
REDDIT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxx  # ~27 caractères
REDDIT_USER_AGENT=Trend Engine Pro/1.0 by /u/your_username

# =======================
# TIKTOK OAUTH
# =======================
TIKTOK_CLIENT_KEY=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
TIKTOK_ACCESS_TOKEN=your_access_token  # Refresh toutes les 24h

# =======================
# FACEBOOK GRAPH API
# =======================
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_page_access_token  # Long-lived

# =======================
# YOUTUBE DATA API v3
# =======================
YOUTUBE_API_KEY=your_api_key_40_chars

# =======================
# GOOGLE TRENDS (no auth required)
# =======================
GOOGLE_TRENDS_REGIONS=US,GB,CA,FR

# =======================
# DATABASE & STORAGE
# =======================
QDRANT_HOST=localhost
QDRANT_PORT=6333
MLFLOW_TRACKING_URI=http://localhost:5000

# =======================
# MODEL SETTINGS
# =======================
MODEL_TYPE=ensemble  # baseline ou ensemble
MODEL_CALIBRATION=isotonic
RETRAIN_THRESHOLD=100
```

---

## 🧪 Script de Test Complet

Créez `scripts/test_oauth.py`:

```python
#!/usr/bin/env python3
"""Test all OAuth configurations"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_reddit():
    try:
        import praw
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
        posts = list(reddit.subreddit("all").hot(limit=1))
        print("✅ Reddit OAuth OK")
        return True
    except Exception as e:
        print(f"❌ Reddit OAuth FAILED: {e}")
        return False

def test_youtube():
    try:
        from googleapiclient.discovery import build
        youtube = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))
        request = youtube.videos().list(part="snippet", chart="mostPopular", regionCode="US", maxResults=1)
        request.execute()
        print("✅ YouTube API OK")
        return True
    except Exception as e:
        print(f"❌ YouTube API FAILED: {e}")
        return False

def test_facebook():
    try:
        import requests
        response = requests.get(
            "https://graph.facebook.com/v18.0/me",
            params={"access_token": os.getenv("FACEBOOK_ACCESS_TOKEN")}
        )
        response.raise_for_status()
        print("✅ Facebook Graph API OK")
        return True
    except Exception as e:
        print(f"❌ Facebook API FAILED: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing OAuth configurations...\n")
    results = {
        "Reddit": test_reddit(),
        "YouTube": test_youtube(),
        "Facebook": test_facebook()
    }

    print(f"\n📊 Results: {sum(results.values())}/{len(results)} passed")
```

**Usage**:

```bash
python scripts/test_oauth.py
```

---

## ⚠️ Sécurité

### ❌ NE JAMAIS

- Commit `.env` dans Git (déjà dans `.gitignore`)
- Partager vos tokens/secrets
- Hardcoder les clés dans le code
- Utiliser tokens production en développement

### ✅ TOUJOURS

- Utiliser `.env` pour les secrets
- Rotation régulière des tokens (tous les 90 jours)
- Monitoring des quotas API
- Logs sans afficher les secrets

---

## 📚 Ressources

### Documentation officielle

- **Reddit**: https://www.reddit.com/dev/api/
- **TikTok**: https://developers.tiktok.com/doc
- **Facebook**: https://developers.facebook.com/docs/graph-api
- **YouTube**: https://developers.google.com/youtube/v3

### Librairies Python

```bash
pip install praw                # Reddit
pip install google-api-python-client  # YouTube
pip install requests            # TikTok, Facebook
```

---

## 🆘 Troubleshooting

### Reddit: "invalid_grant"

→ Vérifier CLIENT_ID et CLIENT_SECRET (copier-coller exact)

### TikTok: "access_token_invalid"

→ Token expiré (24h), refresh avec refresh_token

### Facebook: "OAuthException"

→ Vérifier permissions (pages_read_engagement required)

### YouTube: "quotaExceeded"

→ Limite 10k unités/jour atteinte, attendre 24h

---

## ✅ Prochaines étapes

Après configuration OAuth:

1. **Tester**: `python scripts/test_oauth.py`
2. **Collecter**: `python scripts/data/advanced_collector.py`
3. **Features**: Extract features sur vraies données
4. **Re-train**: Ensemble model avec données réelles
5. **Compare**: AUC synthetic vs real

---

**Dernière mise à jour**: 4 novembre 2024  
**Auteur**: Trend & Viral Engine Pro Team  
**Version**: 1.0
