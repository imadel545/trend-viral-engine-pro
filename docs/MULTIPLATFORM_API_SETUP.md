# 🌐 Configuration Multi-Platform API - Guide Complet

Ce guide explique comment obtenir et configurer les API keys pour **TikTok**, **Instagram**, **YouTube** et autres plateformes.

## 📋 Vue d'ensemble

Pour prédictions cross-platform, le système a besoin d'accès aux APIs de:

| Plateforme    | Gratuit?            | Difficulté   | Limites            | Priorité  |
| ------------- | ------------------- | ------------ | ------------------ | --------- |
| **YouTube**   | ✅ Oui              | 🟢 Facile    | 10K requêtes/jour  | 🔥 HIGH   |
| **Reddit**    | ✅ Oui              | 🟢 Facile    | 60 requêtes/min    | 🔥 HIGH   |
| **TikTok**    | ⚠️ Approval requis  | 🔴 Difficile | Sur demande        | 🟡 MEDIUM |
| **Instagram** | ⚠️ Business account | 🟡 Moyen     | 200 requêtes/heure | 🟡 MEDIUM |
| **Twitter/X** | ⚠️ Basic €100/mois  | 🔴 Difficile | Payant             | 🔵 LOW    |

---

## 1️⃣ YouTube Data API (PRIORITÉ: HIGH)

### Pourquoi YouTube?

- ✅ **Gratuit** (10,000 requêtes/jour = ~300 vidéos/jour)
- ✅ API stable et bien documentée
- ✅ Données complètes (views, likes, comments)
- ✅ Pas d'approval nécessaire

### Étapes d'installation

#### A. Créer projet Google Cloud

1. Aller sur https://console.cloud.google.com/
2. Cliquer **"New Project"**
3. Nom: `Trend-Viral-Engine-YouTube`
4. Cliquer **"Create"**

#### B. Activer YouTube Data API v3

1. Dans le menu → **"APIs & Services" → "Library"**
2. Chercher **"YouTube Data API v3"**
3. Cliquer **"Enable"**

#### C. Créer API Key

1. Menu → **"APIs & Services" → "Credentials"**
2. Cliquer **"Create Credentials" → "API Key"**
3. **Copier la clé** (ex: `AIzaSyC1234567890abcdefghijklmnopqrstu`)
4. ⚠️ **IMPORTANT**: Cliquer **"Restrict Key"**:
   - **Application restrictions**: None (ou HTTP referrers si web)
   - **API restrictions**: Restrict to **YouTube Data API v3** uniquement
5. Cliquer **"Save"**

#### D. Configurer dans .env

```bash
# Ajouter dans .env
YOUTUBE_API_KEY=AIzaSyC1234567890abcdefghijklmnopqrstu
```

#### E. Tester

```python
# Test YouTube API
import asyncio
from src.services.ingestion.multiplatform_collector import get_multiplatform_collector

async def test_youtube():
    collector = get_multiplatform_collector()
    videos = await collector.collect_youtube(keywords=["python tutorial"], count=10)

    for video in videos:
        print(f"✅ {video['title']}: {video['views']:,} views, {video['likes']:,} likes")

    await collector.close()

asyncio.run(test_youtube())
```

**Résultat attendu**:

```
✅ Python Tutorial for Beginners: 2,543,120 views, 87,432 likes
✅ Learn Python in 10 Minutes: 892,345 views, 23,567 likes
...
```

### Limites et quotas

- **10,000 unités/jour** (gratuit)
- 1 search = 100 unités
- 1 video details = 1 unité
- **Donc**: ~100 searches/jour ou 300 vidéos avec détails

**Conseil**: Collecte 1x/jour (300 vidéos) = suffisant pour entraînement

---

## 2️⃣ Reddit API (DÉJÀ CONFIGURÉ)

✅ **Déjà fonctionnel** dans le projet (voir `.env.example`)

**Vérifier configuration**:

```bash
# Dans .env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=TrendViralEngine/1.0
```

**Tester**:

```python
from src.services.ingestion.service import get_ingestion_service

service = get_ingestion_service()
posts = await service.collect_reddit_viral(limit=10)
print(f"✅ {len(posts)} Reddit posts collectés")
```

---

## 3️⃣ TikTok Research API (DIFFICULTÉ: HIGH)

### ⚠️ Contraintes

- **Approval requis** (peut prendre 2-4 semaines)
- Uniquement pour **recherche académique/commerciale**
- Nécessite justification d'usage

### Pourquoi TikTok est important?

- 🔥 Plateforme #1 pour contenu viral
- 📊 Algorithme le plus prédictif
- 💰 Meilleur ROI pour créateurs

