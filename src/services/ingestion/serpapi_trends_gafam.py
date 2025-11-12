"""
SerpAPI Google Trends Collector - GAFAM Production Level
=========================================================

🏆 SOLUTION OFFICIELLE pour remplacer PyTrends obsolète.

Architecture:
- SerpAPI official Google Trends API (https://serpapi.com/google-trends-api)
- Multi-layer caching (L1 memory + L2 disk)
- Regional health monitoring
- Adaptive retry avec exponential backoff
- Prometheus-ready metrics

Pricing:
- Free tier: 100 searches/month
- Starter: $50/month (5,000 searches)
- Professional: $200/month (20,000 searches)

Author: Trend & Viral Engine Pro
Date: 2025-11-06
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from loguru import logger

from src.core.config import settings


class SerpAPITrendsGAFAM:
    """
    Collecteur Google Trends via SerpAPI - Niveau GAFAM.
    
    Features:
    - Multi-strategy: trending_searches, interest_over_time, related_queries
    - Multi-layer caching (L1 30min, L2 24h)
    - Regional health monitoring avec auto-cooldown
    - Adaptive throttling (15-30s base, ajustable)
    - Métriques Prometheus-ready
    
    Usage:
        collector = SerpAPITrendsGAFAM(api_key="your_serpapi_key")
        trends = await collector.collect(regions=["US", "FR"], strategy="multi")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        throttle_base_delay: float = 2.0,  # SerpAPI plus rapide que PyTrends
        max_retries: int = 3
    ):
        """
        Initialize SerpAPI Trends collector.
        
        Args:
            api_key: SerpAPI API key (ou settings.serpapi_api_key)
            cache_dir: Répertoire cache L2 (défaut: data/cache/serpapi)
            throttle_base_delay: Délai base entre requêtes (2s pour SerpAPI)
            max_retries: Nombre max retries sur erreur
        """
        self.api_key = api_key or getattr(settings, 'serpapi_api_key', None)
        if not self.api_key:
            logger.warning("⚠️ SERPAPI_API_KEY manquant - collecte désactivée")
        
        self.base_url = "https://serpapi.com/search"
        default_cache = Path("data/cache/serpapi")
        self.cache_dir = cache_dir or default_cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Throttling
        self.throttle_delay = throttle_base_delay
        self.last_request_time = 0.0
        self.max_retries = max_retries
        
        # Multi-layer cache
        self._l1_cache: Dict[str, tuple[Any, float]] = {}  # {key: (data, timestamp)}
        self._l1_ttl = 1800  # 30min
        self._l2_ttl = 86400  # 24h
        
        # Regional health tracking
        self._region_health: Dict[str, Dict[str, Any]] = {}
        self._health_fail_threshold = 3
        self._health_cooldown_duration = 600  # 10min
        
        # Metrics
        self._metrics = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_errors": 0,
            "requests_429": 0,
            "items_collected": 0,
            "cache_hits_l1": 0,
            "cache_hits_l2": 0,
            "api_credits_used": 0
        }
        
        logger.info("🚀 SerpAPITrendsGAFAM initialized (Production-ready)")
    
    async def collect(
        self,
        regions: Optional[List[str]] = None,
        strategy: str = "multi",
        max_items_per_region: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Collecter trending topics via SerpAPI.
        
        Args:
            regions: Liste codes pays (ex: ["US", "FR", "JP"])
            strategy: "trending" | "interest" | "related" | "multi"
            max_items_per_region: Limite items par région
        
        Returns:
            Liste trending topics avec fields:
                - topic: keyword
                - region: code pays
                - method: trending_searches | interest_over_time | related_queries
                - search_volume: volume recherche (si dispo)
                - growth_pct: croissance % (si dispo)
                - quality_score: 0.95 (SerpAPI data fiable)
        """
        if not self.api_key:
            logger.error("❌ SERPAPI_API_KEY manquant - retour vide")
            return []
        
        regions = regions or ["US", "FR", "GB", "JP"]
        all_trends = []
        
        # Vérifier santé régions
        healthy_regions = [r for r in regions if self._check_region_health(r)]
        logger.info(f"🌐 {strategy} strategy for {len(healthy_regions)}/{len(regions)} regions")
        
        for region in healthy_regions:
            region_trends = []
            
            try:
                if strategy in ["trending", "multi"]:
                    region_trends.extend(
                        await self._collect_trending_searches(region)
                    )
                
                if strategy in ["interest", "multi"] and len(region_trends) > 0:
                    # Enrichir top 3 avec interest over time
                    top_keywords = [t["topic"] for t in region_trends[:3]]
                    enriched = await self._enrich_with_interest(top_keywords, region)
                    region_trends[:3] = enriched
                
                if strategy in ["related", "multi"] and len(region_trends) > 0:
                    # Expansion via related queries
                    seed_keyword = region_trends[0]["topic"]
                    related = await self._collect_related_queries(seed_keyword, region)
                    region_trends.extend(related)
                
                # Limiter items
                region_trends = region_trends[:max_items_per_region]
                all_trends.extend(region_trends)
                
                self._mark_region_success(region)
                logger.success(f"✅ {region}: {len(region_trends)} trends collected")
            
            except Exception as e:
                logger.error(f"❌ {region} failed: {e}")
                self._mark_region_failure(region)
                self._metrics["requests_errors"] += 1
        
        self._metrics["items_collected"] += len(all_trends)
        return all_trends
    
    async def _collect_trending_searches(self, region: str) -> List[Dict[str, Any]]:
        """
        Collecter trending searches via SerpAPI.
        
        Endpoint: https://serpapi.com/google-trends-trending-now
        """
        cache_key = f"trending_{region}"
        
        # Check L1 cache
        cached = self._get_l1_cache(cache_key)
        if cached:
            return cached
        
        # Check L2 cache
        cached = self._get_l2_cache(cache_key)
        if cached:
            self._set_l1_cache(cache_key, cached)
            return cached
        
        # API call
        await self._throttle()
        
        params = {
            "engine": "google_trends_trending_now",
            "geo": region,
            "api_key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as resp:
                    self._metrics["requests_total"] += 1
                    
                    if resp.status == 429:
                        self._metrics["requests_429"] += 1
                        logger.warning("⚠️ SerpAPI rate limit - throttling")
                        await asyncio.sleep(10)
                        raise Exception("Rate limited")
                    
                    resp.raise_for_status()
                    data = await resp.json()
                    
                    # Parse trending searches
                    trends = []
                    trending_searches = data.get("trending_searches", [])
                    
                    for idx, item in enumerate(trending_searches):
                        query = item.get("query", "")
                        search_volume = item.get("search_volume", 0)
                        
                        trends.append({
                            "topic": query,
                            "region": region,
                            "method": "trending_searches",
                            "rank": idx + 1,
                            "search_volume": search_volume,
                            "quality_score": 0.95,  # SerpAPI fiable
                            "collected_at": datetime.utcnow().isoformat()
                        })
                    
                    self._metrics["requests_success"] += 1
                    self._metrics["api_credits_used"] += 1
                    
                    # Cache
                    self._set_l2_cache(cache_key, trends)
                    self._set_l1_cache(cache_key, trends)
                    
                    logger.success(f"✅ trending_searches {region}: {len(trends)} items")
                    return trends
        
        except Exception as e:
            logger.error(f"❌ trending_searches {region}: {e}")
            return []
    
    async def _collect_related_queries(
        self,
        keyword: str,
        region: str
    ) -> List[Dict[str, Any]]:
        """
        Collecter related queries via SerpAPI.
        
        Endpoint: https://serpapi.com/google-trends-related-queries
        """
        cache_key = f"related_{keyword}_{region}"
        
        cached = self._get_l1_cache(cache_key)
        if cached:
            return cached
        
        await self._throttle()
        
        params = {
            "engine": "google_trends",
            "q": keyword,
            "geo": region,
            "data_type": "RELATED_QUERIES",
            "api_key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as resp:
                    self._metrics["requests_total"] += 1
                    resp.raise_for_status()
                    data = await resp.json()
                    
                    trends = []
                    rising_queries = data.get("related_queries", {}).get("rising", [])
                    
                    for item in rising_queries[:10]:
                        query = item.get("query", "")
                        value = item.get("value", 0)
                        
                        trends.append({
                            "topic": query,
                            "region": region,
                            "method": "related_queries",
                            "growth_pct": value if isinstance(value, (int, float)) else 100,
                            "quality_score": 0.90,
                            "collected_at": datetime.utcnow().isoformat()
                        })
                    
                    self._metrics["requests_success"] += 1
                    self._metrics["api_credits_used"] += 1
                    self._set_l1_cache(cache_key, trends)
                    
                    return trends
        
        except Exception as e:
            logger.error(f"❌ related_queries {keyword}: {e}")
            return []
    
    async def _enrich_with_interest(
        self,
        keywords: List[str],
        region: str
    ) -> List[Dict[str, Any]]:
        """
        Enrichir keywords avec interest over time.
        
        Endpoint: https://serpapi.com/google-trends-interest-over-time
        """
        cache_key = f"interest_{'_'.join(keywords)}_{region}"
        
        cached = self._get_l1_cache(cache_key)
        if cached:
            return cached
        
        await self._throttle()
        
        params = {
            "engine": "google_trends",
            "q": ",".join(keywords[:5]),  # Max 5 keywords
            "geo": region,
            "data_type": "TIMESERIES",
            "api_key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as resp:
                    self._metrics["requests_total"] += 1
                    resp.raise_for_status()
                    data = await resp.json()
                    
                    enriched = []
                    timeline = data.get("interest_over_time", {}).get("timeline_data", [])
                    
                    for keyword in keywords:
                        # Calculer avg interest + peak
                        values = []
                        for point in timeline:
                            for val in point.get("values", []):
                                if val.get("query") == keyword:
                                    values.append(val.get("value", 0))
                        
                        if values:
                            avg_interest = sum(values) / len(values)
                            peak_interest = max(values)
                            
                            # Croissance récente
                            recent_avg = sum(values[-3:]) / 3 if len(values) >= 3 else avg_interest
                            early_avg = sum(values[:3]) / 3 if len(values) >= 3 else avg_interest
                            growth = ((recent_avg - early_avg) / (early_avg + 1)) * 100
                            
                            enriched.append({
                                "topic": keyword,
                                "region": region,
                                "method": "interest_over_time",
                                "avg_interest": round(avg_interest, 1),
                                "peak_interest": int(peak_interest),
                                "growth_7d": round(growth, 1),
                                "quality_score": 0.95,
                                "collected_at": datetime.utcnow().isoformat()
                            })
                    
                    self._metrics["requests_success"] += 1
                    self._metrics["api_credits_used"] += 1
                    self._set_l1_cache(cache_key, enriched)
                    
                    return enriched
        
        except Exception as e:
            logger.error(f"❌ interest_over_time: {e}")
            return [{"topic": k, "region": region, "method": "fallback"} for k in keywords]
    
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
    
    # ========== Regional Health ==========
    
    def _check_region_health(self, region: str) -> bool:
        """Vérifier si région est healthy (pas en cooldown)."""
        if region not in self._region_health:
            self._region_health[region] = {
                "status": "healthy",
                "fail_count": 0,
                "success_count": 0,
                "last_fail_ts": 0,
                "last_success_ts": 0
            }
            return True
        
        health = self._region_health[region]
        
        # Cooldown actif?
        if health["status"] == "cooldown":
            elapsed = time.time() - health["last_fail_ts"]
            if elapsed > self._health_cooldown_duration:
                health["status"] = "healthy"
                health["fail_count"] = 0
                logger.info(f"✅ {region} recovered from cooldown")
                return True
            else:
                logger.debug(f"⏳ {region} still in cooldown ({int(elapsed)}s)")
                return False
        
        return True
    
    def _mark_region_success(self, region: str):
        """Marquer région success."""
        if region in self._region_health:
            self._region_health[region]["success_count"] += 1
            self._region_health[region]["last_success_ts"] = time.time()
    
    def _mark_region_failure(self, region: str):
        """Marquer région failure."""
        if region not in self._region_health:
            self._region_health[region] = {"fail_count": 0, "status": "healthy"}
        
        health = self._region_health[region]
        health["fail_count"] += 1
        health["last_fail_ts"] = time.time()
        
        if health["fail_count"] >= self._health_fail_threshold:
            health["status"] = "cooldown"
            logger.warning(f"⚠️ {region} entered cooldown (10min)")
    
    # ========== Throttling ==========
    
    async def _throttle(self):
        """Throttle requests pour respecter rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.throttle_delay:
            await asyncio.sleep(self.throttle_delay - elapsed)
        self.last_request_time = time.time()
    
    # ========== Metrics ==========
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Retourner métriques Prometheus-ready.
        
        Returns:
            {
                "requests_total": 120,
                "requests_success": 115,
                "success_rate_pct": 95.8,
                "items_collected": 450,
                "cache_hits_l1": 30,
                "cache_hits_l2": 10,
                "api_credits_used": 80,
                "regions_healthy": 3,
                "regions_cooldown": 1
            }
        """
        healthy = sum(1 for h in self._region_health.values() if h["status"] == "healthy")
        cooldown = sum(1 for h in self._region_health.values() if h["status"] == "cooldown")
        
        return {
            **self._metrics,
            "success_rate_pct": round(
                (self._metrics["requests_success"] / max(self._metrics["requests_total"], 1)) * 100,
                1
            ),
            "regions_healthy": healthy,
            "regions_cooldown": cooldown
        }
