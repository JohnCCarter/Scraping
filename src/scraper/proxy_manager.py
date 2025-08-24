"""
Avancerad proxy-manager med rotation och health checks
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from urllib.parse import urlparse
import structlog

from ..utils.config import Config


@dataclass
class ProxyInfo:
    """Information om en proxy"""

    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    last_check: float = 0.0
    response_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    is_active: bool = True
    last_used: float = 0.0
    country: Optional[str] = None
    provider: Optional[str] = None

    @property
    def success_rate(self) -> float:
        """Beräknar framgångsgrad"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    @property
    def health_score(self) -> float:
        """Beräknar hälsopoäng baserat på prestanda"""
        if not self.is_active:
            return 0.0

        # Basera på framgångsgrad och response-tid
        success_weight = 0.7
        speed_weight = 0.3

        success_score = self.success_rate
        speed_score = max(0, 1 - (self.response_time / 10))  # Normalisera till 0-1

        return (success_score * success_weight) + (speed_score * speed_weight)


class ProxyManager:
    """
    Avancerad proxy-manager med rotation och health checks
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = structlog.get_logger(__name__)

        # Proxy-lista
        self.proxies: List[ProxyInfo] = []
        self.active_proxies: Set[str] = set()

        # Konfiguration
        self.health_check_interval = self.config.get("proxy.health_check_interval", 300)  # 5 min
        self.health_check_timeout = self.config.get("proxy.health_check_timeout", 10)
        self.max_failures = self.config.get("proxy.max_failures", 5)
        self.min_success_rate = self.config.get("proxy.min_success_rate", 0.5)
        self.rotation_strategy = self.config.get("proxy.rotation_strategy", "round_robin")

        # Rotation-state
        self.current_index = 0
        self.last_rotation = 0.0

        # Health check task
        self.health_check_task: Optional[asyncio.Task] = None

        # Ladda proxies från konfiguration
        self._load_proxies()

    def _load_proxies(self):
        """Laddar proxies från konfiguration"""
        proxy_list = self.config.get("proxy.proxy_list", [])

        for proxy_config in proxy_list:
            if isinstance(proxy_config, str):
                proxy_info = ProxyInfo(url=proxy_config)
            elif isinstance(proxy_config, dict):
                proxy_info = ProxyInfo(
                    url=proxy_config.get("url"),
                    username=proxy_config.get("username"),
                    password=proxy_config.get("password"),
                    country=proxy_config.get("country"),
                    provider=proxy_config.get("provider"),
                )
            else:
                continue

            if proxy_info.url:
                self.proxies.append(proxy_info)
                self.active_proxies.add(proxy_info.url)

        self.logger.info(f"Loaded {len(self.proxies)} proxies")

    async def start(self):
        """Startar proxy-manager och health checks"""
        if self.proxies:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            self.logger.info("Proxy manager started with health checks")

    async def stop(self):
        """Stoppar proxy-manager"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Proxy manager stopped")

    async def get_proxy(self) -> Optional[ProxyInfo]:
        """Hämtar nästa proxy enligt rotationsstrategi"""
        if not self.proxies:
            return None

        active_proxies = [p for p in self.proxies if p.is_active]
        if not active_proxies:
            self.logger.warning("No active proxies available")
            return None

        if self.rotation_strategy == "round_robin":
            proxy = active_proxies[self.current_index % len(active_proxies)]
            self.current_index = (self.current_index + 1) % len(active_proxies)

        elif self.rotation_strategy == "random":
            proxy = random.choice(active_proxies)

        elif self.rotation_strategy == "health_based":
            # Välj proxy baserat på hälsopoäng
            active_proxies.sort(key=lambda p: p.health_score, reverse=True)
            proxy = active_proxies[0]

        elif self.rotation_strategy == "least_used":
            # Välj minst använda proxy
            active_proxies.sort(key=lambda p: p.last_used)
            proxy = active_proxies[0]

        else:
            proxy = active_proxies[0]

        proxy.last_used = time.time()
        return proxy

    async def report_success(self, proxy_url: str, response_time: float):
        """Rapporterar framgångsrik användning av proxy"""
        proxy = self._find_proxy(proxy_url)
        if proxy:
            proxy.success_count += 1
            proxy.response_time = (proxy.response_time + response_time) / 2
            proxy.last_check = time.time()

    async def report_failure(self, proxy_url: str, error: str):
        """Rapporterar misslyckad användning av proxy"""
        proxy = self._find_proxy(proxy_url)
        if proxy:
            proxy.failure_count += 1
            proxy.last_check = time.time()

            # Kontrollera om proxy ska deaktiveras
            if proxy.failure_count >= self.max_failures or proxy.success_rate < self.min_success_rate:
                await self._deactivate_proxy(proxy)

    def _find_proxy(self, proxy_url: str) -> Optional[ProxyInfo]:
        """Hittar proxy baserat på URL"""
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                return proxy
        return None

    async def _deactivate_proxy(self, proxy: ProxyInfo):
        """Deaktiverar en proxy"""
        proxy.is_active = False
        self.active_proxies.discard(proxy.url)
        self.logger.warning(f"Deactivated proxy {proxy.url} due to poor performance")

    async def _activate_proxy(self, proxy: ProxyInfo):
        """Aktiverar en proxy"""
        proxy.is_active = True
        self.active_proxies.add(proxy.url)
        self.logger.info(f"Activated proxy {proxy.url}")

    async def _health_check_loop(self):
        """Loop för regelbundna health checks"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {str(e)}")

    async def _perform_health_checks(self):
        """Utför health checks på alla proxies"""
        self.logger.info("Starting health checks for all proxies")

        tasks = []
        for proxy in self.proxies:
            if time.time() - proxy.last_check > self.health_check_interval:
                tasks.append(self._check_proxy_health(proxy))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Health check failed for proxy {i}: {str(result)}")

        self.logger.info(f"Health checks completed. Active proxies: {len(self.active_proxies)}")

    async def _check_proxy_health(self, proxy: ProxyInfo) -> bool:
        """Kontrollerar hälsan för en specifik proxy"""
        try:
            start_time = time.time()

            # Testa proxy med en enkel request
            test_url = "http://httpbin.org/ip"
            success = await self._test_proxy_request(proxy, test_url)

            response_time = time.time() - start_time

            if success:
                proxy.response_time = response_time
                proxy.last_check = time.time()

                # Aktivera proxy om den var deaktiverad
                if not proxy.is_active:
                    await self._activate_proxy(proxy)

                return True
            else:
                proxy.failure_count += 1
                proxy.last_check = time.time()

                # Deaktivera proxy om den presterar dåligt
                if proxy.failure_count >= self.max_failures:
                    await self._deactivate_proxy(proxy)

                return False

        except Exception as e:
            self.logger.error(f"Health check error for {proxy.url}: {str(e)}")
            proxy.failure_count += 1
            return False

    async def _test_proxy_request(self, proxy: ProxyInfo, test_url: str) -> bool:
        """Testar en proxy med en request"""
        try:
            import aiohttp

            # Skapa proxy-URL
            proxy_url = proxy.url
            if proxy.username and proxy.password:
                parsed = urlparse(proxy.url)
                proxy_url = f"{parsed.scheme}://{proxy.username}:{proxy.password}@{parsed.netloc}"

            # Konfigurera timeout
            timeout = aiohttp.ClientTimeout(total=self.health_check_timeout)

            # Skapa connector med proxy
            connector = aiohttp.ProxyConnector.from_url(proxy_url)

            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(test_url) as response:
                    return response.status == 200

        except Exception as e:
            self.logger.debug(f"Proxy test failed for {proxy.url}: {str(e)}")
            return False

    def add_proxy(
        self,
        proxy_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        country: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Lägger till en ny proxy"""
        proxy_info = ProxyInfo(url=proxy_url, username=username, password=password, country=country, provider=provider)

        self.proxies.append(proxy_info)
        self.active_proxies.add(proxy_url)
        self.logger.info(f"Added new proxy: {proxy_url}")

    def remove_proxy(self, proxy_url: str):
        """Tar bort en proxy"""
        proxy = self._find_proxy(proxy_url)
        if proxy:
            self.proxies.remove(proxy)
            self.active_proxies.discard(proxy_url)
            self.logger.info(f"Removed proxy: {proxy_url}")

    def get_stats(self) -> Dict:
        """Returnerar statistik om proxies"""
        total_proxies = len(self.proxies)
        active_proxies = len(self.active_proxies)

        if total_proxies == 0:
            return {"total_proxies": 0, "active_proxies": 0, "success_rate": 0.0, "avg_response_time": 0.0}

        # Beräkna genomsnittlig statistik
        total_success = sum(p.success_count for p in self.proxies)
        total_failures = sum(p.failure_count for p in self.proxies)
        total_requests = total_success + total_failures

        success_rate = total_success / total_requests if total_requests > 0 else 0.0

        active_proxy_times = [p.response_time for p in self.proxies if p.is_active and p.response_time > 0]
        avg_response_time = sum(active_proxy_times) / len(active_proxy_times) if active_proxy_times else 0.0

        return {
            "total_proxies": total_proxies,
            "active_proxies": active_proxies,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "rotation_strategy": self.rotation_strategy,
        }

    def get_proxy_details(self) -> List[Dict]:
        """Returnerar detaljerad information om alla proxies"""
        details = []
        for proxy in self.proxies:
            details.append(
                {
                    "url": proxy.url,
                    "is_active": proxy.is_active,
                    "success_count": proxy.success_count,
                    "failure_count": proxy.failure_count,
                    "success_rate": proxy.success_rate,
                    "response_time": proxy.response_time,
                    "health_score": proxy.health_score,
                    "last_used": proxy.last_used,
                    "country": proxy.country,
                    "provider": proxy.provider,
                }
            )
        return details
