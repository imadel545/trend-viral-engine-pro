"""
🕵️ ANTI-DETECTION TOOLKIT - User-Agent rotation, Proxy management

Techniques utilisées par scrapers professionnels (ScrapingBee, Bright Data):
- User-Agent rotation réaliste
- Proxy rotation (si configurés)
- Request throttling intelligent
- Header randomization
"""

import random
import time
from typing import Dict, List, Optional
from loguru import logger


class UserAgentRotator:
    """
    User-Agent rotation avec profils réalistes.
    
    Stratégie:
    - Pool de 100+ User-Agents réels
    - Mix Chrome, Firefox, Safari, Edge
    - Desktop + Mobile
    - Versions récentes (2023-2024)
    """

    def __init__(self):
        self.user_agents = self._build_user_agent_pool()
        self.current_index = 0
        
        logger.info(f"🕵️ UserAgentRotator initialized with {len(self.user_agents)} agents")

    def _build_user_agent_pool(self) -> List[str]:
        """Build pool de User-Agents réalistes."""
        
        # Chrome Desktop (Windows, macOS, Linux)
        chrome_desktop = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
        
        # Firefox Desktop
        firefox_desktop = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        ]
        
        # Safari Desktop (macOS)
        safari_desktop = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]
        
        # Edge Desktop
        edge_desktop = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        ]
        
        # Chrome Mobile (Android, iOS)
        chrome_mobile = [
            "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        ]
        
        # Safari Mobile (iOS)
        safari_mobile = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        ]
        
        # Combine all
        all_agents = (
            chrome_desktop * 3 +  # Chrome prioritaire (70% usage)
            firefox_desktop * 2 +
            safari_desktop +
            edge_desktop +
            chrome_mobile +
            safari_mobile
        )
        
        # Shuffle pour randomisation
        random.shuffle(all_agents)
        
        return all_agents

    def get_random(self) -> str:
        """Get random User-Agent."""
        return random.choice(self.user_agents)

    def get_next(self) -> str:
        """Get next User-Agent (rotation séquentielle)."""
        ua = self.user_agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.user_agents)
        return ua

    def get_headers(self, randomize: bool = True) -> Dict[str, str]:
        """
        Get headers complets avec User-Agent.
        
        Args:
            randomize: Si True, utilise random UA, sinon next UA
        
        Returns:
            Dict de headers HTTP réalistes
        """
        ua = self.get_random() if randomize else self.get_next()
        
        # Headers de base réalistes
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
        
        # Randomize Accept-Language (mix français/anglais)
        if random.random() > 0.5:
            headers["Accept-Language"] = "fr-FR,fr;q=0.9,en;q=0.8"
        
        return headers


class ProxyRotator:
    """
    Proxy rotation manager.
    
    NOTE: Nécessite configuration de proxies dans .env
    Format: PROXY_LIST=http://user:pass@host:port,http://...
    """

    def __init__(self, proxy_list: Optional[List[str]] = None):
        self.proxy_list = proxy_list or []
        self.current_index = 0
        self.failed_proxies = set()
        
        if self.proxy_list:
            logger.info(f"🌐 ProxyRotator initialized with {len(self.proxy_list)} proxies")
        else:
            logger.warning("⚠️ ProxyRotator initialized with NO proxies (direct connection)")

    def get_next(self) -> Optional[str]:
        """Get next working proxy."""
        if not self.proxy_list:
            return None
        
        # Filter failed proxies
        working_proxies = [p for p in self.proxy_list if p not in self.failed_proxies]
        
        if not working_proxies:
            logger.warning("⚠️ All proxies failed - resetting failed list")
            self.failed_proxies.clear()
            working_proxies = self.proxy_list
        
        proxy = working_proxies[self.current_index % len(working_proxies)]
        self.current_index += 1
        
        return proxy

    def get_random(self) -> Optional[str]:
        """Get random working proxy."""
        if not self.proxy_list:
            return None
        
        working_proxies = [p for p in self.proxy_list if p not in self.failed_proxies]
        
        if not working_proxies:
            self.failed_proxies.clear()
            working_proxies = self.proxy_list
        
        return random.choice(working_proxies)

    def mark_failed(self, proxy: str):
        """Mark proxy as failed."""
        self.failed_proxies.add(proxy)
        logger.warning(f"❌ Proxy marked as failed: {proxy}")

    def get_proxy_dict(self, proxy: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Get proxy dict format for requests/httpx.
        
        Args:
            proxy: Specific proxy URL (ou None pour next proxy)
        
        Returns:
            {"http": "...", "https": "..."} ou None
        """
        if not proxy:
            proxy = self.get_next()
        
        if not proxy:
            return None
        
        return {
            "http": proxy,
            "https": proxy
        }


class RequestThrottler:
    """
    Throttling intelligent des requêtes.
    
    Features:
    - Rate limiting adaptatif
    - Exponential backoff si détection
    - Random delays pour mimicker humain
    """

    def __init__(
        self,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        adaptive: bool = True
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.adaptive = adaptive
        
        self.last_request_time = 0.0
        self.consecutive_429s = 0
        self.current_delay = min_delay
        
        logger.info(
            f"⏱️ RequestThrottler initialized "
            f"(delay={min_delay}-{max_delay}s, adaptive={adaptive})"
        )

    async def wait(self):
        """Attend avant prochaine requête."""
        import asyncio
        
        # Calculate delay
        if self.adaptive and self.consecutive_429s > 0:
            # Exponential backoff si rate limited
            delay = min(
                self.current_delay * (2 ** self.consecutive_429s),
                60.0  # Max 60s
            )
            logger.warning(f"⏳ Adaptive delay: {delay:.1f}s (429 count: {self.consecutive_429s})")
        else:
            # Random delay normal
            delay = random.uniform(self.min_delay, self.max_delay)
        
        # Wait
        await asyncio.sleep(delay)
        self.last_request_time = time.time()

    def on_success(self):
        """Reset après succès."""
        self.consecutive_429s = 0
        self.current_delay = self.min_delay

    def on_rate_limit(self):
        """Incrémente compteur 429."""
        self.consecutive_429s += 1
        logger.warning(f"⚠️ Rate limit detected (count: {self.consecutive_429s})")


# Global singletons
_ua_rotator: Optional[UserAgentRotator] = None
_proxy_rotator: Optional[ProxyRotator] = None


def get_user_agent_rotator() -> UserAgentRotator:
    """Get or create UserAgentRotator singleton."""
    global _ua_rotator
    if _ua_rotator is None:
        _ua_rotator = UserAgentRotator()
    return _ua_rotator


def get_proxy_rotator(proxy_list: Optional[List[str]] = None) -> ProxyRotator:
    """Get or create ProxyRotator singleton."""
    global _proxy_rotator
    if _proxy_rotator is None:
        _proxy_rotator = ProxyRotator(proxy_list=proxy_list)
    return _proxy_rotator
