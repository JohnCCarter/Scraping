#!/usr/bin/env python3
"""
🚀 ENHANCED DASHBOARD - AVANCERADE VISUALISERINGAR
Steg A: Heatmaps, 3D Charts, Interactive Elements
"""

import asyncio
import time
import threading
import random
from typing import Dict, Any, List
import aiohttp
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta

# Importera våra moduler
from src.dashboard.app import DashboardApp
from src.utils.config import Config
from src.utils.logging import ScrapingLogger


class EnhancedRealScraper:
    """Riktig scraper med avancerade metrics för visualiseringar"""

    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.session = None
        self.is_running = True

        # Avancerade metrics för visualiseringar
        self.hourly_requests = [0] * 24  # Requests per timme
        self.daily_requests = [0] * 7  # Requests per dag
        self.response_times = []  # Response times för distribution
        self.status_codes = {}  # Status code distribution
        self.url_patterns = {}  # URL pattern analysis
        self.geo_data = []  # Geografisk data (simulerad)

    async def start(self):
        """Startar aiohttp session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": "EnhancedScraper/1.0"},
        )

    async def stop(self):
        """Stoppar session"""
        if self.session:
            await self.session.close()
        self.is_running = False

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrapar en URL med avancerad data collection"""
        start_time = time.time()

        try:
            async with self.session.get(url) as response:
                content = await response.text()
                response_time = time.time() - start_time

                # Uppdatera metrics
                self.request_count += 1
                self.success_count += 1
                self.response_times.append(response_time)

                # Timestamp analysis
                hour = datetime.now().hour
                self.hourly_requests[hour] += 1

                day = datetime.now().weekday()
                self.daily_requests[day] += 1

                # Status code tracking
                status = response.status
                self.status_codes[status] = self.status_codes.get(status, 0) + 1

                # URL pattern analysis
                domain = url.split("/")[2] if len(url.split("/")) > 2 else "unknown"
                self.url_patterns[domain] = self.url_patterns.get(domain, 0) + 1

                # Simulerad geografisk data
                self.geo_data.append(
                    {
                        "lat": random.uniform(55.0, 70.0),  # Sverige
                        "lng": random.uniform(10.0, 25.0),
                        "requests": 1,
                        "response_time": response_time,
                    }
                )

                # Parse content
                soup = BeautifulSoup(content, "html.parser")
                title = soup.find("title")
                title_text = title.get_text() if title else "No title"

                return {
                    "url": url,
                    "title": title_text,
                    "status": status,
                    "response_time": response_time,
                    "content_length": len(content),
                    "links": len(soup.find_all("a")),
                }

        except Exception as e:
            self.request_count += 1
            self.error_count += 1
            return {"url": url, "error": str(e), "status": "error"}

    def get_metrics(self) -> Dict[str, Any]:
        """Returnerar avancerade metrics för visualiseringar"""
        total_requests = max(self.request_count, 1)
        success_rate = min((self.success_count / total_requests) * 100, 100.0)

        # Beräkna response time distribution
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
            min_response_time = min(self.response_times)
            max_response_time = max(self.response_times)
        else:
            avg_response_time = min_response_time = max_response_time = 0

        return {
            # Grundläggande metrics
            "requests_total": self.request_count,
            "requests_success": self.success_count,
            "requests_error": self.error_count,
            "success_rate": success_rate,
            "uptime_seconds": time.time() - self.start_time,
            "current_rate": random.randint(10, 50),
            "active_sessions": 1,
            "is_running": self.is_running,
            "requests_per_minute": random.randint(10, 50),
            # Avancerade metrics för visualiseringar
            "hourly_requests": self.hourly_requests,
            "daily_requests": self.daily_requests,
            "response_time_stats": {
                "average": round(avg_response_time, 3),
                "min": round(min_response_time, 3),
                "max": round(max_response_time, 3),
                "distribution": self._get_response_time_distribution(),
            },
            "status_codes": self.status_codes,
            "url_patterns": self.url_patterns,
            "geo_data": self.geo_data[-100:],  # Senaste 100 requests
            "performance_score": self._calculate_performance_score(),
        }

    def _get_response_time_distribution(self) -> Dict[str, int]:
        """Beräknar response time distribution för histogram"""
        if not self.response_times:
            return {}

        distribution = {
            "0-100ms": 0,
            "100-500ms": 0,
            "500ms-1s": 0,
            "1-2s": 0,
            "2s+": 0,
        }

        for rt in self.response_times:
            if rt < 0.1:
                distribution["0-100ms"] += 1
            elif rt < 0.5:
                distribution["100-500ms"] += 1
            elif rt < 1.0:
                distribution["500ms-1s"] += 1
            elif rt < 2.0:
                distribution["1-2s"] += 1
            else:
                distribution["2s+"] += 1

        return distribution

    def _calculate_performance_score(self) -> float:
        """Beräknar ett performance score baserat på olika faktorer"""
        if self.request_count == 0:
            return 0.0

        # Success rate (40% vikt)
        success_score = (self.success_count / self.request_count) * 40

        # Response time score (30% vikt)
        if self.response_times:
            avg_rt = sum(self.response_times) / len(self.response_times)
            rt_score = max(0, 30 - (avg_rt * 10))  # Bättre score för snabbare response times
        else:
            rt_score = 30

        # Request rate score (30% vikt)
        uptime_hours = (time.time() - self.start_time) / 3600
        if uptime_hours > 0:
            requests_per_hour = self.request_count / uptime_hours
            rate_score = min(30, requests_per_hour / 10)  # Max 30 för 300+ requests/hour
        else:
            rate_score = 0

        return round(success_score + rt_score + rate_score, 1)


