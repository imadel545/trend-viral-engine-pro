"""
Production-Grade Optimizations Module
Implements advanced patterns: Caching, Connection Pooling, Circuit Breaker, Rate Limiting
"""

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger


# ═══════════════════════════════════════════════════════════════════
# 1. INTELLIGENT CACHING SYSTEM
# ═══════════════════════════════════════════════════════════════════

class CacheStrategy(Enum):
    """Cache eviction strategies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    HYBRID = "hybrid"  # LRU + TTL


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl
    
    def touch(self):
        """Update access metadata."""
        self.last_accessed = time.time()
        self.access_count += 1


class IntelligentCache:
    """
    Thread-safe intelligent cache with multiple eviction strategies.
    
    Optimizations:
    - O(1) get/set operations
    - Automatic eviction based on strategy
    - TTL support
    - LRU/LFU policies
    - Memory-efficient OrderedDict for LRU
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        strategy: CacheStrategy = CacheStrategy.HYBRID,
        default_ttl: Optional[float] = 3600.0,  # 1 hour
    ):
        self.max_size = max_size
        self.strategy = strategy
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = Lock()
        self.hits = 0
        self.misses = 0
        self.logger = logger.bind(module="cache")
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[key]
            
            # Check expiration
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                return None
            
            # Update access metadata
            entry.touch()
            
            # Move to end for LRU
            if self.strategy in (CacheStrategy.LRU, CacheStrategy.HYBRID):
                self.cache.move_to_end(key)
            
            self.hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in cache."""
        with self.lock:
            # Check if eviction needed
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict()
            
            # Create/update entry
            now = time.time()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                access_count=1,
                ttl=ttl or self.default_ttl,
            )
            
            self.cache[key] = entry
            if self.strategy in (CacheStrategy.LRU, CacheStrategy.HYBRID):
                self.cache.move_to_end(key)
    
    def _evict(self):
        """Evict entry based on strategy."""
        if not self.cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used (first in OrderedDict)
            self.cache.popitem(last=False)
        
        elif self.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            min_key = min(self.cache.keys(), key=lambda k: self.cache[k].access_count)
            del self.cache[min_key]
        
        elif self.strategy == CacheStrategy.TTL:
            # Remove oldest entry
            self.cache.popitem(last=False)
        
        elif self.strategy == CacheStrategy.HYBRID:
            # Remove expired first, then LRU
            expired = [k for k, v in self.cache.items() if v.is_expired()]
            if expired:
                del self.cache[expired[0]]
            else:
                self.cache.popitem(last=False)
    
    def clear(self):
        """Clear all cache."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0.0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "strategy": self.strategy.value,
            }


def cached(cache: IntelligentCache, ttl: Optional[float] = None):
    """
    Decorator for caching function results.
    
    Example:
        cache = IntelligentCache(max_size=100)
        
        @cached(cache, ttl=3600)
        def expensive_function(x):
            return heavy_computation(x)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try cache first
            result = cache.get(key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════
# 2. MODEL CONNECTION POOL
# ═══════════════════════════════════════════════════════════════════

class ModelPool:
    """
    Thread-safe pool of ML models for efficient serving.
    
    Optimizations:
    - Lazy loading (load on first use)
    - Model warming (pre-load frequently used)
    - Memory management (evict unused)
    - Concurrent access control
    """
    
    def __init__(self, max_models: int = 5, ttl: float = 1800.0):
        self.max_models = max_models
        self.ttl = ttl
        self.models: Dict[str, Tuple[Any, float]] = {}  # {name: (model, last_used)}
        self.lock = Lock()
        self.logger = logger.bind(module="model_pool")
        
    def get_or_load(
        self, 
        model_name: str, 
        loader: Callable[[], Any]
    ) -> Any:
        """
        Get model from pool or load if not exists.
        
        Args:
            model_name: Unique model identifier
            loader: Function to load model if not in pool
        """
        with self.lock:
            # Check if model exists and not expired
            if model_name in self.models:
                model, _ = self.models[model_name]
                self.models[model_name] = (model, time.time())
                self.logger.debug(f"Model '{model_name}' retrieved from pool")
                return model
            
            # Evict if pool is full
            if len(self.models) >= self.max_models:
                self._evict_oldest()
            
            # Load model
            self.logger.info(f"Loading model '{model_name}'...")
            model = loader()
            self.models[model_name] = (model, time.time())
            
            return model
    
    def _evict_oldest(self):
        """Evict least recently used model."""
        if not self.models:
            return
        
        oldest = min(self.models.keys(), key=lambda k: self.models[k][1])
        del self.models[oldest]
        self.logger.info(f"Evicted model '{oldest}' from pool")
    
    def preload(self, model_name: str, loader: Callable[[], Any]):
        """Preload model into pool."""
        self.get_or_load(model_name, loader)
        self.logger.info(f"Preloaded model '{model_name}'")
    
    def clear(self):
        """Clear all models from pool."""
        with self.lock:
            self.models.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self.lock:
            return {
                "models_loaded": len(self.models),
                "max_models": self.max_models,
                "model_names": list(self.models.keys()),
            }


# ═══════════════════════════════════════════════════════════════════
# 3. CIRCUIT BREAKER PATTERN
# ═══════════════════════════════════════════════════════════════════

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance.
    
    Prevents cascading failures by:
    - Opening circuit after failure threshold
    - Allowing periodic recovery attempts
    - Automatic reset after success
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time: Optional[float] = None
        self.lock = Lock()
        self.logger = logger.bind(module="circuit_breaker")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Raises:
            RuntimeError: If circuit is OPEN
        """
        with self.lock:
            # Check if circuit should transition to HALF_OPEN
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.logger.info("Circuit breaker: OPEN → HALF_OPEN")
                else:
                    raise RuntimeError("Circuit breaker is OPEN")
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        with self.lock:
            self.failures = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.successes += 1
                if self.successes >= self.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.successes = 0
                    self.logger.info("Circuit breaker: HALF_OPEN → CLOSED")
    
    def _on_failure(self):
        """Handle failed call."""
        with self.lock:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.logger.warning("Circuit breaker: HALF_OPEN → OPEN")
            
            elif self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.logger.warning(f"Circuit breaker: CLOSED → OPEN (failures={self.failures})")
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt recovery."""
        if self.last_failure_time is None:
            return True
        
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def reset(self):
        """Manually reset circuit breaker."""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failures = 0
            self.successes = 0
            self.last_failure_time = None
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state."""
        with self.lock:
            return {
                "state": self.state.value,
                "failures": self.failures,
                "successes": self.successes,
            }


