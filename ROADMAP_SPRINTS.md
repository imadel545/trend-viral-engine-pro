# 🚀 ROADMAP - Trend & Viral Engine Pro

## Implémentation progressive - Style DeepMind/OpenAI/Meta

**Objectif:** Transformer le système actuel (85% opérationnel) en moteur autonome de génération virale  
**Timeline totale:** 4-6 semaines  
**Approche:** Progressive, testée, sans régression

---

## 📅 VUE D'ENSEMBLE

```
┌────────────┬─────────────┬──────────────┬──────────────┐
│  Sprint 1  │  Sprint 2   │   Sprint 3   │   Sprint 4   │
│  5 jours   │  1 semaine  │  1 semaine   │  2 semaines  │
├────────────┼─────────────┼──────────────┼──────────────┤
│ Données +  │ Publication │ Génération   │ Apprentissage│
│ Fixes      │ + Feedback  │ Virale       │ + Scaling    │
└────────────┴─────────────┴──────────────┴──────────────┘
    ↓              ↓              ↓              ↓
 Fondations    Automatisation  Viralité    Production
```

---

## 🏃 SPRINT 1: FONDATIONS SOLIDES

**Durée:** 5 jours  
**Objectif:** Stabiliser ingestion + enrichir données + fixes critiques

### 📋 Tâches

#### Tâche 1.1: Fix GoogleTrendsSource (30 min)

**Fichier:** `src/services/ingestion/service.py`

**Problème actuel:**

```python
class GoogleTrendsSource(DataSource):
    def __init__(self):
        super().__init__("google_trends")
        # ❌ Manque: self._request_count = 0
```

**Fix:**

```python
class GoogleTrendsSource(DataSource):
    def __init__(self):
        super().__init__("google_trends")
        self._request_count = 0  # ← Ajouter
        self._last_request_time = None
        self.pytrends = TrendReq(hl='en-US', tz=360)
```

**Test:**

```bash
pytest tests/test_ingestion.py::test_google_trends_source -v
```

**Critère succès:** ✅ Test passing

---

#### Tâche 1.2: Enrichir Reddit data (4h)

**Fichier:** `src/services/ingestion/advanced_sources.py`

**Problème:** 80% des trends Reddit ont `text=NaN`

**Solution:** Fetch selftext + top 5 comments

**Implémentation:**

```python
class EnhancedRedditSource(DataSource):
    async def _enrich_post(self, submission) -> Dict[str, Any]:
        """Enrich Reddit post avec selftext + comments."""

        # 1. Get selftext
        text_parts = []
        if submission.selftext:
            text_parts.append(submission.selftext[:500])

        # 2. Fetch top 5 comments
        try:
            submission.comments.replace_more(limit=0)
            top_comments = sorted(
                submission.comments.list(),
                key=lambda c: c.score,
                reverse=True
            )[:5]

            for comment in top_comments:
                if hasattr(comment, 'body') and len(comment.body) > 20:
                    text_parts.append(comment.body[:200])
        except Exception as e:
            self.logger.warning(f"Failed to fetch comments: {e}")

        # 3. Combine
        enriched_text = " | ".join(text_parts)

        return {
            'topic': submission.title,
            'text': enriched_text or submission.title,  # Fallback sur title
            'url': submission.url,
            'score': submission.score,
            'upvote_ratio': submission.upvote_ratio,
            'num_comments': submission.num_comments,
            'created_utc': submission.created_utc,
            'subreddit': submission.subreddit.display_name,
            'author': str(submission.author),
            'source': 'reddit_enhanced',
            'collected_at': datetime.now().isoformat()
        }
```

**Test manuel:**

```python
# Vérifier qualité données
import pandas as pd
df = pd.read_parquet('data/raw/reddit_enhanced_YYYYMMDD_HHMMSS.parquet')
print(f"Rows with text: {df['text'].notna().sum()} / {len(df)}")
print(f"Avg text length: {df['text'].str.len().mean():.0f} chars")
```

**Critère succès:**

- ✅ 95%+ trends ont text non-vide
- ✅ Longueur moyenne text ≥ 100 caractères

