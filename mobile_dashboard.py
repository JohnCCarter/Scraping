#!/usr/bin/env python3
"""
📱 MOBILE DASHBOARD - RESPONSIVE DESIGN & MOBILE APP
Steg D: Mobile-first design, touch-friendly interface, responsive features
"""

import asyncio
import time
import threading
import random
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
from bs4 import BeautifulSoup

# Importera våra moduler
from src.dashboard.app import DashboardApp
from src.utils.config import Config
from src.utils.logging import ScrapingLogger


class MobileDeviceType(Enum):
    """Mobile device types"""

    PHONE = "phone"
    TABLET = "tablet"
    DESKTOP = "desktop"


class TouchGesture(Enum):
    """Touch gestures"""

    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    TAP = "tap"
    LONG_PRESS = "long_press"
    PINCH = "pinch"


class MobileScraper:
    """Mobile-optimized scraper med touch-friendly features"""

    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.session = None
        self.is_running = False

        # Mobile-specific features
        self.device_type = MobileDeviceType.PHONE
        self.touch_gestures = []
        self.mobile_metrics = {}
        self.responsive_breakpoints = {"phone": 768, "tablet": 1024, "desktop": 1200}

        # Mobile performance
        self.mobile_performance = {
            "load_time": 0.0,
            "touch_responsiveness": 0.0,
            "battery_optimization": 0.0,
            "offline_capability": 0.0,
        }

    async def start(self):
        """Startar mobile scraper"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": "MobileScraper/1.0"},
        )
        self.is_running = True

    async def stop(self):
        """Stoppar mobile scraper"""
        if self.session:
            await self.session.close()
        self.is_running = False

    async def scrape_mobile_optimized(self, url: str) -> Dict[str, Any]:
        """Scrapar med mobile-optimization"""
        if not self.is_running:
            return {"url": url, "error": "Scraper is not running", "status": "error"}

        start_time = time.time()

        try:
            async with self.session.get(url) as response:
                content = await response.text()
                response_time = time.time() - start_time

                # Mobile-optimized content processing
                mobile_analysis = await self._analyze_mobile_content(content, url)

                # Uppdatera metrics
                self._update_mobile_metrics(response.status, response_time, mobile_analysis)

                return {
                    "url": url,
                    "status": response.status,
                    "response_time": response_time,
                    "mobile_analysis": mobile_analysis,
                    "content_length": len(content),
                    "device_type": self.device_type.value,
                }

        except Exception as e:
            self.request_count += 1
            self.error_count += 1
            return {"url": url, "error": str(e), "status": "error"}

    async def _analyze_mobile_content(self, content: str, url: str) -> Dict[str, Any]:
        """Analyserar innehåll för mobile-optimization"""
        analysis = {
            "mobile_friendly": False,
            "touch_elements": 0,
            "responsive_design": False,
            "performance_score": 0.0,
            "accessibility_score": 0.0,
        }

        try:
            soup = BeautifulSoup(content, "html.parser")

            # Kolla mobile-friendly features
            viewport_meta = soup.find("meta", attrs={"name": "viewport"})
            if viewport_meta:
                analysis["mobile_friendly"] = True

            # Räkna touch-friendly element
            touch_elements = soup.find_all(["button", "a", "input", "select"])
            analysis["touch_elements"] = len(touch_elements)

            # Kolla responsive design
            css_links = soup.find_all("link", attrs={"rel": "stylesheet"})
            for link in css_links:
                href = link.get("href", "")
                if "responsive" in href.lower() or "mobile" in href.lower():
                    analysis["responsive_design"] = True
                    break

            # Beräkna performance score
            analysis["performance_score"] = self._calculate_mobile_performance(soup)

            # Beräkna accessibility score
            analysis["accessibility_score"] = self._calculate_accessibility_score(soup)

        except Exception as e:
            analysis["error"] = str(e)

        return analysis

    def _calculate_mobile_performance(self, soup) -> float:
        """Beräknar mobile performance score"""
        score = 0.0

        # Kolla efter optimeringar
        if soup.find("meta", attrs={"name": "viewport"}):
            score += 0.3

        # Kolla efter lazy loading
        images = soup.find_all("img")
        lazy_images = [img for img in images if img.get("loading") == "lazy"]
        if lazy_images:
            score += 0.2

        # Kolla efter minifierade resurser
        scripts = soup.find_all("script")
        for script in scripts:
            src = script.get("src", "")
            if ".min." in src:
                score += 0.1
                break

        # Kolla efter CSS optimeringar
        styles = soup.find_all("style")
        if styles:
            score += 0.1

        return min(score, 1.0)

    def _calculate_accessibility_score(self, soup) -> float:
        """Beräknar accessibility score"""
        score = 0.0

        # Kolla efter alt-text på bilder
        images = soup.find_all("img")
        if images:
            alt_images = [img for img in images if img.get("alt")]
            score += (len(alt_images) / len(images)) * 0.3

        # Kolla efter ARIA labels
        aria_elements = soup.find_all(attrs={"aria-label": True})
        if aria_elements:
            score += 0.2

        # Kolla efter semantic HTML
        semantic_elements = soup.find_all(["nav", "main", "section", "article", "aside", "footer"])
        if semantic_elements:
            score += 0.2

        # Kolla efter keyboard navigation
        focusable_elements = soup.find_all(["button", "a", "input", "select", "textarea"])
        if focusable_elements:
            score += 0.1

        return min(score, 1.0)

    def _update_mobile_metrics(self, status: int, response_time: float, mobile_analysis: Dict[str, Any]):
        """Uppdaterar mobile metrics"""
        self.request_count += 1
        self.success_count += 1

        # Uppdatera mobile performance
        self.mobile_performance["load_time"] = response_time
        self.mobile_performance["touch_responsiveness"] = mobile_analysis.get("touch_elements", 0) / 100

        # Lägg till touch gesture
        self.touch_gestures.append(
            {
                "type": TouchGesture.TAP.value,
                "timestamp": datetime.now().isoformat(),
                "url": mobile_analysis.get("url", ""),
            }
        )

        # Uppdatera mobile metrics
        self.mobile_metrics = {
            "mobile_friendly_sites": sum(1 for _ in self.touch_gestures if _["type"] == TouchGesture.TAP.value),
            "responsive_sites": sum(1 for _ in self.touch_gestures if mobile_analysis.get("responsive_design", False)),
            "performance_avg": self.mobile_performance["load_time"],
            "accessibility_avg": mobile_analysis.get("accessibility_score", 0),
        }

    def set_device_type(self, device_type: MobileDeviceType):
        """Sätter device type"""
        self.device_type = device_type

    def get_mobile_metrics(self) -> Dict[str, Any]:
        """Returnerar mobile metrics"""
        total_requests = max(self.request_count, 1)
        success_rate = min((self.success_count / total_requests) * 100, 100.0)

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
            # Mobile-specific metrics
            "device_type": self.device_type.value,
            "mobile_friendly_sites": self.mobile_metrics.get("mobile_friendly_sites", 0),
            "responsive_sites": self.mobile_metrics.get("responsive_sites", 0),
            "performance_avg": round(self.mobile_performance["load_time"], 2),
            "accessibility_avg": round(self.mobile_metrics.get("accessibility_avg", 0) * 100, 1),
            "touch_gestures_count": len(self.touch_gestures),
            "battery_optimization": round(self.mobile_performance["battery_optimization"] * 100, 1),
            "offline_capability": round(self.mobile_performance["offline_capability"] * 100, 1),
        }


class MockProxyManager:
    """Mock proxy manager"""

    def __init__(self):
        self.total_proxies = 10
        self.active_proxies = 8
        self.failed_proxies = 2

    def get_stats(self) -> Dict[str, Any]:
        success_rate = min((self.active_proxies / self.total_proxies) * 100, 100.0)
        return {
            "total_proxies": self.total_proxies,
            "active_proxies": self.active_proxies,
            "failed_proxies": self.failed_proxies,
            "success_rate": success_rate,
            "average_response_time": random.uniform(0.5, 2.0),
            "requests_per_proxy": random.randint(50, 200),
        }


class MockWebhookManager:
    """Mock webhook manager"""

    def __init__(self):
        self.total_webhooks = 5
        self.active_webhooks = 4
        self.sent_events = 150
        self.failed_events = 2

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
        }


class MobileDashboardDemo:
    """Mobile dashboard demo med responsive design"""

    def __init__(self):
        self.config = Config()
        self.logger = ScrapingLogger(__name__)

        # Skapa mobile scraper
        self.scraper = MobileScraper()
        self.proxy_manager = MockProxyManager()
        self.webhook_manager = MockWebhookManager()

        # Dashboard med mobile features
        self.dashboard = DashboardApp(self.config)
        self.dashboard.set_components(
            scraper=self.scraper,
            proxy_manager=self.proxy_manager,
            webhook_manager=self.webhook_manager,
        )

    async def start(self):
        """Startar mobile dashboard demo"""
        self.logger.info("📱 Starting Mobile Dashboard Demo")

        # Starta mobile scraper
        await self.scraper.start()

        # Starta mobile scraping i bakgrunden
        scraping_thread = threading.Thread(target=self._run_mobile_scraping)
        scraping_thread.daemon = True
        scraping_thread.start()

        # Starta dashboard på port 8085
        self.logger.info("🌐 Starting Mobile Dashboard on http://127.0.0.1:8085")

        dashboard_thread = threading.Thread(target=self._run_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()

        await asyncio.sleep(3)

        self.logger.info("✅ Mobile Dashboard Demo started successfully!")
        self.logger.info("📱 Open http://127.0.0.1:8085 to see mobile-optimized features")

    def _run_mobile_scraping(self):
        """Kör mobile scraping i bakgrunden"""
        urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml",
            "https://httpbin.org/headers",
            "https://httpbin.org/user-agent",
        ]

        while self.scraper.is_running:
            try:
                # Välj slumpmässig URL
                url = random.choice(urls)

                # Simulera mobile scraping
                asyncio.run(self.scraper.scrape_mobile_optimized(url))

                time.sleep(random.uniform(2, 5))

            except Exception as e:
                self.logger.error(f"Error in mobile scraping: {str(e)}")
                time.sleep(5)

    def _run_dashboard(self):
        """Kör dashboard på port 8085"""
        try:
            self.dashboard.run(host="127.0.0.1", port=8085)
        except Exception as e:
            self.logger.error(f"Dashboard error: {str(e)}")


async def main():
    """Huvudfunktion"""
    demo = MobileDashboardDemo()
    await demo.start()

    # Håll igång
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await demo.scraper.stop()
        print("\n👋 Mobile Dashboard Demo stopped")


if __name__ == "__main__":
    asyncio.run(main())