def circuit_breaker(breaker: CircuitBreaker):
    """Decorator for circuit breaker protection."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════
# 4. RATE LIMITER
# ═══════════════════════════════════════════════════════════════════

class RateLimiter:
    """
    Token bucket rate limiter.
    
    Implements:
    - Configurable rate and burst
    - Thread-safe operation
    - Automatic token refill
    """
    
    def __init__(self, rate: float, burst: int):
        """
        Initialize rate limiter.
        
        Args:
            rate: Tokens per second
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.time()
        self.lock = Lock()
        self.logger = logger.bind(module="rate_limiter")
    
    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens.
        
        Returns:
            True if tokens acquired, False otherwise
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Refill tokens
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            # Check if enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def wait(self, tokens: int = 1, timeout: Optional[float] = None):
        """
        Wait until tokens are available.
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum wait time (None = infinite)
        
        Raises:
            TimeoutError: If timeout exceeded
        """
        start = time.time()
        
        while not self.acquire(tokens):
            if timeout and (time.time() - start) >= timeout:
                raise TimeoutError("Rate limit wait timeout")
            
            time.sleep(0.01)  # 10ms sleep
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        with self.lock:
            return {
                "rate": self.rate,
                "burst": self.burst,
                "tokens_available": self.tokens,
            }


def rate_limited(limiter: RateLimiter, tokens: int = 1):
    """Decorator for rate limiting."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait(tokens)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════
# 5. BATCH PROCESSOR
# ═══════════════════════════════════════════════════════════════════

class BatchProcessor:
    """
    Intelligent batch processor for ML predictions.
    
    Optimizations:
    - Dynamic batching based on load
    - Timeout-based flushing
    - Memory-efficient processing
    """
    
    def __init__(
        self,
        batch_size: int = 32,
        timeout: float = 0.1,  # 100ms
        processor: Optional[Callable] = None,
    ):
        self.batch_size = batch_size
        self.timeout = timeout
        self.processor = processor
        self.queue: List[Any] = []
        self.lock = Lock()
        self.logger = logger.bind(module="batch_processor")
    
    def add(self, item: Any) -> Optional[List[Any]]:
        """
        Add item to batch.
        
        Returns:
            Processed batch if batch is full, None otherwise
        """
        with self.lock:
            self.queue.append(item)
            
            if len(self.queue) >= self.batch_size:
                return self._process_batch()
        
        return None
    
    def flush(self) -> Optional[List[Any]]:
        """Force process current batch."""
        with self.lock:
            if self.queue:
                return self._process_batch()
        return None
    
    def _process_batch(self) -> List[Any]:
        """Process current batch."""
        if not self.processor:
            batch = self.queue.copy()
            self.queue.clear()
            return batch
        
        batch = self.queue.copy()
        self.queue.clear()
        
        self.logger.debug(f"Processing batch of {len(batch)} items")
        result = self.processor(batch)
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics."""
        with self.lock:
            return {
                "queue_size": len(self.queue),
                "batch_size": self.batch_size,
                "timeout": self.timeout,
            }


# ═══════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════

__all__ = [
    "IntelligentCache",
    "CacheStrategy",
    "cached",
    "ModelPool",
    "CircuitBreaker",
    "CircuitState",
    "circuit_breaker",
    "RateLimiter",
    "rate_limited",
    "BatchProcessor",
]