### Étapes d'application

#### A. Créer compte développeur TikTok

1. Aller sur https://developers.tiktok.com/
2. **Sign Up** avec email professionnel
3. Vérifier email

#### B. Créer une app

1. Dashboard → **"My Apps" → "Create New App"**
2. Remplir:
   - **App name**: Trend Viral Engine
   - **App type**: Research
   - **Use case**: Social media trend analysis and viral content prediction
   - **Website**: (votre site ou GitHub)

#### C. Demander accès Research API

1. Dans l'app → **"Products" → "Research API"**
2. Cliquer **"Request Access"**
3. Remplir le formulaire:

**Questions fréquentes**:

**Q: What will you use the API for?**

> We are building a machine learning system to analyze viral content patterns across social media platforms. The Research API will allow us to collect public video metadata (views, likes, shares) to train predictive models that help content creators optimize their posts. This is for commercial use in a SaaS product for social media agencies.

**Q: Expected request volume?**

> 1,000 videos per day for initial training data collection (first 3 months), then 200 videos per day for ongoing model updates.

**Q: Which endpoints do you need?**

> - `/video/query/` - Search trending videos
> - `/video/info/` - Get video statistics

4. **Submit** et attendre approval (2-4 semaines)

#### D. Configuration après approval

```bash
# Ajouter dans .env (après approval)
TIKTOK_API_KEY=your_access_token_here
```

### Alternative: Scraping (sans API)

Si pas d'approval:

```python
# Utiliser données demo ou scraping léger (respecter Terms of Service)
# Voir src/services/ingestion/multiplatform_collector.py -> _get_tiktok_demo_data()
```

**⚠️ Attention**: TikTok interdit scraping agressif (risque de ban IP)

---

## 4️⃣ Instagram Graph API (DIFFICULTÉ: MEDIUM)

### Prérequis

- ✅ Compte **Instagram Business** (gratuit)
- ✅ Page Facebook associée
- ⚠️ Limites: 200 requêtes/heure

### Étapes

#### A. Convertir compte en Business

1. Instagram App → **Paramètres → Compte**
2. **"Passer à un compte professionnel"**
3. Choisir catégorie: **"Service digital"**

#### B. Lier à Facebook Page

1. Créer Facebook Page (si pas déjà fait)
2. Instagram → **Paramètres → Compte → Pages liées**
3. Connecter la page

#### C. Obtenir Access Token

1. Aller sur https://developers.facebook.com/
2. **"My Apps" → "Create App"**
3. Type: **"Business"**
4. Remplir infos basiques
5. **"Add Product" → "Instagram Graph API"**
6. Générer **Access Token**:
   - Tools → **Graph API Explorer**
   - Permissions: `instagram_basic`, `pages_read_engagement`
   - Generate Token

#### D. Configurer

```bash
# Dans .env
INSTAGRAM_API_KEY=your_access_token
```

#### E. Tester

```python
collector = get_multiplatform_collector()
posts = await collector.collect_instagram(hashtags=["viral", "trending"], count=20)
print(f"✅ {len(posts)} Instagram posts collectés")
```

### Limites

- **200 requêtes/heure** (Graph API)
- **90 jours** token validity (puis renouveler)

---

## 5️⃣ Twitter/X API (OPTIONNEL - PAYANT)

### ⚠️ Depuis 2023: API payante

| Plan      | Prix        | Limites         |
| --------- | ----------- | --------------- |
| **Free**  | €0          | ❌ Supprimé     |
| **Basic** | €100/mois   | 10K tweets/mois |
| **Pro**   | €5,000/mois | 1M tweets/mois  |

**Recommandation**: ⏸️ **Skip pour MVP** (trop cher pour valeur ajoutée)

Alternative: Utiliser Google Trends + Reddit pour tendances textuelles

---

## 📝 Configuration finale .env

```bash
# ============= MULTIPLATFORM APIS =============

# YouTube (PRIORITÉ HIGH - Gratuit)
YOUTUBE_API_KEY=AIzaSyC1234567890abcdefghijklmnopqrstu

# Reddit (DÉJÀ CONFIGURÉ)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=TrendViralEngine/1.0

# TikTok (après approval)
TIKTOK_API_KEY=your_tiktok_token

# Instagram (si compte business)
INSTAGRAM_API_KEY=your_instagram_token

# Twitter/X (optionnel - payant)
TWITTER_API_KEY=your_twitter_bearer_token
```

---

## 🚀 Test complet multiplateforme