---

#### Tâche 1.3: Ajouter YouTube Trending source (3h)

**Fichier:** `src/services/ingestion/youtube_trending.py` (NOUVEAU)

**Implémentation:**

```python
"""
YouTube Trending Source - Collecte vidéos trending
Nécessite: YOUTUBE_API_KEY dans .env
"""
import aiohttp
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

from src.core.config import settings
from src.services.ingestion.service import DataSource


class YouTubeTrendingSource(DataSource):
    """
    Collecte vidéos trending YouTube via YouTube Data API v3.

    API Docs: https://developers.google.com/youtube/v3/docs/videos/list
    Quota: 1 request = 100 units (10,000 daily limit = 100 requests/day)
    """

    def __init__(self):
        super().__init__("youtube_trending")
        self.api_key = settings.youtube_api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

        if not self.api_key:
            self.logger.warning("⚠️ YOUTUBE_API_KEY not configured")

    async def collect(
        self,
        region_code: str = "US",
        category_id: str = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Collecte vidéos trending.

        Args:
            region_code: Code pays ISO (US, FR, GB, etc.)
            category_id: Catégorie YouTube (optionnel)
            max_results: Nombre max de vidéos (1-50)

        Returns:
            Liste de trends avec title, description, statistics
        """
        if not self.api_key:
            self.logger.error("YOUTUBE_API_KEY required")
            return []

        url = f"{self.base_url}/videos"
        params = {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": min(max_results, 50),
            "key": self.api_key
        }

        if category_id:
            params["videoCategoryId"] = category_id

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_videos(data, region_code)
                    elif response.status == 403:
                        error = await response.json()
                        self.logger.error(f"API quota exceeded or invalid key: {error}")
                        return []
                    else:
                        error = await response.text()
                        self.logger.error(f"API error {response.status}: {error}")
                        return []

        except Exception as e:
            self.logger.error(f"Failed to collect YouTube trends: {e}")
            return []

    def _parse_videos(self, data: Dict, region_code: str) -> List[Dict[str, Any]]:
        """Parse API response to trends format."""
        trends = []

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})

            # Calculer engagement rate
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))

            engagement_rate = (likes + comments) / views if views > 0 else 0

            trend = {
                'topic': snippet.get("title", ""),
                'text': snippet.get("description", "")[:1000],  # Limit 1000 chars
                'url': f"https://www.youtube.com/watch?v={item['id']}",
                'video_id': item['id'],
                'channel': snippet.get("channelTitle", ""),
                'channel_id': snippet.get("channelId", ""),
                'published_at': snippet.get("publishedAt", ""),
                'views': views,
                'likes': likes,
                'comments': comments,
                'engagement_rate': engagement_rate,
                'duration': content.get("duration", ""),
                'category_id': snippet.get("categoryId", ""),
                'tags': snippet.get("tags", []),
                'region': region_code,
                'source': 'youtube_trending',
                'collected_at': datetime.now().isoformat()
            }

            trends.append(trend)

        self.logger.info(f"✅ Collected {len(trends)} YouTube trending videos from {region_code}")
        return trends
```

**Ajouter dans IngestionService:**

```python
# src/services/ingestion/service.py

from src.services.ingestion.youtube_trending import YouTubeTrendingSource

class IngestionService:
    def __init__(self):
        self.sources = {
            "google_trends": GoogleTrendsSource(),
            "reddit": EnhancedRedditSource(),
            "tiktok": TikTokCreativeCenterSource(),
            "facebook": FacebookGraphAPISource(),
            "youtube": YouTubeTrendingSource(),  # ← Ajouter
        }
```

**Test:**

```python
# Test manual
import asyncio
from src.services.ingestion.youtube_trending import YouTubeTrendingSource

async def test():
    source = YouTubeTrendingSource()
    trends = await source.collect(region_code="US", max_results=10)
    print(f"Collected: {len(trends)} trends")
    if trends:
        print(f"Sample: {trends[0]['topic'][:50]}...")

asyncio.run(test())
```

**Critère succès:**

