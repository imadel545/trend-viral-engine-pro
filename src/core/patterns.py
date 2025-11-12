"""
Advanced OOP Patterns - Thread-safe, extensible, production-ready.

Patterns implémentés:
1. Thread-Safe Singleton (Double-Check Locking)
2. Observer Pattern (monitoring découplé)
3. Decorator utilities (cache, retry, monitoring)
4. Dependency Injection Container

Usage:
    from src.core.patterns import ServiceContainer, cached, monitored, retry, ObservableService
    
Author: Trend & Viral Engine Pro
Date: 11 novembre 2025
"""

from functools import wraps
import time
import asyncio
from typing import Callable, Any, Optional, List, Dict, Protocol
from threading import Lock
from loguru import logger


# ============================================================================
# 1. OBSERVER PATTERN
# ============================================================================

class IObserver(Protocol):
    """Interface pour observers (monitoring, logging, etc.)"""
    
    def update(self, event: Dict[str, Any]) -> None:
        """
        Notifié lors d'un événement.
        
        Args:
            event: Dictionnaire avec type d'événement et données
        """
        ...


class ObservableService:
    """
    Classe de base pour services observables.
    
    Permet d'attacher observers pour monitoring découplé.
    """
    
    def __init__(self):
        self.observers: List[IObserver] = []
    
    def attach(self, observer: IObserver) -> None:
        """Attacher un observer."""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def detach(self, observer: IObserver) -> None:
        """Détacher un observer."""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def notify(self, event: Dict[str, Any]) -> None:
        """
        Notifier tous les observers.
        
        Args:
            event: Événement à propager (type, données)
        """
        for observer in self.observers:
            try:
                observer.update(event)
            except Exception as e:
                logger.error(f"Observer {type(observer).__name__} failed: {e}")


class LoggingObserver:
    """Observer pour logs structurés."""
    
    def update(self, event: Dict[str, Any]) -> None:
        event_type = event.get('type', 'unknown')
        logger.info(
            f"Event: {event_type}",
            **{k: v for k, v in event.items() if k != 'type'}
        )


# ============================================================================
# 2. DECORATOR PATTERN
# ============================================================================

def cached(ttl: int = 60, key_func: Optional[Callable] = None):
    """
    Decorator pour cache avec Time-To-Live.
    
    Args:
        ttl: Durée cache en secondes
        key_func: Fonction optionnelle pour générer clé cache
    
    Example:
        @cached(ttl=300)
        def expensive_computation(x, y):
            return x + y
    """
    cache = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Générer clé cache
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Clé par défaut: args + kwargs
                key = (args, tuple(sorted(kwargs.items())))
            
            # Check cache
            if key in cache:
                value, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    logger.debug(f"Cache hit: {func.__name__}")
                    return value
            
            # Calcul + mise en cache
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            
            return result
        
        # Ajouter méthode pour vider cache
        wrapper.clear_cache = lambda: cache.clear()
        
        return wrapper
    return decorator


def retry(max_attempts: int = 3, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator pour retry avec backoff exponentiel.
    
    Args:
        max_attempts: Nombre maximum de tentatives
        backoff: Facteur backoff (2.0 = double à chaque fois)
        exceptions: Tuple d'exceptions à catcher
    
    Example:
        @retry(max_attempts=3, backoff=2.0)
        async def unstable_api_call():
            ...
    """
    def decorator(func: Callable) -> Callable:
        
        # Version async
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        delay = backoff ** (attempt - 1)
                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
            
            raise last_exception
        
        # Version sync
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        delay = backoff ** (attempt - 1)
                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
            
            raise last_exception
        
        # Retourner version appropriée
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def monitored(operation_name: str):
    """
    Decorator pour monitoring automatique (latency, succès, erreurs).
    
    Args:
        operation_name: Nom de l'opération pour les métriques
    
    Example:
        @monitored("scoring.predict")
        async def predict(features):
            ...
    """
    def decorator(func: Callable) -> Callable:
        
        # Version async
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start = time.time()
            
            try:
                result = await func(*args, **kwargs)
                latency = time.time() - start
                
                logger.info(f"{operation_name} completed in {latency:.2f}s")
                
                return result
            
            except Exception as e:
                latency = time.time() - start
                logger.error(f"{operation_name} failed after {latency:.2f}s: {e}")
                raise
        
        # Version sync
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start = time.time()
            
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start
                
                logger.info(f"{operation_name} completed in {latency:.2f}s")
                
                return result
            
            except Exception as e:
                latency = time.time() - start
                logger.error(f"{operation_name} failed after {latency:.2f}s: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# ============================================================================
# 3. DEPENDENCY INJECTION CONTAINER
# ============================================================================

class ServiceContainer:
    """
    Dependency Injection Container (Singleton).
    
    Gère création et lifecycle des services.
    Thread-safe avec double-check locking.
    
    Example:
        container = ServiceContainer()
        
        # Enregistrer factory
        container.register(ScoringService, lambda: ScoringService())
        
        # Résoudre service (singleton)
        scoring = container.resolve(ScoringService)
    """
    
    _instance: Optional['ServiceContainer'] = None
    _lock: Lock = Lock()
    
    def __new__(cls):
        """Thread-safe singleton avec double-check locking."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._services = {}
                    cls._instance._factories = {}
                    cls._instance._initialized = True
        return cls._instance
    
    def register(self, interface: type, factory: Callable) -> None:
        """
        Enregistrer factory pour un service.
        
        Args:
            interface: Type/interface du service
            factory: Fonction créant l'instance
        """
        self._factories[interface] = factory
        logger.debug(f"Registered factory for {interface.__name__}")
    
    def resolve(self, interface: type) -> Any:
        """
        Résoudre service (singleton par type).
        
        Args:
            interface: Type/interface à résoudre
        
        Returns:
            Instance du service (créée ou cached)
        
        Raises:
            ValueError: Si aucune factory enregistrée
        """
        if interface not in self._services:
            with self._lock:
                if interface not in self._services:
                    if interface not in self._factories:
                        raise ValueError(f"No factory registered for {interface.__name__}")
                    
                    factory = self._factories[interface]
                    self._services[interface] = factory()
                    logger.debug(f"Created instance of {interface.__name__}")
        
        return self._services[interface]
    
    def reset(self) -> None:
        """Reset container (utile pour tests)."""
        with self._lock:
            self._services.clear()
            logger.debug("Container reset")
    
    def is_registered(self, interface: type) -> bool:
        """Vérifier si un service est enregistré."""
        return interface in self._factories


# ============================================================================
# 4. THREAD-SAFE SINGLETON MIXIN
# ============================================================================

class ThreadSafeSingleton:
    """
    Mixin pour créer singletons thread-safe avec double-check locking.
    
    Usage:
        class MyService(ThreadSafeSingleton):
            def __init__(self):
                if hasattr(self, '_initialized'):
                    return
                
                # Initialisation
                self._initialized = True
    """
    
    _instances: Dict[type, Any] = {}
    _lock: Lock = Lock()
    
    def __new__(cls, *args, **kwargs):
        """Thread-safe singleton avec double-check locking."""
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Observer Pattern
    'IObserver',
    'ObservableService',
    'LoggingObserver',
    
    # Decorators
    'cached',
    'retry',
    'monitored',
    
    # Dependency Injection
    'ServiceContainer',
    
    # Thread-Safe Singleton
    'ThreadSafeSingleton',
]
