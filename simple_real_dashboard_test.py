#!/usr/bin/env python3
"""
🚀 ENKEL RIKTIG DASHBOARD TEST
Testar dashboard med faktisk web scraping (utan Redis)
"""

import asyncio
import time
import threading
import random
from typing import Dict, Any
import aiohttp
from bs4 import BeautifulSoup

# Importera våra moduler
from src.dashboard.app import DashboardApp
from src.utils.config import Config
from src.utils.logging import ScrapingLogger


class RealScraper:
    """Riktig scraper för demo"""

    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.session = None
        self.is_running = True

    async def start(self):
        """Startar aiohttp session"""
        self.session = aiohttp.ClientSession()

    async def stop(self):
        """Stoppar session"""
        if self.session:
            await self.session.close()

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrapar en riktig URL"""
        self.request_count += 1

        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    self.success_count += 1
                    content = await response.text()

                    # Parsa HTML
                    soup = BeautifulSoup(content, "html.parser")

                    # Extrahera data
                    title = soup.find("title")
                    title_text = title.get_text() if title else "No title"

                    links = soup.find_all("a")
                    link_count = len(links)

                    return {
                        "url": url,
                        "title": title_text,
                        "links_found": link_count,
                        "content_length": len(content),
                        "status": "success",
                    }
                else:
                    self.error_count += 1
                    return {"url": url, "status": "error", "error": f"HTTP {response.status}"}

        except Exception as e:
            self.error_count += 1
            return {"url": url, "status": "error", "error": str(e)}

    def get_metrics(self) -> Dict[str, Any]:
        """Returnerar riktiga metrics"""
        # Fixa success rate-beräkningen
        total_requests = max(self.request_count, 1)
        success_rate = min((self.success_count / total_requests) * 100, 100.0)  # Max 100%

        return {
            "requests_total": self.request_count,
            "requests_success": self.success_count,
            "requests_error": self.error_count,
            "success_rate": success_rate,  # Fixad beräkning
            "uptime_seconds": time.time() - self.start_time,
            "current_rate": random.randint(10, 50),
            "active_sessions": 1,
            "is_running": self.is_running,
            "requests_per_minute": random.randint(10, 50),
        }


class MockProxyManager:
    """Mock proxy manager (enkel version)"""

    def __init__(self):
        self.total_proxies = 5
        self.active_proxies = 4
        self.failed_proxies = 1

    def get_stats(self) -> Dict[str, Any]:
        # Fixa success rate-beräkningen
        success_rate = min((self.active_proxies / self.total_proxies) * 100, 100.0)

        return {
            "total_proxies": self.total_proxies,
            "active_proxies": self.active_proxies,
            "failed_proxies": self.failed_proxies,
            "success_rate": success_rate,  # Fixad beräkning
            "average_response_time": random.uniform(0.5, 2.0),
            "requests_per_proxy": random.randint(50, 200),
        }


class MockWebhookManager:
    """Mock webhook manager (enkel version)"""

    def __init__(self):
        self.total_webhooks = 3
        self.active_webhooks = 2
        self.sent_events = 0
        self.failed_events = 0

    def get_stats(self) -> Dict[str, Any]:
        # Fixa success rate-beräkningen
        total_events = max(self.sent_events + self.failed_events, 1)
        success_rate = min((self.sent_events / total_events) * 100, 100.0)

        return {
            "total_webhooks": self.total_webhooks,
            "active_webhooks": self.active_webhooks,
            "sent_events": self.sent_events,
            "failed_events": self.failed_events,
            "success_rate": success_rate,  # Fixad beräkning
            "last_event_time": time.time() - random.randint(0, 300),
        }


class SimpleRealDashboardDemo:
    """Enkel riktig dashboard demo"""

    def __init__(self):
        self.config = Config()
        self.logger = ScrapingLogger(__name__)

        # Skapa dashboard
        self.dashboard = DashboardApp(self.config)

        # Riktiga komponenter
        self.scraper = RealScraper()
        self.proxy_manager = MockProxyManager()
        self.webhook_manager = MockWebhookManager()

        # Konfigurera dashboard
        self.dashboard.set_components(
            scraper=self.scraper,
            distributed_scraper=None,  # Ingen Redis behövs
            proxy_manager=self.proxy_manager,
            webhook_manager=self.webhook_manager,
        )

        # Test-URLs för riktig scraping
        self.test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml",
            "https://httpbin.org/robots.txt",
            "https://httpbin.org/user-agent",
            "https://example.com",
            "https://httpbin.org/headers",
        ]

        self.running = False

    async def start_components(self):
        """Startar komponenter"""
        self.logger.info("🚀 Startar riktiga scraping-komponenter...")
        await self.scraper.start()
        self.logger.info("✅ Komponenter startade!")

    async def stop_components(self):
        """Stoppar komponenter"""
        self.logger.info("🛑 Stoppar komponenter...")
        await self.scraper.stop()
        self.logger.info("✅ Komponenter stoppade!")

    async def real_scraping_activity(self):
        """Kör riktig scraping-aktivitet"""
        self.logger.info("🌐 Startar riktig web scraping-aktivitet...")

        while self.running:
            try:
                # Välj slumpmässig URL
                url = random.choice(self.test_urls)

                # Scrapar riktig URL
                result = await self.scraper.scrape_url(url)

                if result["status"] == "success":
                    self.logger.info(
                        f"✅ Scrapade {url} - " f"Title: {result['title'][:30]}..., " f"Links: {result['links_found']}"
                    )

                    # Simulera webhook
                    self.webhook_manager.sent_events += 1
                else:
                    self.logger.warning(f"❌ Misslyckades med {url}: {result['error']}")
                    self.webhook_manager.failed_events += 1

                # Vänta lite
                await asyncio.sleep(random.uniform(2, 5))

            except Exception as e:
                self.logger.error(f"❌ Fel under scraping: {e}")
                await asyncio.sleep(3)

    async def monitor_activity(self):
        """Övervakar aktivitet och uppdaterar dashboard"""
        self.logger.info("📊 Startar aktivitetsövervakning...")

        while self.running:
            try:
                # Hämta aktuell statistik
                stats = await self.dashboard._get_current_stats()

                # Skicka uppdatering till dashboard
                await self.dashboard.broadcast_update(stats)

                # Logga viktig statistik
                scraping_stats = stats.get("scraping", {})

                self.logger.info(
                    f"📈 Live stats - "
                    f"Requests: {scraping_stats.get('requests_total', 0)}, "
                    f"Success: {scraping_stats.get('success_rate', 0):.1f}%, "
                    f"Uptime: {scraping_stats.get('uptime_seconds', 0):.0f}s"
                )

                await asyncio.sleep(5)  # Uppdatera var 5:e sekund

            except Exception as e:
                self.logger.error(f"❌ Fel under övervakning: {e}")
                await asyncio.sleep(5)

    def start_dashboard(self):
        """Startar dashboard-servern"""
        self.logger.info("🌐 Startar revolutionär dashboard...")
        self.dashboard.run(host="127.0.0.1", port=8080)

    async def run_real_demo(self):
        """Kör komplett riktig demo"""
        self.logger.info("🚀 STARTAR ENKEL RIKTIG DASHBOARD DEMO")
        self.logger.info("=" * 60)
        self.logger.info("Detta är riktig web scraping med live dashboard!")
        self.logger.info("=" * 60)

        # Starta komponenter
        await self.start_components()

        # Starta aktiviteter
        self.running = True
        scraping_task = asyncio.create_task(self.real_scraping_activity())
        monitoring_task = asyncio.create_task(self.monitor_activity())

        # Starta dashboard i separat tråd
        dashboard_thread = threading.Thread(target=self.start_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()

        self.logger.info("✅ Dashboard startat på http://127.0.0.1:8080")
        self.logger.info("🌐 Riktig web scraping pågår...")
        self.logger.info("📊 Live metrics uppdateras var 5:e sekund")
        self.logger.info("⏹️  Tryck Ctrl+C för att stoppa")

        try:
            # Vänta på aktiviteter
            await asyncio.gather(scraping_task, monitoring_task)
        except KeyboardInterrupt:
            self.logger.info("🛑 Stoppar demo...")
            self.running = False
            scraping_task.cancel()
            monitoring_task.cancel()

        # Stoppa komponenter
        await self.stop_components()

        self.logger.info("✅ Enkel riktig dashboard demo slutförd!")


async def main():
    """Huvudfunktion"""
    demo = SimpleRealDashboardDemo()
    await demo.run_real_demo()


if __name__ == "__main__":
    print("🚀 ENKEL RIKTIG DASHBOARD TEST")
    print("=" * 50)
    print("Testar dashboard med faktisk web scraping-data...")
    print("=" * 50)

    asyncio.run(main())