- ✅ 50 vidéos trending collectées
- ✅ Chaque vidéo a title + description + statistics
- ✅ Quota API non dépassé (100 units/request)

---

#### Tâche 1.4: Filtrer trends avec texte insuffisant (1h)

**Fichier:** `src/services/ingestion/service.py`

**Ajout validation:**

```python
class IngestionService:
    def _validate_trend(self, trend: Dict[str, Any]) -> bool:
        """Valider qualité d'un trend avant sauvegarde."""

        # 1. Champs obligatoires
        required_fields = ['topic', 'source', 'collected_at']
        if not all(field in trend for field in required_fields):
            return False

        # 2. Text minimum
        text = str(trend.get('text', ''))
        if len(text) < 20:  # Minimum 20 caractères
            self.logger.debug(f"Trend rejected: text too short ({len(text)} chars)")
            return False

        # 3. Topic non-vide
        topic = str(trend.get('topic', '')).strip()
        if len(topic) < 5:
            self.logger.debug(f"Trend rejected: topic too short")
            return False

        return True

    async def run_collection(self, sources: List[str] = None) -> Path:
        """Collecte avec validation."""
        all_trends = []

        for source_name, source in self.sources.items():
            if sources and source_name not in sources:
                continue

            trends = await source.collect()

            # Filtrer trends invalides
            valid_trends = [t for t in trends if self._validate_trend(t)]
            invalid_count = len(trends) - len(valid_trends)

            if invalid_count > 0:
                self.logger.warning(
                    f"{source_name}: {invalid_count}/{len(trends)} trends filtered (invalid)"
                )

            all_trends.extend(valid_trends)

        # Save...
```

**Critère succès:**

- ✅ Trends avec text <20 chars filtrés
- ✅ Logs indiquent nombre de trends filtrés
- ✅ 95%+ des trends sauvegardés sont exploitables

---

#### Tâche 1.5: Tests Sprint 1 (1h)

**Fichiers tests à créer/modifier:**

1. `tests/test_youtube_trending.py`:

```python
import pytest
from src.services.ingestion.youtube_trending import YouTubeTrendingSource

@pytest.mark.asyncio
async def test_youtube_collect():
    source = YouTubeTrendingSource()

    # Skip si pas de clé API
    if not source.api_key:
        pytest.skip("YOUTUBE_API_KEY not configured")

    trends = await source.collect(region_code="US", max_results=10)

    assert len(trends) > 0
    assert len(trends) <= 10

    # Vérifier structure
    trend = trends[0]
    assert 'topic' in trend
    assert 'text' in trend
    assert 'url' in trend
    assert 'views' in trend
    assert 'source' in trend
    assert trend['source'] == 'youtube_trending'
```

2. Update `tests/test_ingestion.py`:

```python
def test_ingestion_service_has_youtube():
    from src.services.ingestion import get_ingestion_service
    service = get_ingestion_service()
    assert 'youtube' in service.sources
```

**Critère succès:**

- ✅ Tous les tests Sprint 1 passent
- ✅ Pas de régression sur tests existants

---

### 📊 Livrables Sprint 1

| Livrable          | Fichier                                      | Statut |
| ----------------- | -------------------------------------------- | ------ |
| GoogleTrends fix  | `src/services/ingestion/service.py`          | ✅     |
| Reddit enrichment | `src/services/ingestion/advanced_sources.py` | ✅     |
| YouTube source    | `src/services/ingestion/youtube_trending.py` | ✅     |
| Validation trends | `src/services/ingestion/service.py`          | ✅     |
| Tests             | `tests/test_youtube_trending.py`             | ✅     |

---

### 🎯 Critères de succès Sprint 1

```
✅ GoogleTrendsSource fonctionne (test passing)
✅ 95%+ trends Reddit ont texte ≥100 chars
✅ 50 vidéos YouTube trending collectées
✅ 95%+ trends sauvegardés sont exploitables
✅ Pas de régression (37+ tests passing)
✅ Données enrichies disponibles dans data/raw/
```

**Validation finale:**