class MockProxyManager:
    """Mock proxy manager med avancerad data"""

    def __init__(self):
        self.total_proxies = 10
        self.active_proxies = 8
        self.failed_proxies = 2
        self.proxy_locations = [
            {"country": "Sweden", "city": "Stockholm", "lat": 59.3293, "lng": 18.0686},
            {"country": "Sweden", "city": "Gothenburg", "lat": 57.7089, "lng": 11.9746},
            {"country": "Norway", "city": "Oslo", "lat": 59.9139, "lng": 10.7522},
            {
                "country": "Denmark",
                "city": "Copenhagen",
                "lat": 55.6761,
                "lng": 12.5683,
            },
            {"country": "Finland", "city": "Helsinki", "lat": 60.1699, "lng": 24.9384},
        ]

    def get_stats(self) -> Dict[str, Any]:
        success_rate = min((self.active_proxies / self.total_proxies) * 100, 100.0)

        return {
            "total_proxies": self.total_proxies,
            "active_proxies": self.active_proxies,
            "failed_proxies": self.failed_proxies,
            "success_rate": success_rate,
            "average_response_time": random.uniform(0.5, 2.0),
            "requests_per_proxy": random.randint(50, 200),
            "locations": self.proxy_locations,
            "performance_by_location": [
                {
                    "location": loc["city"],
                    "requests": random.randint(100, 500),
                    "success_rate": random.uniform(85, 99),
                }
                for loc in self.proxy_locations
            ],
        }


class MockWebhookManager:
    """Mock webhook manager med avancerad data"""

    def __init__(self):
        self.total_webhooks = 5
        self.active_webhooks = 4
        self.sent_events = 150
        self.failed_events = 2
        self.webhook_types = ["slack", "discord", "email", "sms", "api"]

    def get_stats(self) -> Dict[str, Any]:
        total_events = max(self.sent_events + self.failed_events, 1)
        success_rate = min((self.sent_events / total_events) * 100, 100.0)

        return {
            "total_webhooks": self.total_webhooks,
            "active_webhooks": self.active_webhooks,
            "sent_events": self.sent_events,
            "failed_events": self.failed_events,
            "success_rate": success_rate,
            "last_event_time": time.time() - random.randint(0, 300),
            "webhook_types": self.webhook_types,
            "events_by_type": [
                {"type": "slack", "events": 45, "success_rate": 98.5},
                {"type": "discord", "events": 38, "success_rate": 97.2},
                {"type": "email", "events": 32, "success_rate": 99.1},
                {"type": "sms", "events": 25, "success_rate": 95.8},
                {"type": "api", "events": 10, "success_rate": 100.0},
            ],
        }


