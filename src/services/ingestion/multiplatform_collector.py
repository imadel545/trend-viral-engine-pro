"""
Multi-Platform Data Collector - Collecte données de TOUTES les plateformes
===========================================================================

Collecte données virales de:
- TikTok (via TikTok API)
- Instagram (via Instagram Graph API)
- YouTube (via YouTube Data API)
- Reddit (existant)
- Twitter/X (optionnel)

Permet d'entraîner le modèle sur données multiplateforme
pour prédictions cross-platform.
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from src.core.config import settings


class MultiPlatformCollector:
    """
    Collecte données de toutes les plateformes sociales.
    
    Unifie les formats de données pour entraînement ML cross-platform.
    """
    
    def __init__(self):
        self.logger = logger.bind(service="multiplatform_collector")
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API Keys (depuis .env)
        self.tiktok_api_key = getattr(settings, 'tiktok_api_key', None)
        self.instagram_api_key = getattr(settings, 'instagram_api_key', None)
        self.youtube_api_key = getattr(settings, 'youtube_api_key', None)
        
        self.logger.info("✅ MultiPlatformCollector initialisé")
    
    async def _ensure_session(self):
        """Crée session HTTP si nécessaire"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def collect_tiktok(
        self,
        keywords: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Collecte posts TikTok trending.
        
        Args:
            keywords: Liste de mots-clés à rechercher
            hashtags: Hashtags à suivre
            count: Nombre de posts à collecter
        
        Returns:
            Liste de posts normalisés
        """
        
        if not self.tiktok_api_key:
            self.logger.warning("⚠️  TikTok API key manquante - utilisation données demo")
            return self._get_tiktok_demo_data(count)
        
        await self._ensure_session()
        
        posts = []
        
        try:
            # TikTok Research API (nécessite approval)
            url = "https://open.tiktokapis.com/v2/research/video/query/"
            
            headers = {
                "Authorization": f"Bearer {self.tiktok_api_key}",
                "Content-Type": "application/json"
            }
            
            # Query trending videos
            query = {
                "query": {
                    "and": [
                        {"field_name": "region_code", "operation": "EQ", "field_values": ["US", "FR", "GB"]},
                        {"field_name": "create_date", "operation": "GTE", "field_values": [(datetime.now() - timedelta(days=7)).strftime("%Y%m%d")]}
                    ]
                },
                "max_count": count
            }
            
            async with self.session.post(url, headers=headers, json=query) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    for video in data.get('data', {}).get('videos', []):
                        posts.append(self._normalize_tiktok_post(video))
                    
                    self.logger.info(f"✅ TikTok: {len(posts)} posts collectés")
                else:
                    self.logger.error(f"❌ TikTok API error: {resp.status}")
                    return self._get_tiktok_demo_data(count)
        
        except Exception as e:
            self.logger.error(f"❌ Erreur TikTok: {e}")
            return self._get_tiktok_demo_data(count)
        
        return posts
    
    async def collect_instagram(
        self,
        hashtags: Optional[List[str]] = None,
        count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Collecte posts Instagram trending.
        
        Args:
            hashtags: Hashtags à suivre
            count: Nombre de posts
        
        Returns:
            Liste de posts normalisés
        """
        
        if not self.instagram_api_key:
            self.logger.warning("⚠️  Instagram API key manquante - données demo")
            return self._get_instagram_demo_data(count)
        
        await self._ensure_session()
        
        posts = []
        
        try:
            # Instagram Graph API
            url = f"https://graph.instagram.com/v18.0/ig_hashtag_search"
            
            params = {
                "user_id": "me",  # Nécessite compte business
                "q": ",".join(hashtags or ["viral", "trending"]),
                "access_token": self.instagram_api_key
            }
            
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Récupérer top posts pour chaque hashtag
                    for hashtag_data in data.get('data', []):
                        hashtag_id = hashtag_data['id']
                        
                        # Get top media
                        media_url = f"https://graph.instagram.com/v18.0/{hashtag_id}/top_media"
                        media_params = {
                            "access_token": self.instagram_api_key,
                            "fields": "id,caption,like_count,comments_count,timestamp,media_type,media_url"
                        }
                        
                        async with self.session.get(media_url, params=media_params) as media_resp:
                            if media_resp.status == 200:
                                media_data = await media_resp.json()
                                
                                for post in media_data.get('data', []):
                                    posts.append(self._normalize_instagram_post(post))
                                    
                                    if len(posts) >= count:
                                        break
                    
                    self.logger.info(f"✅ Instagram: {len(posts)} posts collectés")
                else:
                    self.logger.error(f"❌ Instagram API error: {resp.status}")
                    return self._get_instagram_demo_data(count)
        
        except Exception as e:
            self.logger.error(f"❌ Erreur Instagram: {e}")
            return self._get_instagram_demo_data(count)
        
        return posts[:count]
    
    async def collect_youtube(
        self,
        keywords: Optional[List[str]] = None,
        count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Collecte vidéos YouTube trending.
        
        Args:
            keywords: Mots-clés de recherche
            count: Nombre de vidéos
        
        Returns:
            Liste de vidéos normalisées
        """
        
        if not self.youtube_api_key:
            self.logger.warning("⚠️  YouTube API key manquante - données demo")
            return self._get_youtube_demo_data(count)
        
        await self._ensure_session()
        
        videos = []
        
        try:
            # YouTube Data API v3
            url = "https://www.googleapis.com/youtube/v3/search"
            
            params = {
                "part": "snippet",
                "q": " ".join(keywords or ["viral", "trending"]),
                "type": "video",
                "order": "viewCount",
                "maxResults": min(count, 50),  # Max 50 per request
                "key": self.youtube_api_key
            }
            
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    video_ids = [item['id']['videoId'] for item in data.get('items', [])]
                    
                    # Get detailed stats
                    if video_ids:
                        stats_url = "https://www.googleapis.com/youtube/v3/videos"
                        stats_params = {
                            "part": "statistics,snippet",
                            "id": ",".join(video_ids),
                            "key": self.youtube_api_key
                        }
                        
                        async with self.session.get(stats_url, params=stats_params) as stats_resp:
                            if stats_resp.status == 200:
                                stats_data = await stats_resp.json()
                                
                                for video in stats_data.get('items', []):
                                    videos.append(self._normalize_youtube_video(video))
                                
                                self.logger.info(f"✅ YouTube: {len(videos)} vidéos collectées")
                            else:
                                self.logger.error(f"❌ YouTube stats error: {stats_resp.status}")
                                return self._get_youtube_demo_data(count)
                else:
                    self.logger.error(f"❌ YouTube API error: {resp.status}")
                    return self._get_youtube_demo_data(count)
        
        except Exception as e:
            self.logger.error(f"❌ Erreur YouTube: {e}")
            return self._get_youtube_demo_data(count)
        
        return videos
    
    async def collect_all_platforms(
        self,
        count_per_platform: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collecte données de TOUTES les plateformes en parallèle.
        
        Args:
            count_per_platform: Nombre de posts par plateforme
        
        Returns:
            Dict {'platform': [posts]}
        """
        
        self.logger.info("🚀 Démarrage collecte multiplateforme...")
        
        # Collecte en parallèle pour rapidité
        tasks = [
            self.collect_tiktok(count=count_per_platform),
            self.collect_instagram(count=count_per_platform),
            self.collect_youtube(count=count_per_platform),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Nettoyer les résultats (gérer les exceptions)
        tiktok_data = results[0] if isinstance(results[0], list) else []
        instagram_data = results[1] if isinstance(results[1], list) else []
        youtube_data = results[2] if isinstance(results[2], list) else []
        
        data = {
            'tiktok': tiktok_data,
            'instagram': instagram_data,
            'youtube': youtube_data,
        }
        
        total = sum(len(posts) for posts in data.values())
        self.logger.info(f"✅ Collecte terminée: {total} posts de {len(data)} plateformes")
        
        return data
    
    # =========================================================================
    # NORMALISATION - Format unifié pour toutes plateformes
    # =========================================================================
    
    def _normalize_tiktok_post(self, raw: Dict) -> Dict[str, Any]:
        """Normalise post TikTok vers format unifié"""
        return {
            'platform': 'tiktok',
            'id': raw.get('id'),
            'title': raw.get('video_description', '')[:300],
            'author': raw.get('username'),
            'created_at': raw.get('create_time'),
            'views': raw.get('view_count', 0),
            'likes': raw.get('like_count', 0),
            'comments': raw.get('comment_count', 0),
            'shares': raw.get('share_count', 0),
            'engagement_rate': self._calculate_engagement(
                raw.get('like_count', 0) + raw.get('comment_count', 0) + raw.get('share_count', 0),
                raw.get('view_count', 1)
            ),
            'is_viral': raw.get('view_count', 0) > 100000,
            'hashtags': raw.get('hashtag_names', []),
            'url': f"https://www.tiktok.com/@{raw.get('username')}/video/{raw.get('id')}"
        }
    
    def _normalize_instagram_post(self, raw: Dict) -> Dict[str, Any]:
        """Normalise post Instagram vers format unifié"""
        return {
            'platform': 'instagram',
            'id': raw.get('id'),
            'title': raw.get('caption', '')[:300],
            'author': raw.get('username'),
            'created_at': raw.get('timestamp'),
            'views': raw.get('like_count', 0) * 10,  # Approximation (Instagram ne donne pas views)
            'likes': raw.get('like_count', 0),
            'comments': raw.get('comments_count', 0),
            'shares': raw.get('like_count', 0) * 0.05,  # Approximation
            'engagement_rate': self._calculate_engagement(
                raw.get('like_count', 0) + raw.get('comments_count', 0),
                raw.get('like_count', 0) * 10
            ),
            'is_viral': raw.get('like_count', 0) > 10000,
            'media_type': raw.get('media_type'),
            'url': f"https://www.instagram.com/p/{raw.get('id')}"
        }
    
    def _normalize_youtube_video(self, raw: Dict) -> Dict[str, Any]:
        """Normalise vidéo YouTube vers format unifié"""
        stats = raw.get('statistics', {})
        snippet = raw.get('snippet', {})
        
        return {
            'platform': 'youtube',
            'id': raw.get('id'),
            'title': snippet.get('title', '')[:300],
            'author': snippet.get('channelTitle'),
            'created_at': snippet.get('publishedAt'),
            'views': int(stats.get('viewCount', 0)),
            'likes': int(stats.get('likeCount', 0)),
            'comments': int(stats.get('commentCount', 0)),
            'shares': 0,  # YouTube ne fournit pas ce chiffre
            'engagement_rate': self._calculate_engagement(
                int(stats.get('likeCount', 0)) + int(stats.get('commentCount', 0)),
                int(stats.get('viewCount', 1))
            ),
            'is_viral': int(stats.get('viewCount', 0)) > 1000000,
            'url': f"https://www.youtube.com/watch?v={raw.get('id')}"
        }
    
    def _calculate_engagement(self, total_interactions: int, views: int) -> float:
        """Calcule engagement rate"""
        return (total_interactions / views * 100) if views > 0 else 0
    
    # =========================================================================
    # DONNÉES DEMO (utilisées si pas d'API keys)
    # =========================================================================
    
    def _get_tiktok_demo_data(self, count: int) -> List[Dict]:
        """Données demo TikTok (pour tests)"""
        self.logger.info("📦 Utilisation données demo TikTok")
        # ... retourner des données factices basées sur patterns réels
        return []
    
    def _get_instagram_demo_data(self, count: int) -> List[Dict]:
        """Données demo Instagram"""
        self.logger.info("📦 Utilisation données demo Instagram")
        return []
    
    def _get_youtube_demo_data(self, count: int) -> List[Dict]:
        """Données demo YouTube"""
        self.logger.info("📦 Utilisation données demo YouTube")
        return []
    
    async def close(self):
        """Ferme la session HTTP"""
        if self.session:
            await self.session.close()
            self.session = None


# Singleton
_collector_instance = None

def get_multiplatform_collector() -> MultiPlatformCollector:
    """Retourne l'instance singleton du collecteur"""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = MultiPlatformCollector()
    return _collector_instance