```bash
# 1. Run ingestion
python scripts/run_ingestion.py --sources reddit,youtube

# 2. Vérifier qualité
python scripts/validate_data_quality.py

# 3. Tests
pytest tests/test_ingestion.py -v
```

---

## 🎬 SPRINT 2: PUBLICATION & FEEDBACK AUTOMATIQUE

**Durée:** 1 semaine  
**Objectif:** YouTube Data API + upload automatique + tracking metrics

### 📋 Tâches

#### Tâche 2.1: Configuration YouTube API (voir guide dédié)

**Durée:** 30 min

**Actions:**

1. Console Google Cloud → Nouveau projet "TrendViralEngine"
2. Activer YouTube Data API v3
3. Créer OAuth 2.0 Client ID (upload requiert auth)
4. Download `client_secrets.json`
5. Stocker dans `.env` et `.gitignore`

**Détails:** Voir `GUIDE_YOUTUBE_API.md` (section suivante)

---

#### Tâche 2.2: YouTube Publisher Service (6h)

**Fichier:** `src/services/publishing/youtube_publisher.py` (NOUVEAU)

**Implémentation:**

```python
"""
YouTube Publisher - Upload automatique vidéos
Utilise YouTube Data API v3 avec OAuth2.0
"""
import os
import pickle
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from loguru import logger

from src.core.config import settings


SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


class YouTubePublisher:
    """
    Publie vidéos sur YouTube avec tracking.

    Quota: 1 upload = 1600 units (10,000 daily = ~6 uploads/jour)
    """

    def __init__(self):
        self.logger = logger.bind(service="youtube_publisher")
        self.credentials_file = settings.youtube_credentials_file
        self.token_file = Path("data/cache/youtube_token.pickle")
        self.youtube = None

        self._authenticate()

    def _authenticate(self):
        """Authentification OAuth2.0."""
        creds = None

        # Check token sauvegardé
        if self.token_file.exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        # Refresh si expiré
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self.logger.info("✅ YouTube token refreshed")

        # Nouvelle auth si pas de token
        if not creds or not creds.valid:
            if not Path(self.credentials_file).exists():
                raise FileNotFoundError(
                    f"YouTube credentials not found: {self.credentials_file}\n"
                    f"Download from Google Cloud Console and save to this path."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, SCOPES
            )
            creds = flow.run_local_server(port=0)

            # Save token
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

            self.logger.info("✅ YouTube authenticated (new token)")

        # Build API client
        self.youtube = build('youtube', 'v3', credentials=creds)
        self.logger.info("✅ YouTube API client ready")

    async def upload(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: List[str] = None,
        category_id: str = "22",  # People & Blogs
        privacy_status: str = "public"
    ) -> Dict[str, Any]:
        """
        Upload vidéo sur YouTube.

        Args:
            video_path: Chemin vers .mp4
            title: Titre (max 100 chars)
            description: Description (max 5000 chars)
            tags: Tags (max 500 chars total)
            category_id: Catégorie YouTube (22=People, 24=Entertainment)
            privacy_status: public | unlisted | private

        Returns:
            {
                'video_id': 'abc123',
                'url': 'https://www.youtube.com/watch?v=abc123',
                'upload_status': 'uploaded',
                'published_at': '2025-11-06T...'
            }
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        # Prepare metadata
        body = {
            'snippet': {
                'title': title[:100],  # Limit 100 chars
                'description': description[:5000],
                'tags': tags or [],
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }

        # Upload
        media = MediaFileUpload(
            str(video_path),
            chunksize=1024*1024,  # 1MB chunks
            resumable=True
        )

        self.logger.info(f"⬆️  Uploading {video_path.name} to YouTube...")

        try:
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            response = self._upload_with_progress(request)

            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            self.logger.info(f"✅ Uploaded: {video_url}")

            return {
                'video_id': video_id,
                'url': video_url,
                'title': title,
                'upload_status': 'uploaded',
                'published_at': datetime.now().isoformat(),
                'platform': 'youtube'
            }

        except Exception as e:
            self.logger.error(f"❌ Upload failed: {e}")
            raise

    def _upload_with_progress(self, request):
        """Execute upload avec progress."""
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                self.logger.info(f"⬆️  Progress: {progress}%")

        return response

    async def get_video_analytics(
        self,
        video_id: str
    ) -> Dict[str, Any]:
        """
        Récupère metrics d'une vidéo.

        Returns:
            {
                'views': 12345,
                'likes': 567,
                'comments': 89,
                'shares': 23,  # Si disponible
                'watch_time_minutes': 4567.8
            }
        """
        try:
            # Get video statistics
            request = self.youtube.videos().list(
                part='statistics',
                id=video_id
            )
            response = request.execute()

            if not response.get('items'):
                self.logger.warning(f"Video {video_id} not found")
                return {}

            stats = response['items'][0]['statistics']

            analytics = {
                'video_id': video_id,
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'comments': int(stats.get('commentCount', 0)),
                'favorites': int(stats.get('favoriteCount', 0)),
                'fetched_at': datetime.now().isoformat()
            }

            self.logger.info(f"📊 Analytics for {video_id}: {analytics['views']} views")
            return analytics

        except Exception as e:
            self.logger.error(f"Failed to fetch analytics: {e}")
            return {}


# Singleton factory
_publisher = None

def get_youtube_publisher() -> YouTubePublisher:
    global _publisher
    if _publisher is None:
        _publisher = YouTubePublisher()
    return _publisher
```

