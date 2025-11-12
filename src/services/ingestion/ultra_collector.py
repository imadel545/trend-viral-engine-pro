"""
🚀 ULTRA COLLECTOR - Orchestration 4 sources parallèles avec résilience maximale

Architecture:
- Circuit Breaker pour chaque source
- Bulkhead pattern (isolation des pannes)
- Cache distribué avec TTL intelligent
- Fallback multi-niveaux
- User-Agent rotation
- Proxy rotation (si configuré)
- Métriques Prometheus
"""

import asyncio
import random
from datetime import datetime
from typing import Any, Dict, List, Optional
from loguru import logger
import pandas as pd

from src.core.config import settings
from src.core.resilience import (
    CircuitBreaker,
    CacheLayer,
    FallbackStrategy,
    get_or_create_cache,
    get_or_create_breaker
)


class SourceCollector:
    """
    Collecteur ultra-robuste pour une source.
    
    Features:
    - Circuit breaker dédié
    - Cache avec TTL
    - Fallback strategy
    - Métriques détaillées
    """

    def __init__(
        self,
        name: str,
        collector_func: callable,
        cache_ttl: int = 3600,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ):
        self.name = name
        self.collector_func = collector_func
        
        # Circuit breaker dédié
        self.breaker = get_or_create_breaker(
            name=f"breaker_{name}",
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
        
        # Cache dédié
        self.cache = get_or_create_cache(
            name=f"cache_{name}",
            ttl=cache_ttl,
            max_size=500
        )
        
        # Fallback strategy
        self.fallback = FallbackStrategy(name=name)
        
        # Métriques
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.cache_hits = 0
        self.fallback_uses = 0
        
        logger.info(f"🔧 SourceCollector '{name}' initialized")

    async def collect(
        self,
        force_refresh: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Collecte données avec résilience maximale.
        
        Args:
            force_refresh: Force refresh (ignore cache)
            **kwargs: Arguments pour le collector
        
        Returns:
            Liste de tendances collectées
        """
        self.total_requests += 1
        
        # Build cache key (handle unhashable types like lists)
        import json
        cache_key = f"{self.name}_{hash(json.dumps(kwargs, sort_keys=True, default=str))}"
        
        # 1. Check cache (si pas force refresh)
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached is not None:
                self.cache_hits += 1
                logger.info(f"💾 {self.name}: Using cached data (hit rate: {self.cache_hits}/{self.total_requests})")
                return cached
        
        # 2. Try collection avec circuit breaker
        try:
            logger.info(f"🌐 {self.name}: Fetching fresh data...")
            
            async def protected_call():
                if asyncio.iscoroutinefunction(self.collector_func):
                    return await self.collector_func(**kwargs)
                return self.collector_func(**kwargs)
            
            results = await self.breaker.call(protected_call)
            
            # Success: update metrics et cache
            self.successful_requests += 1
            self.cache.set(cache_key, results)
            
            logger.success(f"✅ {self.name}: {len(results)} items collected")
            return results
            
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"❌ {self.name}: Collection failed - {e}")
            
            # 3. Fallback strategy
            fallback_data = await self.fallback.get_fallback(
                error=e,
                cache=self.cache,
                cache_key=cache_key,
                synthetic_generator=self._generate_synthetic_data
            )
            
            if fallback_data:
                self.fallback_uses += 1
                logger.warning(f"🔄 {self.name}: Using fallback data ({len(fallback_data)} items)")
                return fallback_data
            
            # 4. Return empty if all fails
            logger.error(f"⚠️ {self.name}: All strategies failed - returning empty")
            return []

    def _generate_synthetic_data(self) -> List[Dict[str, Any]]:
        """
        Génère données synthétiques pour tests/fallback.
        
        NOTE: À remplacer par vraies données historiques en production.
        """
        logger.debug(f"🎲 {self.name}: Generating synthetic data")
        
        synthetic_trends = [
            {
                "title": f"Synthetic Trend {i+1}",
                "source": self.name,
                "collected_at": datetime.now().isoformat(),
                "score": random.uniform(0.5, 0.9),
                "metadata": {"synthetic": True}
            }
            for i in range(5)
        ]
        
        return synthetic_trends

    def get_metrics(self) -> Dict[str, Any]:
        """Métriques détaillées du collecteur."""
        success_rate = (
            (self.successful_requests / self.total_requests * 100)
            if self.total_requests > 0 else 0
        )
        
        return {
            "source": self.name,
            "total_requests": self.total_requests,
            "successful": self.successful_requests,
            "failed": self.failed_requests,
            "success_rate": f"{success_rate:.1f}%",
            "cache_hits": self.cache_hits,
            "fallback_uses": self.fallback_uses,
            "cache_stats": self.cache.stats(),
            "breaker_state": self.breaker.state.value
        }


class UltraCollector:
    """
    Orchestrateur ultra-robuste pour 4 sources parallèles.
    
    Architecture Bulkhead:
    - Chaque source isolée avec son circuit breaker
    - Exécution parallèle avec asyncio.gather
    - Agrégation intelligente des résultats
    - Métriques consolidées
    
    Sources:
    1. Reddit (asyncpraw)
    2. Google Trends (pytrends + anti-rate-limiting)
    3. Facebook Graph API (v18.0)
    4. TikTok Creative Center (OAuth)
    """

    def __init__(self):
        self.collectors: Dict[str, SourceCollector] = {}
        self._initialized = False
        
        logger.info("🚀 UltraCollector initializing...")

    async def initialize(self):
        """
        Initialise les 4 collecteurs sources.
        
        NOTE: Les fonctions collector seront importées dynamiquement
        pour éviter circular imports.
        """
        if self._initialized:
            return
        
        logger.info("🔧 Initializing 5 source collectors...")
        
        # Import collectors dynamiquement
        from src.services.ingestion.advanced_sources import (
            EnhancedRedditSource,
            FacebookGraphAPISource,
            TikTokCreativeCenterSource
        )
        from src.services.ingestion.serpapi_trends_gafam import SerpAPITrendsGAFAM
        from src.services.ingestion.twitter_trends_gafam import TwitterTrendsGAFAM
        
        # 1. SerpAPI Google Trends Collector (PRODUCTION - Priorité 1)
        import os
        serpapi_key = os.getenv("SERPAPI_API_KEY")
        serpapi_source = SerpAPITrendsGAFAM(api_key=serpapi_key)
        self.collectors["serpapi"] = SourceCollector(
            name="serpapi",
            collector_func=serpapi_source.collect,
            cache_ttl=3600,  # 1 heure (données officielles Google stables)
            failure_threshold=3,
            recovery_timeout=180
        )
        
        # 2. Twitter Trends Collector (PRODUCTION - Priorité 2)
        twitter_token = os.getenv("TWITTER_BEARER_TOKEN")
        twitter_source = TwitterTrendsGAFAM(bearer_token=twitter_token)
        self.collectors["twitter"] = SourceCollector(
            name="twitter",
            collector_func=twitter_source.collect,
            cache_ttl=1800,  # 30 min (trending topics volatiles)
            failure_threshold=3,
            recovery_timeout=120
        )
        
        # 3. Reddit Collector (EXCELLENT 5/5)
        reddit_source = EnhancedRedditSource()
        self.collectors["reddit"] = SourceCollector(
            name="reddit",
            collector_func=reddit_source.collect,
            cache_ttl=1800,  # 30 min (données sociales volatiles)
            failure_threshold=3,
            recovery_timeout=120
        )
        
        # 4. Facebook Collector (BON 3/5)
        facebook_source = FacebookGraphAPISource()
        self.collectors["facebook"] = SourceCollector(
            name="facebook",
            collector_func=facebook_source.collect,
            cache_ttl=1800,  # 30 min
            failure_threshold=3,
            recovery_timeout=120
        )
        
        # 4. TikTok Collector (BON 3/5)
        tiktok_source = TikTokCreativeCenterSource()
        self.collectors["tiktok"] = SourceCollector(
            name="tiktok",
            collector_func=tiktok_source.collect,
            cache_ttl=1800,  # 30 min
            failure_threshold=3,
            recovery_timeout=120
        )
        
        self._initialized = True
        logger.success("✅ 5 source collectors initialized (SerpAPI + Twitter + Reddit + Facebook + TikTok)")

    async def collect_all(
        self,
        force_refresh: bool = False,
        sources: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collecte données de toutes les sources en parallèle.
        
        Args:
            force_refresh: Force refresh (ignore cache)
            sources: Liste sources spécifiques (None = toutes)
            **kwargs: Arguments pour chaque collector
        
        Returns:
            Dict[source_name, List[trends]]
        
        Example:
            results = await collector.collect_all(
                sources=["reddit", "google_trends"],
                reddit={"subreddits": ["viral", "videos", "trending"], "limit": 50},
                google_trends={"regions": ["FR", "US"]}
            )
        """
        await self.initialize()
        
        # Sélectionner sources
        selected_sources = sources or list(self.collectors.keys())
        
        logger.info(f"🌐 Collecting from {len(selected_sources)} sources: {selected_sources}")
        
        # Préparer tasks parallèles (Bulkhead pattern)
        tasks = {}
        for source_name in selected_sources:
            if source_name not in self.collectors:
                logger.warning(f"⚠️ Unknown source: {source_name} - skipping")
                continue
            
            collector = self.collectors[source_name]
            
            # Extraire kwargs spécifiques à cette source
            source_kwargs = kwargs.get(source_name, {})
            
            # Créer task
            tasks[source_name] = asyncio.create_task(
                collector.collect(force_refresh=force_refresh, **source_kwargs)
            )
        
        # Exécuter en parallèle avec gather (return_exceptions=True pour isolation)
        logger.info(f"⚡ Executing {len(tasks)} parallel collections...")
        results_list = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Agréger résultats
        results = {}
        for source_name, result in zip(tasks.keys(), results_list):
            if isinstance(result, Exception):
                logger.error(f"❌ {source_name} failed: {result}")
                results[source_name] = []
            else:
                results[source_name] = result
                logger.success(f"✅ {source_name}: {len(result)} items")
        
        # Log summary
        total_items = sum(len(items) for items in results.values())
        successful_sources = sum(1 for items in results.values() if len(items) > 0)
        
        logger.info(
            f"📊 Collection complete: {successful_sources}/{len(selected_sources)} sources OK, "
            f"{total_items} total items"
        )
        
        return results

    async def collect_batch(
        self,
        target_count: int = 100,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Collecte batch avec target count.
        
        Strategy:
        1. Collecte toutes sources en parallèle
        2. Agrège résultats
        3. Si < target_count, retry avec force_refresh
        4. Sauvegarde en Parquet
        
        Args:
            target_count: Nombre minimum de tendances
            force_refresh: Force refresh
        
        Returns:
            DataFrame avec toutes les tendances
        """
        logger.info(f"🎯 Batch collection: target={target_count} items")
        
        # Collecte initiale
        results = await self.collect_all(force_refresh=force_refresh)
        
        # Agréger
        all_trends = []
        for source, trends in results.items():
            for trend in trends:
                trend["source"] = source  # Ensure source field
                all_trends.append(trend)
        
        # Check target
        if len(all_trends) < target_count and not force_refresh:
            logger.warning(f"⚠️ Only {len(all_trends)}/{target_count} items - retrying with force_refresh")
            results = await self.collect_all(force_refresh=True)
            
            all_trends = []
            for source, trends in results.items():
                for trend in trends:
                    trend["source"] = source
                    all_trends.append(trend)
        
        # Convert to DataFrame
        if not all_trends:
            logger.error("❌ No trends collected from any source")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_trends)
        
        # Ensure collected_at
        if "collected_at" not in df.columns:
            df["collected_at"] = datetime.now().isoformat()
        
        logger.success(f"✅ Batch complete: {len(df)} items from {df['source'].nunique()} sources")
        
        return df

    def get_all_metrics(self) -> Dict[str, Any]:
        """Métriques consolidées de toutes les sources."""
        metrics = {
            "collectors": {},
            "summary": {
                "total_sources": len(self.collectors),
                "total_requests": 0,
                "total_successful": 0,
                "total_failed": 0,
                "sources_healthy": 0
            }
        }
        
        for name, collector in self.collectors.items():
            collector_metrics = collector.get_metrics()
            metrics["collectors"][name] = collector_metrics
            
            # Update summary
            metrics["summary"]["total_requests"] += collector_metrics["total_requests"]
            metrics["summary"]["total_successful"] += collector_metrics["successful"]
            metrics["summary"]["total_failed"] += collector_metrics["failed"]
            
            if collector_metrics["breaker_state"] == "closed":
                metrics["summary"]["sources_healthy"] += 1
        
        # Calculate global success rate
        total_req = metrics["summary"]["total_requests"]
        total_ok = metrics["summary"]["total_successful"]
        metrics["summary"]["global_success_rate"] = (
            f"{(total_ok / total_req * 100):.1f}%"
            if total_req > 0 else "0.0%"
        )
        
        return metrics


# Singleton instance
_ultra_collector_instance: Optional[UltraCollector] = None


def get_ultra_collector() -> UltraCollector:
    """Get or create UltraCollector singleton."""
    global _ultra_collector_instance
    if _ultra_collector_instance is None:
        _ultra_collector_instance = UltraCollector()
    return _ultra_collector_instance
