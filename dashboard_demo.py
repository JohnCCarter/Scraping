#!/usr/bin/env python3
"""
🚀 REVOLUTIONÄR DASHBOARD DEMO
Testar web-baserat dashboard med real-time metrics
"""

import asyncio
import time
import threading
from typing import Dict, Any
import random

# Importera våra moduler
from src.dashboard.app import DashboardApp
from src.utils.config import Config
from src.utils.logging import ScrapingLogger


class MockScraper:
    """Mock scraper för demo-data"""

    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()

    def get_metrics(self) -> Dict[str, Any]:
        """Returnerar mock metrics"""
        return {
            "requests_total": self.request_count,
            "requests_success": self.success_count,
            "requests_error": self.error_count,
            "success_rate": (self.success_count / max(self.request_count, 1)) * 100,
            "uptime_seconds": time.time() - self.start_time,
            "current_rate": random.randint(10, 50),  # requests per minute
            "active_sessions": random.randint(1, 5),
            "is_running": True,  # Lägg till detta för att visa "Online" status
            "requests_per_minute": random.randint(10, 50),  # Lägg till detta för JavaScript
        }

    def simulate_request(self):
        """Simulerar en request"""
        self.request_count += 1
        if random.random() > 0.1:  # 90% success rate
            self.success_count += 1
        else:
            self.error_count += 1


class MockDistributedScraper:
    """Mock distributed scraper för demo-data"""

    def __init__(self):
        self.queue_size = 0
        self.active_workers = 0
        self.completed_tasks = 0
        self.failed_tasks = 0

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Returnerar mock queue stats"""
        return {
            "queue_size": self.queue_size,
            "active_workers": self.active_workers,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": (self.completed_tasks / max(self.completed_tasks + self.failed_tasks, 1)) * 100,
            "worker_utilization": random.randint(60, 95),
            "pending_tasks": self.queue_size,  # Lägg till detta för JavaScript
        }

    def simulate_task(self):
        """Simulerar en task"""
        if self.queue_size > 0:
            self.queue_size -= 1
            if random.random() > 0.05:  # 95% success rate
                self.completed_tasks += 1
            else:
                self.failed_tasks += 1


class MockProxyManager:
    """Mock proxy manager för demo-data"""

    def __init__(self):
        self.total_proxies = 10
        self.active_proxies = 8
        self.failed_proxies = 2

    def get_stats(self) -> Dict[str, Any]:
        """Returnerar mock proxy stats"""
        return {
            "total_proxies": self.total_proxies,
            "active_proxies": self.active_proxies,
            "failed_proxies": self.failed_proxies,
            "success_rate": (self.active_proxies / self.total_proxies) * 100,
            "average_response_time": random.uniform(0.5, 2.0),
            "requests_per_proxy": random.randint(100, 500),
        }


class MockWebhookManager:
    """Mock webhook manager för demo-data"""

    def __init__(self):
        self.total_webhooks = 5
        self.active_webhooks = 4
        self.sent_events = 0
        self.failed_events = 0

    def get_stats(self) -> Dict[str, Any]:
        """Returnerar mock webhook stats"""
        return {
            "total_webhooks": self.total_webhooks,
            "active_webhooks": self.active_webhooks,
            "sent_events": self.sent_events,
            "failed_events": self.failed_events,
            "success_rate": (self.sent_events / max(self.sent_events + self.failed_events, 1)) * 100,
            "last_event_time": time.time() - random.randint(0, 300),
        }


class DashboardDemo:
    """Demo för revolutionär dashboard"""

    def __init__(self):
        self.config = Config()
        self.logger = ScrapingLogger(__name__)

        # Skapa dashboard
        self.dashboard = DashboardApp(self.config)

        # Mock-komponenter
        self.mock_scraper = MockScraper()
        self.mock_distributed = MockDistributedScraper()
        self.mock_proxy = MockProxyManager()
        self.mock_webhook = MockWebhookManager()

        # Konfigurera dashboard med mock-komponenter
        self.dashboard.set_components(
            scraper=self.mock_scraper,
            distributed_scraper=self.mock_distributed,
            proxy_manager=self.mock_proxy,
            webhook_manager=self.mock_webhook,
        )

        self.running = False

    async def simulate_activity(self):
        """Simulerar aktivitet för att generera data"""
        self.logger.info("🚀 Startar simulering av scraping-aktivitet...")

        while self.running:
            # Simulera scraper-aktivitet
            self.mock_scraper.simulate_request()

            # Simulera distributed scraping
            if random.random() > 0.7:  # 30% chans att lägga till task
                self.mock_distributed.queue_size += 1

            if self.mock_distributed.queue_size > 0:
                self.mock_distributed.simulate_task()

            # Simulera webhook-aktivitet
            if random.random() > 0.8:  # 20% chans att skicka webhook
                if random.random() > 0.95:  # 5% chans att misslyckas
                    self.mock_webhook.failed_events += 1
                else:
                    self.mock_webhook.sent_events += 1

            # Skicka uppdatering till dashboard
            stats = await self.dashboard._get_current_stats()
            await self.dashboard.broadcast_update(stats)

            # Vänta 2 sekunder
            await asyncio.sleep(2)

    def start_dashboard(self):
        """Startar dashboard-servern"""
        self.logger.info("🌐 Startar revolutionär dashboard...")
        self.dashboard.run(host="127.0.0.1", port=8080)

    async def run_demo(self):
        """Kör komplett dashboard-demo"""
        self.logger.info("🚀 STARTAR REVOLUTIONÄR DASHBOARD DEMO")
        self.logger.info("=" * 60)
        self.logger.info("Detta är framtidens web scraping dashboard!")
        self.logger.info("=" * 60)

        # Starta simulering i bakgrunden
        self.running = True
        simulation_task = asyncio.create_task(self.simulate_activity())

        # Starta dashboard i separat tråd
        dashboard_thread = threading.Thread(target=self.start_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()

        self.logger.info("✅ Dashboard startat på http://127.0.0.1:8080")
        self.logger.info("📊 Öppna webbläsaren för att se real-time metrics!")
        self.logger.info("🔄 Simulering av aktivitet pågår...")
        self.logger.info("⏹️  Tryck Ctrl+C för att stoppa")

        try:
            # Vänta på simulering
            await simulation_task
        except KeyboardInterrupt:
            self.logger.info("🛑 Stoppar demo...")
            self.running = False
            simulation_task.cancel()

        self.logger.info("✅ Dashboard demo slutförd!")


async def main():
    """Huvudfunktion"""
    demo = DashboardDemo()
    await demo.run_demo()


if __name__ == "__main__":
    print("🚀 REVOLUTIONÄR DASHBOARD DEMO")
    print("=" * 50)
    print("Startar web-baserat dashboard med real-time metrics...")
    print("=" * 50)

    asyncio.run(main())