---

#### Tâche 2.3: Publishing Service orchestrator (3h)

**Fichier:** `src/services/publishing/service.py` (NOUVEAU)

**Implémentation:**

```python
"""
Publishing Service - Orchestration multi-plateforme
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from loguru import logger

from src.services.publishing.youtube_publisher import get_youtube_publisher
# from src.services.publishing.tiktok_publisher import get_tiktok_publisher  # Future


class PublishingService:
    """
    Gère publication automatique sur multiples plateformes.
    Tracking: video_id → URL → metrics
    """

    def __init__(self):
        self.logger = logger.bind(service="publishing")
        self.youtube = get_youtube_publisher()
        # self.tiktok = get_tiktok_publisher()  # Sprint 4

        # Tracking database (simple JSON pour MVP)
        self.tracking_file = Path("data/publishing/tracking.json")
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)

    async def publish(
        self,
        video_path: Path,
        metadata: Dict[str, Any],
        platforms: List[str] = None
    ) -> Dict[str, Any]:
        """
        Publie vidéo sur plateformes spécifiées.

        Args:
            video_path: Chemin .mp4
            metadata: {
                'title': str,
                'description': str,
                'tags': List[str],
                'category': str
            }
            platforms: ['youtube', 'tiktok'] (défaut: youtube uniquement)

        Returns:
            {
                'youtube': {'video_id': '...', 'url': '...'},
                'tiktok': {...}
            }
        """
        platforms = platforms or ['youtube']
        results = {}

        for platform in platforms:
            try:
                if platform == 'youtube':
                    result = await self.youtube.upload(
                        video_path=video_path,
                        title=metadata['title'],
                        description=metadata['description'],
                        tags=metadata.get('tags', []),
                        category_id=metadata.get('category_id', '22'),
                        privacy_status=metadata.get('privacy', 'public')
                    )
                    results['youtube'] = result

                    # Save tracking
                    await self._track_publication(video_path, result)

                # elif platform == 'tiktok':  # Sprint 4
                #     result = await self.tiktok.upload(...)
                #     results['tiktok'] = result

            except Exception as e:
                self.logger.error(f"Failed to publish on {platform}: {e}")
                results[platform] = {'error': str(e)}

        return results

    async def _track_publication(
        self,
        video_path: Path,
        result: Dict[str, Any]
    ):
        """Enregistrer publication pour tracking."""
        import json

        tracking = {}
        if self.tracking_file.exists():
            tracking = json.loads(self.tracking_file.read_text())

        video_name = video_path.stem
        tracking[video_name] = {
            'video_path': str(video_path),
            'published_at': result['published_at'],
            'platforms': {
                result['platform']: {
                    'video_id': result['video_id'],
                    'url': result['url']
                }
            }
        }

        self.tracking_file.write_text(json.dumps(tracking, indent=2))
        self.logger.info(f"✅ Tracked publication: {video_name}")

    async def collect_metrics(
        self,
        video_name: str
    ) -> Dict[str, Any]:
        """
        Collecte metrics de toutes les plateformes pour une vidéo.

        Returns:
            {
                'youtube': {'views': 123, 'likes': 45, ...},
                'tiktok': {...}
            }
        """
        import json

        if not self.tracking_file.exists():
            return {}

        tracking = json.loads(self.tracking_file.read_text())

        if video_name not in tracking:
            self.logger.warning(f"Video {video_name} not tracked")
            return {}

        metrics = {}

        # YouTube
        if 'youtube' in tracking[video_name]['platforms']:
            video_id = tracking[video_name]['platforms']['youtube']['video_id']
            yt_metrics = await self.youtube.get_video_analytics(video_id)
            metrics['youtube'] = yt_metrics

        # TikTok (Sprint 4)
        # if 'tiktok' in tracking[video_name]['platforms']:
        #     ...

        return metrics


# Singleton factory
_service = None

def get_publishing_service() -> PublishingService:
    global _service
    if _service is None:
        _service = PublishingService()
    return _service
```