```python
import asyncio
from src.services.ingestion.multiplatform_collector import get_multiplatform_collector

async def test_all_platforms():
    collector = get_multiplatform_collector()

    # Collecte toutes plateformes en parallèle
    data = await collector.collect_all_platforms(count_per_platform=50)

    print("\n📊 RÉSULTATS COLLECTE MULTIPLATEFORME:")
    print("=" * 50)

    for platform, posts in data.items():
        if posts:
            total_views = sum(p['views'] for p in posts)
            avg_engagement = sum(p['engagement_rate'] for p in posts) / len(posts)
            viral_count = sum(1 for p in posts if p['is_viral'])

            print(f"\n🎯 {platform.upper()}")
            print(f"   Posts collectés: {len(posts)}")
            print(f"   Vues totales: {total_views:,}")
            print(f"   Engagement moyen: {avg_engagement:.2f}%")
            print(f"   Posts viraux: {viral_count} ({viral_count/len(posts)*100:.1f}%)")
        else:
            print(f"\n⚠️  {platform.upper()}: Aucune donnée (API key manquante?)")

    await collector.close()

# Lancer test
asyncio.run(test_all_platforms())
```

**Résultat attendu** (avec YouTube + Reddit configurés):

```
📊 RÉSULTATS COLLECTE MULTIPLATEFORME:
==================================================

🎯 YOUTUBE
   Posts collectés: 50
   Vues totales: 45,234,567
   Engagement moyen: 4.32%
   Posts viraux: 12 (24.0%)

🎯 REDDIT
   Posts collectés: 50
   Vues totales: 234,567
   Engagement moyen: 8.76%
   Posts viraux: 8 (16.0%)

⚠️  TIKTOK: Aucune donnée (API key manquante?)
⚠️  INSTAGRAM: Aucune donnée (API key manquante?)
```

---

## 📈 Stratégie de collecte recommandée

### Phase 1: MVP (Semaines 1-2)

- ✅ **YouTube API** (gratuit, facile)
- ✅ **Reddit API** (déjà configuré)
- ⏩ **Total**: ~400 posts/jour

### Phase 2: Expansion (Semaines 3-6)

- ⏳ **TikTok approval** en cours
- ✅ **Instagram Business** (si compte existant)
- ⏩ **Total**: ~600 posts/jour

### Phase 3: Production (Mois 2-3)

- ✅ **TikTok approved**
- ✅ Toutes plateformes actives
- ⏩ **Total**: 1000+ posts/jour

### Coût estimé

| Plateforme | Coût/mois           | Valeur      |
| ---------- | ------------------- | ----------- |
| YouTube    | €0                  | 🟢 HIGH     |
| Reddit     | €0                  | 🟢 HIGH     |
| TikTok     | €0 (après approval) | 🔥 CRITICAL |
| Instagram  | €0                  | 🟡 MEDIUM   |
| Twitter/X  | €100                | 🔴 Skip MVP |

**Total MVP**: **€0/mois** 🎉

---

## 🆘 Troubleshooting

### Erreur: "API key invalid"

```bash
# Vérifier que la clé est dans .env
cat .env | grep YOUTUBE_API_KEY

# Redémarrer l'app pour recharger .env
docker-compose restart
```

### Erreur: "Quota exceeded"

```python
# YouTube: 10K unités/jour dépassées
# Solution: Attendre minuit (reset quotidien) ou créer nouveau projet

# Instagram: 200 requêtes/heure
# Solution: Ralentir collecte (1 requête/20 secondes)
```

### TikTok: Application rejetée

```
Raisons fréquentes:
1. Use case pas assez détaillé
2. Email non-professionnel (gmail.com)
3. Pas de site web/GitHub

Solutions:
- Créer landing page projet
- Email professionnel (@votre-domaine.com)
- Détailler cas d'usage (recherche commerciale)
```

---

## 📚 Ressources

- **YouTube API**: https://developers.google.com/youtube/v3
- **Reddit API**: https://www.reddit.com/dev/api/
- **TikTok Research API**: https://developers.tiktok.com/products/research-api/
- **Instagram Graph API**: https://developers.facebook.com/docs/instagram-api
- **Postman Collections**: Tester APIs interactivement

---

## ✅ Checklist finale

- [ ] YouTube API key configurée et testée
- [ ] Reddit API fonctionnelle (déjà fait normalement)
- [ ] TikTok application soumise (si pas déjà)
- [ ] Instagram Business account créé (optionnel)
- [ ] Test `collect_all_platforms()` réussi
- [ ] Collecte automatique configurée (1x/jour)

**Une fois 2+ plateformes configurées** → Système multiplateforme opérationnel! 🚀
