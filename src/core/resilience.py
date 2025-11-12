"""
🏗️ RESILIENCE PATTERNS - Circuit Breaker, Bulkhead, Cache, Fallback

Architecture patterns utilisés par Netflix (Hystrix), AWS, Google.
Garantit la robustesse du système même en cas de pannes partielles.
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from loguru import logger


class CircuitState(Enum):
    """État du circuit breaker."""
    CLOSED = "closed"  # Normal - requêtes passent
    OPEN = "open"      # Erreurs détectées - requêtes bloquées
    HALF_OPEN = "half_open"  # Test - vérification si service récupéré


class CircuitBreaker:
    """
    Circuit Breaker pattern (Netflix Hystrix).
    
    Protège contre les cascades de pannes en ouvrant le circuit
    après un seuil d'erreurs, puis le teste périodiquement.
    
    States:
    - CLOSED: Service OK, requêtes passent
    - OPEN: Service down, requêtes rejetées immédiatement
    - HALF_OPEN: Test de récupération
    
    Example:
        breaker = CircuitBreaker(
            failure_threshold=5,  # 5 erreurs consécutives
            recovery_timeout=60,  # 60s avant retry
            expected_exception=APIError
        )
        
        @breaker
        async def call_api():
            return await external_api.get()
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        success_threshold: int = 2,
        name: str = "circuit"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        self.name = name
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        
        logger.info(f"🔌 Circuit Breaker '{name}' initialized (threshold={failure_threshold}, timeout={recovery_timeout}s)")

    def _should_attempt_reset(self) -> bool:
        """Vérifie si on doit tester la récupération."""
        return (
            self.state == CircuitState.OPEN
            and self.last_failure_time is not None
            and time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _record_success(self):
        """Enregistre un succès."""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info(f"✅ Circuit '{self.name}' CLOSED (récupéré)")
                self.state = CircuitState.CLOSED
                self.success_count = 0

    def _record_failure(self):
        """Enregistre un échec."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.warning(f"🔴 Circuit '{self.name}' OPEN ({self.failure_count} failures)")
                self.state = CircuitState.OPEN

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Exécute la fonction avec protection circuit breaker.
        
        Raises:
            CircuitBreakerOpenError: Si circuit ouvert
            expected_exception: Si fonction échoue
        """
        # Si circuit ouvert, vérifier si on peut tester la récupération
        if self._should_attempt_reset():
            logger.info(f"🔶 Circuit '{self.name}' HALF_OPEN (testing recovery)")
            self.state = CircuitState.HALF_OPEN
        
        # Si circuit ouvert, rejeter immédiatement
        if self.state == CircuitState.OPEN:
            logger.warning(f"⚠️ Circuit '{self.name}' OPEN - request rejected")
            raise CircuitBreakerOpenError(f"Circuit '{self.name}' is OPEN")
        
        # Tenter l'appel
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self._record_success()
            return result
            
        except self.expected_exception as e:
            self._record_failure()
            logger.error(f"❌ Circuit '{self.name}' failure: {e}")
            raise

    def __call__(self, func: Callable) -> Callable:
        """Decorator pour circuit breaker."""
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper


class CircuitBreakerOpenError(Exception):
    """Circuit breaker ouvert - service temporairement indisponible."""
    pass


class CacheLayer:
    """
    Cache intelligent avec TTL et LRU.
    
    Features:
    - TTL (Time To Live) configurable
    - LRU (Least Recently Used) eviction
    - Hit/Miss tracking pour monitoring
    - Async-safe
    
    Example:
        cache = CacheLayer(ttl=3600, max_size=1000)
        
        # Get with fallback
        data = await cache.get_or_set(
            key="trends_FR",
            fallback=lambda: fetch_trends("FR"),
            ttl=1800
        )
    """

    def __init__(self, ttl: int = 3600, max_size: int = 1000, name: str = "cache"):
        self.ttl = ttl
        self.max_size = max_size
        self.name = name
        
        self._cache: Dict[str, tuple[Any, float]] = {}  # key -> (value, expire_time)
        self._access_times: Dict[str, float] = {}  # key -> last_access_time
        
        self.hits = 0
        self.misses = 0
        
        logger.info(f"💾 Cache '{name}' initialized (TTL={ttl}s, max_size={max_size})")

    def _is_expired(self, key: str) -> bool:
        """Vérifie si la clé est expirée."""
        if key not in self._cache:
            return True
        
        _, expire_time = self._cache[key]
        return time.time() > expire_time

    def _evict_lru(self):
        """Éviction LRU si cache plein."""
        if len(self._cache) >= self.max_size:
            # Trouver clé la moins récemment utilisée
            lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
            del self._cache[lru_key]
            del self._access_times[lru_key]
            logger.debug(f"🗑️ Cache '{self.name}' evicted LRU key: {lru_key}")

    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        if self._is_expired(key):
            self.misses += 1
            if key in self._cache:
                del self._cache[key]
                del self._access_times[key]
            return None
        
        self.hits += 1
        self._access_times[key] = time.time()
        value, _ = self._cache[key]
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Stocke une valeur dans le cache."""
        self._evict_lru()
        
        expire_time = time.time() + (ttl or self.ttl)
        self._cache[key] = (value, expire_time)
        self._access_times[key] = time.time()

    async def get_or_set(
        self,
        key: str,
        fallback: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get avec fallback si miss.
        
        Args:
            key: Clé cache
            fallback: Fonction async/sync pour récupérer la valeur
            ttl: TTL custom (optionnel)
        """
        cached = self.get(key)
        if cached is not None:
            logger.debug(f"💾 Cache '{self.name}' HIT: {key}")
            return cached
        
        logger.debug(f"❌ Cache '{self.name}' MISS: {key}")
        
        # Appeler fallback
        if asyncio.iscoroutinefunction(fallback):
            value = await fallback()
        else:
            value = fallback()
        
        self.set(key, value, ttl)
        return value

    def clear(self):
        """Vide le cache."""
        self._cache.clear()
        self._access_times.clear()
        logger.info(f"🗑️ Cache '{self.name}' cleared")

    def stats(self) -> Dict[str, Any]:
        """Statistiques du cache."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "name": self.name,
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl": self.ttl
        }


class FallbackStrategy:
    """
    Fallback strategy pour données de secours.
    
    Utilisé quand la source principale échoue:
    1. Cache (si disponible)
    2. Données historiques
    3. Données synthétiques
    4. Empty result
    """

    def __init__(self, name: str = "fallback"):
        self.name = name
        self.fallback_count = 0

    async def get_fallback(
        self,
        error: Exception,
        cache: Optional[CacheLayer] = None,
        cache_key: Optional[str] = None,
        synthetic_generator: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère données de fallback.
        
        Priority:
        1. Stale cache (données expirées mais présentes)
        2. Synthetic data generator
        3. Empty list
        """
        self.fallback_count += 1
        logger.warning(f"🔄 Fallback '{self.name}' triggered (count={self.fallback_count}): {error}")
        
        # Try stale cache
        if cache and cache_key:
            # Force get même si expiré
            if cache_key in cache._cache:
                value, _ = cache._cache[cache_key]
                logger.info(f"📦 Using stale cache for '{cache_key}'")
                return value
        
        # Try synthetic data
        if synthetic_generator:
            logger.info(f"🎲 Generating synthetic data for '{self.name}'")
            if asyncio.iscoroutinefunction(synthetic_generator):
                return await synthetic_generator()
            return synthetic_generator()
        
        # Return empty
        logger.warning(f"⚠️ No fallback available for '{self.name}' - returning empty")
        return []


# Global instances (can be used across services)
_global_caches: Dict[str, CacheLayer] = {}
_global_breakers: Dict[str, CircuitBreaker] = {}


def get_or_create_cache(name: str, ttl: int = 3600, max_size: int = 1000) -> CacheLayer:
    """Get or create global cache instance."""
    if name not in _global_caches:
        _global_caches[name] = CacheLayer(ttl=ttl, max_size=max_size, name=name)
    return _global_caches[name]


def get_or_create_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60
) -> CircuitBreaker:
    """Get or create global circuit breaker instance."""
    if name not in _global_breakers:
        _global_breakers[name] = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            name=name
        )
    return _global_breakers[name]