---

#### Tâche 2.4: Feedback loop automatique (4h)

**Fichier:** `src/services/feedback/auto_collector.py` (NOUVEAU)

**Implémentation:**

```python
"""
Auto Feedback Collector - Collecte automatique metrics
Scheduled task: run toutes les 24h pour vidéos publiées
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from loguru import logger

from src.services.publishing import get_publishing_service
from src.services.feedback import get_feedback_service


class AutoFeedbackCollector:
    """
    Collecte automatiquement metrics des vidéos publiées.
    Run 24h et 48h après publication.
    """

    def __init__(self):
        self.logger = logger.bind(service="auto_feedback")
        self.publishing = get_publishing_service()
        self.feedback = get_feedback_service()
        self.tracking_file = Path("data/publishing/tracking.json")

    async def collect_all_pending(self):
        """Collecte metrics pour vidéos nécessitant update."""
        if not self.tracking_file.exists():
            self.logger.info("No tracked videos yet")
            return

        tracking = json.loads(self.tracking_file.read_text())

        pending_videos = self._find_pending_videos(tracking)

        self.logger.info(f"📊 Collecting metrics for {len(pending_videos)} videos")

        for video_name in pending_videos:
            await self._collect_video_metrics(video_name, tracking[video_name])

    def _find_pending_videos(self, tracking: Dict) -> List[str]:
        """Trouve vidéos nécessitant collecte metrics."""
        pending = []
        now = datetime.now()

        for video_name, data in tracking.items():
            published_at = datetime.fromisoformat(data['published_at'])
            hours_since = (now - published_at).total_seconds() / 3600

            # Collecter après 24h et 48h
            last_collected = data.get('last_metrics_collected')

            if hours_since >= 24:
                if not last_collected:
                    pending.append(video_name)
                else:
                    last_dt = datetime.fromisoformat(last_collected)
                    if (now - last_dt).total_seconds() / 3600 >= 24:
                        pending.append(video_name)

        return pending

    async def _collect_video_metrics(
        self,
        video_name: str,
        video_data: Dict[str, Any]
    ):
        """Collecte et enregistre metrics pour une vidéo."""
        try:
            # Get metrics
            metrics = await self.publishing.collect_metrics(video_name)

            if not metrics:
                return

            # Aggregate tous platforms
            total_views = sum(
                platform_metrics.get('views', 0)
                for platform_metrics in metrics.values()
            )
            total_likes = sum(
                platform_metrics.get('likes', 0)
                for platform_metrics in metrics.values()
            )
            total_comments = sum(
                platform_metrics.get('comments', 0)
                for platform_metrics in metrics.values()
            )

            # Record feedback
            self.feedback.record_feedback(
                video_id=video_name,
                views_24h=total_views,
                likes=total_likes,
                shares=0,  # TODO: collect shares
                comments=total_comments,
                platform_metrics=metrics
            )

            # Update tracking
            video_data['last_metrics_collected'] = datetime.now().isoformat()
            video_data['latest_metrics'] = metrics

            self._save_tracking_update(video_name, video_data)

            self.logger.info(
                f"✅ {video_name}: {total_views} views, {total_likes} likes"
            )

        except Exception as e:
            self.logger.error(f"Failed to collect {video_name}: {e}")

    def _save_tracking_update(self, video_name: str, video_data: Dict):
        """Update tracking file."""
        tracking = json.loads(self.tracking_file.read_text())
        tracking[video_name] = video_data
        self.tracking_file.write_text(json.dumps(tracking, indent=2))


# Singleton
_collector = None

def get_auto_feedback_collector() -> AutoFeedbackCollector:
    global _collector
    if _collector is None:
        _collector = AutoFeedbackCollector()
    return _collector
```

