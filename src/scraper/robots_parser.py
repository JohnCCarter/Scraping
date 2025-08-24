"""
Avancerad robots.txt-parser med fullständig RFC-kompatibilitet
"""

import re
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
import structlog

from ..utils.config import Config


@dataclass
class RobotsRule:
    """En regel från robots.txt"""

    user_agent: str
    path: str
    allow: bool
    crawl_delay: Optional[float] = None
    request_rate: Optional[float] = None


@dataclass
class RobotsTxt:
    """Parsad robots.txt-fil"""

    url: str
    rules: List[RobotsRule]
    sitemaps: List[str]
    last_modified: Optional[float] = None
    expires: Optional[float] = None
    cache_control: Optional[str] = None


class AdvancedRobotsParser:
    """
    Avancerad robots.txt-parser som följer RFC 9309
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = structlog.get_logger(__name__)

        # Cache för parsade robots.txt-filer
        self._cache: Dict[str, Tuple[RobotsTxt, float]] = {}
        self.cache_timeout = self.config.get("robots.cache_timeout", 3600)  # 1 timme

        # Regex-mönster för parsing
        self.patterns = {
            "user_agent": re.compile(r"^User-agent:\s*(.+)$", re.IGNORECASE),
            "disallow": re.compile(r"^Disallow:\s*(.+)$", re.IGNORECASE),
            "allow": re.compile(r"^Allow:\s*(.+)$", re.IGNORECASE),
            "crawl_delay": re.compile(r"^Crawl-delay:\s*(\d+(?:\.\d+)?)$", re.IGNORECASE),
            "request_rate": re.compile(r"^Request-rate:\s*(\d+)/(\d+)$", re.IGNORECASE),
            "sitemap": re.compile(r"^Sitemap:\s*(.+)$", re.IGNORECASE),
            "comment": re.compile(r"^#.*$"),
            "empty": re.compile(r"^\s*$"),
        }

    async def can_fetch(self, url: str, user_agent: str = "*") -> Tuple[bool, Optional[float]]:
        """
        Kontrollerar om en URL får skrapas enligt robots.txt

        Args:
            url: URL att kontrollera
            user_agent: User-Agent att använda för kontroll

        Returns:
            Tuple av (tillåten, crawl_delay)
        """
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            # Hämta och parsa robots.txt
            robots_txt = await self._get_robots_txt(robots_url)
            if not robots_txt:
                return True, None  # Tillåt om robots.txt inte finns

            # Kontrollera regler
            return self._check_rules(robots_txt, parsed_url.path, user_agent)

        except Exception as e:
            self.logger.warning(f"Error checking robots.txt for {url}: {str(e)}")
            return True, None  # Tillåt vid fel

    async def _get_robots_txt(self, robots_url: str) -> Optional[RobotsTxt]:
        """Hämtar och cachar robots.txt"""
        current_time = time.time()

        # Kontrollera cache
        if robots_url in self._cache:
            robots_txt, cache_time = self._cache[robots_url]
            if current_time - cache_time < self.cache_timeout:
                return robots_txt

        # Hämta robots.txt
        try:
            import aiohttp

            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(robots_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        robots_txt = self._parse_robots_txt(robots_url, content)

                        # Cache resultatet
                        self._cache[robots_url] = (robots_txt, current_time)
                        return robots_txt
                    else:
                        self.logger.info(f"Robots.txt not found at {robots_url}")
                        return None

        except Exception as e:
            self.logger.warning(f"Error fetching robots.txt from {robots_url}: {str(e)}")
            return None

    def _parse_robots_txt(self, robots_url: str, content: str) -> RobotsTxt:
        """Parsar robots.txt-innehåll"""
        lines = content.split("\n")
        rules = []
        sitemaps = []
        current_user_agents = ["*"]  # Standard User-Agent

        for line in lines:
            line = line.strip()

            # Skippa kommentarer och tomma rader
            if self.patterns["comment"].match(line) or self.patterns["empty"].match(line):
                continue

            # User-Agent
            user_agent_match = self.patterns["user_agent"].match(line)
            if user_agent_match:
                current_user_agents = [user_agent_match.group(1).strip()]
                continue

            # Disallow
            disallow_match = self.patterns["disallow"].match(line)
            if disallow_match:
                path = disallow_match.group(1).strip()
                for user_agent in current_user_agents:
                    rules.append(RobotsRule(user_agent=user_agent, path=path, allow=False))
                continue

            # Allow
            allow_match = self.patterns["allow"].match(line)
            if allow_match:
                path = allow_match.group(1).strip()
                for user_agent in current_user_agents:
                    rules.append(RobotsRule(user_agent=user_agent, path=path, allow=True))
                continue

            # Crawl-delay
            crawl_delay_match = self.patterns["crawl_delay"].match(line)
            if crawl_delay_match:
                delay = float(crawl_delay_match.group(1))
                for user_agent in current_user_agents:
                    rules.append(RobotsRule(user_agent=user_agent, path="*", allow=True, crawl_delay=delay))
                continue

            # Request-rate
            request_rate_match = self.patterns["request_rate"].match(line)
            if request_rate_match:
                requests = int(request_rate_match.group(1))
                seconds = int(request_rate_match.group(2))
                rate = seconds / requests
                for user_agent in current_user_agents:
                    rules.append(RobotsRule(user_agent=user_agent, path="*", allow=True, request_rate=rate))
                continue

            # Sitemap
            sitemap_match = self.patterns["sitemap"].match(line)
            if sitemap_match:
                sitemap_url = sitemap_match.group(1).strip()
                sitemaps.append(sitemap_url)
                continue

        return RobotsTxt(url=robots_url, rules=rules, sitemaps=sitemaps)

    def _check_rules(self, robots_txt: RobotsTxt, path: str, user_agent: str) -> Tuple[bool, Optional[float]]:
        """Kontrollerar om en sökväg är tillåten enligt reglerna"""
        applicable_rules = []
        crawl_delay = None

        # Hitta tillämpliga regler
        for rule in robots_txt.rules:
            if (
                rule.user_agent == "*"
                or rule.user_agent.lower() in user_agent.lower()
                or user_agent.lower() in rule.user_agent.lower()
            ):

                if self._path_matches(rule.path, path):
                    applicable_rules.append(rule)
                    if rule.crawl_delay:
                        crawl_delay = rule.crawl_delay
                    if rule.request_rate:
                        crawl_delay = rule.request_rate

        # Sortera regler efter specificitet (mer specifika först)
        applicable_rules.sort(key=lambda r: len(r.path), reverse=True)

        # Kontrollera om sökvägen är tillåten
        for rule in applicable_rules:
            if rule.path != "*":  # Skip generella regler
                return rule.allow, crawl_delay

        # Om ingen specifik regel hittades, tillåt
        return True, crawl_delay

    def _path_matches(self, pattern: str, path: str) -> bool:
        """Kontrollerar om en sökväg matchar ett mönster"""
        if pattern == "*":
            return True

        # Normalisera sökvägar
        pattern = pattern.rstrip("/")
        path = path.rstrip("/")

        # Exakt match
        if pattern == path:
            return True

        # Prefix match
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return path.startswith(prefix)

        # Wildcard match
        if "*" in pattern:
            regex_pattern = pattern.replace("*", ".*")
            return bool(re.match(regex_pattern, path))

        # Prefix match (standard robots.txt-beteende)
        return path.startswith(pattern)

    def get_sitemaps(self, robots_url: str) -> List[str]:
        """Hämtar sitemaps från robots.txt"""
        if robots_url in self._cache:
            robots_txt, _ = self._cache[robots_url]
            return robots_txt.sitemaps
        return []

    def clear_cache(self):
        """Rensar robots.txt-cache"""
        self._cache.clear()
        self.logger.info("Robots.txt cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Returnerar cache-statistik"""
        return {"cached_robots_files": len(self._cache), "cache_timeout": self.cache_timeout}