class EnhancedDashboardDemo:
    """Enhanced dashboard demo med avancerade visualiseringar"""

    def __init__(self):
        self.config = Config()
        self.logger = ScrapingLogger(__name__)

        # Skapa enhanced scraper
        self.scraper = EnhancedRealScraper()
        self.proxy_manager = MockProxyManager()
        self.webhook_manager = MockWebhookManager()

        # Dashboard med avancerade visualiseringar
        self.dashboard = DashboardApp(self.config)
        self.dashboard.set_components(
            scraper=self.scraper,
            proxy_manager=self.proxy_manager,
            webhook_manager=self.webhook_manager,
        )

    async def start(self):
        """Startar enhanced dashboard demo"""
        self.logger.info("🚀 Starting Enhanced Dashboard Demo")

        # Starta scraper
        await self.scraper.start()

        # Starta scraping i bakgrunden
        scraping_thread = threading.Thread(target=self._run_scraping_loop)
        scraping_thread.daemon = True
        scraping_thread.start()

        # Starta dashboard på port 8082 för att undvika konflikter
        self.logger.info("🌐 Starting Enhanced Dashboard on http://127.0.0.1:8082")

        # Kör dashboard i bakgrunden
        dashboard_thread = threading.Thread(target=self._run_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()

        # Vänta lite för att låta allt starta
        await asyncio.sleep(3)

        self.logger.info("✅ Enhanced Dashboard Demo started successfully!")
        self.logger.info("📊 Open http://127.0.0.1:8082 to see advanced visualizations")

    def _run_scraping_loop(self):
        """Kör scraping-loop i bakgrunden"""
        urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml",
            "https://httpbin.org/headers",
            "https://httpbin.org/user-agent",
            "https://httpbin.org/robots.txt",
        ]

        while self.scraper.is_running:
            try:
                # Kör scraping i event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                for url in urls:
                    if not self.scraper.is_running:
                        break

                    result = loop.run_until_complete(self.scraper.scrape_url(url))

                    # Logga resultat
                    if "error" not in result:
                        self.logger.info(
                            f"✅ Scrapade {url} - Title: {result['title'][:50]}..., Links: {result['links']}"
                        )
                    else:
                        self.logger.warning(f"❌ Fel vid scraping av {url}: {result['error']}")

                    # Kort paus mellan requests
                    time.sleep(random.uniform(1, 3))

                # Logga live stats
                metrics = self.scraper.get_metrics()
                self.logger.info(
                    f"📊 Live stats - Requests: {metrics['requests_total']}, Success: {metrics['success_rate']:.1f}%, Uptime: {int(metrics['uptime_seconds'])}s"
                )

                loop.close()

            except Exception as e:
                self.logger.error(f"Error in scraping loop: {str(e)}")
                time.sleep(5)

    def _run_dashboard(self):
        """Kör dashboard på port 8082"""
        try:
            self.dashboard.run(host="127.0.0.1", port=8082)
        except Exception as e:
            self.logger.error(f"Dashboard error: {str(e)}")


async def main():
    """Huvudfunktion"""
    demo = EnhancedDashboardDemo()
    await demo.start()

    # Håll igång
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await demo.scraper.stop()
        print("\n👋 Enhanced Dashboard Demo stopped")


if __name__ == "__main__":
    asyncio.run(main())