---

#### Tâche 2.5: Scheduled task Prefect (2h)

**Fichier:** `scripts/workflows/feedback_collection_flow.py` (NOUVEAU)

**Implémentation:**

```python
"""
Prefect Flow - Collecte automatique feedback toutes les 24h
"""
from prefect import flow, task
from prefect.schedules import IntervalSchedule
from datetime import timedelta
import asyncio

from src.services.feedback.auto_collector import get_auto_feedback_collector


@task(name="collect_feedback", retries=3)
async def collect_feedback_task():
    """Collecte feedback pour vidéos publiées."""
    collector = get_auto_feedback_collector()
    await collector.collect_all_pending()


@flow(
    name="auto_feedback_collection",
    description="Collecte automatique metrics vidéos publiées"
)
async def feedback_collection_flow():
    """Flow principal."""
    await collect_feedback_task()


if __name__ == "__main__":
    # Run once
    asyncio.run(feedback_collection_flow())
```

**Déploiement:**

```bash
# Déployer avec schedule 24h
prefect deployment build scripts/workflows/feedback_collection_flow.py:feedback_collection_flow \
    --name daily-feedback \
    --interval 86400  # 24h en secondes

prefect deployment apply feedback_collection_flow-deployment.yaml
```

---

### 📊 Livrables Sprint 2

| Livrable           | Fichier                                         | Statut |
| ------------------ | ----------------------------------------------- | ------ |
| YouTube API config | `GUIDE_YOUTUBE_API.md`                          | ✅     |
| YouTube Publisher  | `src/services/publishing/youtube_publisher.py`  | ✅     |
| Publishing Service | `src/services/publishing/service.py`            | ✅     |
| Auto Feedback      | `src/services/feedback/auto_collector.py`       | ✅     |
| Prefect Flow       | `scripts/workflows/feedback_collection_flow.py` | ✅     |
| Tests              | `tests/test_publishing.py`                      | ✅     |

---

### 🎯 Critères de succès Sprint 2

```
✅ YouTube API configurée et auth OAuth2 fonctionnelle
✅ 1 vidéo test uploadée sur YouTube avec succès
✅ video_id → URL trackée dans tracking.json
✅ Metrics collectées après 24h (views, likes, comments)
✅ Feedback enregistré dans data/feedback/
✅ Prefect flow déployé et scheduled
✅ Tests passing (40+ tests)
```

**Validation finale:**

```bash
# 1. Upload test
python scripts/test_youtube_upload.py outputs/video_test.mp4

# 2. Vérifier tracking
cat data/publishing/tracking.json

# 3. Collecter metrics (after 24h)
python scripts/collect_feedback.py

# 4. Tests
pytest tests/test_publishing.py -v
```

---

## 🎨 SPRINT 3: GÉNÉRATION VIDÉO VIRALE

**Durée:** 1 semaine  
**Objectif:** TTS + animations + backgrounds + musique

**(Suite dans le prochain message - Sprints 3 & 4)**

---

**Status:** 📝 Roadmap Sprint 1 & 2 détaillés  
**Next:** Sprint 3 (Génération virale) + Sprint 4 (Validation) + Guide YouTube API
