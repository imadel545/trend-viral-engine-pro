"""
Twitter Trending Topics Collector - GAFAM Production Level
===========================================================

🏆 Alternative/Complément à SerpAPI pour trending content.

Architecture:
- Twitter API v2 official (trending topics endpoint)
- Multi-region support (WOEIDs)
- Multi-layer caching (L1 memory + L2 disk)
- Rate limiting géré (75 req/15min free tier)
- Prometheus-ready metrics

Pricing:
- Free tier: 1,500 tweets/month
- Basic: $100/month (10,000 tweets)
- Pro: $5,000/month (1M tweets)

Author: Trend & Viral Engine Pro
Date: 2025-11-06
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from loguru import logger

from src.core.config import settings


# WOEIDs (Where On Earth IDs) - Yahoo! Geographic Codes
WOEIDS = {
    "Worldwide": 1,
    "US": 23424977,
    "France": 23424819,
    "Paris": 615702,
    "UK": 23424975,
    "London": 44418,
    "Canada": 23424775,
    "Brazil": 23424768,
    "Japan": 23424856,
    "Tokyo": 1118370,
    "India": 23424848,
    "Germany": 23424829,
    "Spain": 23424950,
    "Italy": 23424853,
    "Australia": 23424748,
}


class TwitterTrendsGAFAM:
    """
    Collecteur Twitter Trending Topics via API v2 - Niveau GAFAM.
    
    Features:
    - Trending topics par région (WOEIDs)
    - Hashtags + tweet volumes
    - Multi-layer caching (L1 30min, L2 24h)
    - Rate limiting respecté (75 req/15min)
    - Métriques Prometheus-ready
    
    Usage:
        collector = TwitterTrendsGAFAM(bearer_token="your_token")
        trends = await collector.collect(regions=["US", "France"])
    """
    
    def __init__(
        self,
        bearer_token: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        rate_limit_window: int = 900  # 15 minutes
    ):
        """
        Initialize Twitter Trends collector.
        
        Args:
            bearer_token: Twitter API v2 Bearer Token
            cache_dir: Répertoire cache L2
            rate_limit_window: Fenêtre rate limit (900s = 15min)
        """
        self.bearer_token = bearer_token or getattr(settings, 'twitter_bearer_token', None)
        if not self.bearer_token:
            logger.warning("⚠️ TWITTER_BEARER_TOKEN manquant - collecte désactivée")
        
        self.base_url = "https://api.twitter.com/1.1"  # v1.1 pour trends/place
        default_cache = Path("data/cache/twitter")
        self.cache_dir = cache_dir or default_cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting (75 req/15min pour free tier)
        self.rate_limit_window = rate_limit_window
        self.rate_limit_max = 75
        self._request_timestamps: List[float] = []
        
        # Multi-layer cache
        self._l1_cache: Dict[str, tuple[Any, float]] = {}
        self._l1_ttl = 1800  # 30min
        self._l2_ttl = 86400  # 24h
        
        # Metrics
        self._metrics = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_errors": 0,
            "requests_rate_limited": 0,
            "items_collected": 0,
            "cache_hits_l1": 0,
            "cache_hits_l2": 0,
        }
        
        logger.info("🚀 TwitterTrendsGAFAM initialized (Production-ready)")
    
    async def collect(
        self,
        regions: Optional[List[str]] = None,
        max_items_per_region: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Collecter trending topics Twitter.
        
        Args:
            regions: Liste noms régions (ex: ["US", "France", "UK"])
            max_items_per_region: Limite items par région
        
        Returns:
            Liste trending topics avec fields:
                - topic: nom trend (ex: "#Python", "Elon Musk")
                - region: nom région
                - method: twitter_trending
                - tweet_volume: nombre tweets (peut être None)
                - url: URL Twitter search
                - quality_score: 0.92
        """
        if not self.bearer_token:
            logger.error("❌ TWITTER_BEARER_TOKEN manquant - retour vide")
            return []
        
        regions = regions or ["Worldwide", "US", "France"]
        all_trends = []
        
        logger.info(f"🌐 Collecting Twitter trends for {len(regions)} regions")
        
        for region_name in regions:
            try:
                # Vérifier rate limiting
                await self._check_rate_limit()
                
                # Récupérer WOEID
                woeid = WOEIDS.get(region_name)
                if not woeid:
                    logger.warning(f"⚠️ WOEID unknown for {region_name}, skipping")
                    continue
                
                # Check cache
                cache_key = f"twitter_trends_{woeid}"
                cached = self._get_l1_cache(cache_key)
                if cached:
                    all_trends.extend(cached[:max_items_per_region])
                    logger.info(f"💾 {region_name}: {len(cached)} trends (L1 cache)")
                    continue
                
                cached = self._get_l2_cache(cache_key)
                if cached:
                    self._set_l1_cache(cache_key, cached)
                    all_trends.extend(cached[:max_items_per_region])
                    logger.info(f"💾 {region_name}: {len(cached)} trends (L2 cache)")
                    continue
                
                # API call
                region_trends = await self._get_trends_for_woeid(woeid, region_name)
                
                # Cache
                self._set_l2_cache(cache_key, region_trends)
                self._set_l1_cache(cache_key, region_trends)
                
                all_trends.extend(region_trends[:max_items_per_region])
                logger.success(f"✅ {region_name}: {len(region_trends)} trends collected")
            
            except Exception as e:
                logger.error(f"❌ {region_name} failed: {e}")
                self._metrics["requests_errors"] += 1
        
        self._metrics["items_collected"] += len(all_trends)
        return all_trends
    
    async def _get_trends_for_woeid(
        self,
        woeid: int,
        region_name: str
    ) -> List[Dict[str, Any]]:
        """
        Récupérer trending topics pour un WOEID.
        
        Endpoint: GET /1.1/trends/place.json
        """
        url = f"{self.base_url}/trends/place.json"
        params = {"id": woeid}
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    self._metrics["requests_total"] += 1
                    self._request_timestamps.append(time.time())
                    
                    if resp.status == 429:
                        self._metrics["requests_rate_limited"] += 1
                        logger.warning("⚠️ Twitter rate limit hit - waiting 15min")
                        raise Exception("Rate limited")
                    
                    resp.raise_for_status()
                    data = await resp.json()
                    
                    # Parse trends
                    trends = []
                    if data and len(data) > 0:
                        trend_list = data[0].get("trends", [])
                        
                        for trend_item in trend_list:
                            name = trend_item.get("name", "")
                            url_twitter = trend_item.get("url", "")
                            tweet_volume = trend_item.get("tweet_volume")
                            
                            trends.append({
                                "topic": name,
                                "region": region_name,
                                "method": "twitter_trending",
                                "tweet_volume": tweet_volume,
                                "url": url_twitter,
                                "quality_score": 0.92,
                                "collected_at": datetime.utcnow().isoformat()
                            })
                    
                    self._metrics["requests_success"] += 1
                    return trends
        
        except Exception as e:
            logger.error(f"❌ Twitter API error for WOEID {woeid}: {e}")
            raise
    
    async def _check_rate_limit(self):
        """
        Vérifier et respecter rate limiting (75 req/15min).
        """
        now = time.time()
        
        # Nettoyer timestamps anciens (> 15min)
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if now - ts < self.rate_limit_window
        ]
        
        # Si limite atteinte, attendre
        if len(self._request_timestamps) >= self.rate_limit_max:
            oldest_ts = min(self._request_timestamps)
            wait_time = self.rate_limit_window - (now - oldest_ts)
            
            if wait_time > 0:
                logger.warning(f"⏳ Rate limit reached, waiting {wait_time:.0f}s")
                await asyncio.sleep(wait_time)
    
    # ========== Caching ==========
    
    def _get_l1_cache(self, key: str) -> Optional[Any]:
        """Récupérer données L1 cache (memory)."""
        if key in self._l1_cache:
            data, ts = self._l1_cache[key]
            if time.time() - ts < self._l1_ttl:
                self._metrics["cache_hits_l1"] += 1
                logger.debug(f"💾 L1 cache HIT: {key}")
                return data
            else:
                del self._l1_cache[key]
        return None
    
    def _set_l1_cache(self, key: str, data: Any):
        """Sauvegarder données L1 cache."""
        self._l1_cache[key] = (data, time.time())
    
    def _get_l2_cache(self, key: str) -> Optional[Any]:
        """Récupérer données L2 cache (disk)."""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.json"
        if cache_file.exists():
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime < self._l2_ttl:
                with cache_file.open("r") as f:
                    data = json.load(f)
                self._metrics["cache_hits_l2"] += 1
                logger.debug(f"💾 L2 cache HIT: {key}")
                return data
        return None
    
    def _set_l2_cache(self, key: str, data: Any):
        """Sauvegarder données L2 cache."""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.json"
        with cache_file.open("w") as f:
            json.dump(data, f)
    
    def _hash_key(self, key: str) -> str:
        """Hash clé cache pour nom fichier."""
        return hashlib.md5(key.encode()).hexdigest()
    
    # ========== Metrics ==========
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Retourner métriques Prometheus-ready.
        
        Returns:
            {
                "requests_total": 50,
                "requests_success": 48,
                "success_rate_pct": 96.0,
                "items_collected": 240,
                "cache_hits_l1": 10,
                "cache_hits_l2": 5,
                "rate_limited_count": 1,
                "current_rate_limit_usage": 50
            }
        """
        now = time.time()
        recent_requests = [
            ts for ts in self._request_timestamps
            if now - ts < self.rate_limit_window
        ]
        
        return {
            **self._metrics,
            "success_rate_pct": round(
                (self._metrics["requests_success"] / max(self._metrics["requests_total"], 1)) * 100,
                1
            ),
            "current_rate_limit_usage": len(recent_requests),
            "rate_limit_max": self.rate_limit_max
        }
    
    @staticmethod
    def list_available_regions() -> List[str]:
        """Retourner liste régions disponibles."""
        return list(WOEIDS.keys())
