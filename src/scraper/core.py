"""
Core WebScraper class with async support and robust error handling
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

import aiohttp
import structlog
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from ..utils.config import Config
from ..utils.logging import setup_logger
from .parsers import HTMLParser, JSONParser
from .validators import DataValidator
from .exporters import DataExporter


@dataclass
class ScrapingResult:
    """Resultat från en scraping-operation"""

    url: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time: Optional[float] = None
    status_code: Optional[int] = None


class WebScraper:
    """
    Huvudklass för web scraping med asynkron stöd och robust felhantering
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initierar WebScraper med konfiguration

        Args:
            config_path: Sökväg till konfigurationsfil (YAML/JSON)
        """
        self.config = Config(config_path)
        self.logger = setup_logger(__name__)

        # Komponenter
        self.html_parser = HTMLParser()
        self.json_parser = JSONParser()
        self.validator = DataValidator()
        self.exporter = DataExporter()

        # Session-hantering
        self.session: Optional[aiohttp.ClientSession] = None
        self.playwright = None
        self.browser = None

        # Rate limiting
        self.request_times: List[float] = []
        self.semaphore = asyncio.Semaphore(self.config.get("rate_limiting.max_concurrent", 10))

        # Metrics
        self.metrics = {"total_requests": 0, "successful_requests": 0, "failed_requests": 0, "total_response_time": 0.0}

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    async def start(self):
        """Startar scraper-sessionen"""
        self.logger.info("Starting WebScraper session")

        # Skapa aiohttp session
        timeout = aiohttp.ClientTimeout(
            total=self.config.get("scraper.timeout", 30), connect=self.config.get("scraper.connect_timeout", 10)
        )

        headers = {
            "User-Agent": self.config.get(
                "scraper.user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        }

        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)

        # Starta Playwright om JavaScript-rendering behövs
        if self.config.get("scraper.use_playwright", False):
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.config.get("scraper.headless", True))

    async def stop(self):
        """Stoppar scraper-sessionen"""
        self.logger.info("Stopping WebScraper session")

        if self.session:
            await self.session.close()

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        # Logga metrics
        self._log_metrics()

    async def scrape_url(self, url: str, parser_type: str = "auto") -> ScrapingResult:
        """
        Skrapar en URL och returnerar strukturerad data

        Args:
            url: URL att skrapa
            parser_type: Typ av parser ("html", "json", "auto")

        Returns:
            ScrapingResult med data eller felinformation
        """
        start_time = time.time()

        try:
            # Rate limiting
            await self._rate_limit()

            # Kontrollera robots.txt
            if not await self._check_robots_txt(url):
                return ScrapingResult(
                    url=url, success=False, error="robots.txt forbids access", response_time=time.time() - start_time
                )

            # Skapa request
            async with self.semaphore:
                if self.config.get("scraper.use_playwright", False):
                    data = await self._scrape_with_playwright(url)
                else:
                    data = await self._scrape_with_requests(url)

            # Parsa data
            if parser_type == "auto":
                parser_type = self._detect_content_type(data)

            parsed_data = await self._parse_data(data, parser_type)

            # Validera data
            if parsed_data:
                validated_data = self.validator.validate(parsed_data)
            else:
                validated_data = None

            # Uppdatera metrics
            response_time = time.time() - start_time
            self._update_metrics(success=True, response_time=response_time)

            return ScrapingResult(url=url, success=True, data=validated_data, response_time=response_time)

        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            response_time = time.time() - start_time
            self._update_metrics(success=False, response_time=response_time)

            return ScrapingResult(url=url, success=False, error=str(e), response_time=response_time)

    async def scrape_multiple(self, urls: List[str], parser_type: str = "auto") -> List[ScrapingResult]:
        """
        Skrapar flera URLs parallellt

        Args:
            urls: Lista med URLs att skrapa
            parser_type: Typ av parser

        Returns:
            Lista med ScrapingResult
        """
        self.logger.info(f"Starting batch scraping of {len(urls)} URLs")

        tasks = [self.scrape_url(url, parser_type) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Hantera exceptions från gather
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ScrapingResult(url=urls[i], success=False, error=str(result)))
            else:
                processed_results.append(result)

        return processed_results

    async def _scrape_with_requests(self, url: str) -> str:
        """Skrapar med aiohttp (snabbare för statiskt innehåll)"""
        async with self.session.get(url) as response:
            self.metrics["total_requests"] += 1

            if response.status == 200:
                return await response.text()
            else:
                raise Exception(f"HTTP {response.status}: {response.reason}")

    async def _scrape_with_playwright(self, url: str) -> str:
        """Skrapar med Playwright (för JavaScript-renderat innehåll)"""
        page = await self.browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle")
            content = await page.content()
            return content
        finally:
            await page.close()

    async def _parse_data(self, raw_data: str, parser_type: str) -> Optional[Dict[str, Any]]:
        """Parsar rådata med lämplig parser"""
        if parser_type == "html":
            return self.html_parser.parse(raw_data)
        elif parser_type == "json":
            return self.json_parser.parse(raw_data)
        else:
            # Försök auto-detect
            try:
                return self.json_parser.parse(raw_data)
            except:
                return self.html_parser.parse(raw_data)

    def _detect_content_type(self, data: str) -> str:
        """Detekterar innehållstyp automatiskt"""
        data = data.strip()
        if data.startswith("{") or data.startswith("["):
            return "json"
        else:
            return "html"

    async def _rate_limit(self):
        """Implementerar rate limiting"""
        delay = self.config.get("rate_limiting.delay_between_requests", 1.0)

        # Rensa gamla request-tider
        current_time = time.time()
        self.request_times = [t for t in self.request_times if current_time - t < 60]

        # Kontrollera rate limit
        max_requests = self.config.get("rate_limiting.requests_per_minute", 60)
        if len(self.request_times) >= max_requests:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                self.logger.info(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)

        self.request_times.append(current_time)

        # Lägg till delay mellan requests
        if delay > 0:
            await asyncio.sleep(delay)

    async def _check_robots_txt(self, url: str) -> bool:
        """Kontrollerar robots.txt (förenklad implementation)"""
        # I en riktig implementation skulle vi här:
        # 1. Hämta robots.txt från domänen
        # 2. Parsa den och kontrollera regler
        # 3. Returnera True/False baserat på regler

        # För nu returnerar vi True (tillåt allt)
        return True

    def _update_metrics(self, success: bool, response_time: float):
        """Uppdaterar scraping-metrics"""
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1

        self.metrics["total_response_time"] += response_time

    def _log_metrics(self):
        """Loggar sammanställda metrics"""
        total = self.metrics["total_requests"]
        if total > 0:
            success_rate = (self.metrics["successful_requests"] / total) * 100
            avg_response_time = self.metrics["total_response_time"] / total

            self.logger.info(
                "Scraping session completed",
                total_requests=total,
                success_rate=f"{success_rate:.1f}%",
                avg_response_time=f"{avg_response_time:.2f}s",
            )

    def export_data(
        self, data: Union[ScrapingResult, List[ScrapingResult]], format: str = "json", output_path: Optional[str] = None
    ):
        """
        Exporterar skrapad data

        Args:
            data: ScrapingResult eller lista med ScrapingResult
            format: Export-format ("json", "csv", "excel")
            output_path: Sökväg för output-fil
        """
        if isinstance(data, ScrapingResult):
            data = [data]

        # Filtrera framgångsrika requests
        successful_data = [result.data for result in data if result.success and result.data]

        if not successful_data:
            self.logger.warning("No successful data to export")
            return

        # Exportera
        if not output_path:
            timestamp = int(time.time())
            output_path = f"data/scraped_data_{timestamp}.{format}"

        self.exporter.export(successful_data, format, output_path)
        self.logger.info(f"Data exported to {output_path}")
