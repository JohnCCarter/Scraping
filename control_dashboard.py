#!/usr/bin/env python3
"""
🎮 CONTROL DASHBOARD - START/STOP & JOB MANAGEMENT
Steg B: Avancerade kontroller, job management, real-time monitoring
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


class JobStatus(Enum):
    """Job status enum"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Job priority enum"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class ScrapingJob:
    """Representerar ett scraping-job"""

    def __init__(self, job_id: str, urls: List[str], priority: JobPriority = JobPriority.NORMAL):
        self.job_id = job_id
        self.urls = urls
        self.priority = priority
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress = 0.0  # 0-100%
        self.results: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.metadata = {
            "total_urls": len(urls),
            "processed_urls": 0,
            "successful_urls": 0,
            "failed_urls": 0,
            "average_response_time": 0.0,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Konverterar job till dictionary"""
        return {
            "job_id": self.job_id,
            "urls": self.urls,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (self.completed_at.isoformat() if self.completed_at else None),
            "progress": self.progress,
            "results_count": len(self.results),
            "errors_count": len(self.errors),
            "metadata": self.metadata,
        }


class JobManager:
    """Hanterar scraping-jobs"""

    def __init__(self):
        self.jobs: Dict[str, ScrapingJob] = {}
        self.job_queue: List[str] = []
        self.active_jobs: List[str] = []
        self.completed_jobs: List[str] = []
        self.max_concurrent_jobs = 3
        self.is_running = False

    def create_job(self, urls: List[str], priority: JobPriority = JobPriority.NORMAL) -> str:
        """Skapar ett nytt job"""
        job_id = f"job_{int(time.time())}_{random.randint(1000, 9999)}"
        job = ScrapingJob(job_id, urls, priority)
        self.jobs[job_id] = job
        self.job_queue.append(job_id)
        return job_id

    def start_job(self, job_id: str) -> bool:
        """Startar ett job"""
        if job_id not in self.jobs:
            return False

        job = self.jobs[job_id]
        if job.status != JobStatus.PENDING:
            return False

        if len(self.active_jobs) >= self.max_concurrent_jobs:
            return False

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        self.active_jobs.append(job_id)

        if job_id in self.job_queue:
            self.job_queue.remove(job_id)

        return True

    def pause_job(self, job_id: str) -> bool:
        """Pausar ett job"""
        if job_id not in self.jobs or job_id not in self.active_jobs:
            return False

        job = self.jobs[job_id]
        if job.status != JobStatus.RUNNING:
            return False

        job.status = JobStatus.PAUSED
        self.active_jobs.remove(job_id)
        self.job_queue.insert(0, job_id)  # Lägg tillbaka i kön med högsta prioritet
        return True

    def resume_job(self, job_id: str) -> bool:
        """Återupptar ett job"""
        if job_id not in self.jobs:
            return False

        job = self.jobs[job_id]
        if job.status != JobStatus.PAUSED:
            return False

        return self.start_job(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Avbryter ett job"""
        if job_id not in self.jobs:
            return False

        job = self.jobs[job_id]
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()

        if job_id in self.active_jobs:
            self.active_jobs.remove(job_id)
        if job_id in self.job_queue:
            self.job_queue.remove(job_id)

        return True

    def complete_job(self, job_id: str) -> bool:
        """Markerar ett job som slutfört"""
        if job_id not in self.jobs or job_id not in self.active_jobs:
            return False

        job = self.jobs[job_id]
        job.status = JobStatus.COMPLETED
        job.progress = 100.0
        job.completed_at = datetime.now()

        self.active_jobs.remove(job_id)
        self.completed_jobs.append(job_id)
        return True

    def get_job_stats(self) -> Dict[str, Any]:
        """Returnerar job-statistik"""
        total_jobs = len(self.jobs)
        pending_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.PENDING])
        running_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])
        completed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.COMPLETED])
        failed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.FAILED])
        paused_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.PAUSED])

        return {
            "total_jobs": total_jobs,
            "pending_jobs": pending_jobs,
            "running_jobs": running_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "paused_jobs": paused_jobs,
            "queue_size": len(self.job_queue),
            "active_jobs": len(self.active_jobs),
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "is_running": self.is_running,
        }

    def get_jobs_list(self) -> List[Dict[str, Any]]:
        """Returnerar lista över alla jobs"""
        return [job.to_dict() for job in self.jobs.values()]


class ControlledScraper:
    """Scraper med avancerade kontroller"""

    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.session = None
        self.is_running = False
        self.is_paused = False
        self.current_job_id: Optional[str] = None

        # Avancerade metrics
        self.hourly_requests = [0] * 24
        self.daily_requests = [0] * 7
        self.response_times = []
        self.status_codes = {}
        self.url_patterns = {}
        self.geo_data = []

        # Job manager
        self.job_manager = JobManager()

    async def start(self):
        """Startar scraper"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": "ControlledScraper/1.0"},
        )
        self.is_running = True
        self.job_manager.is_running = True

    async def stop(self):
        """Stoppar scraper"""
        if self.session:
            await self.session.close()
        self.is_running = False
        self.job_manager.is_running = False

    def pause(self):
        """Pausar scraper"""
        self.is_paused = True

    def resume(self):
        """Återupptar scraper"""
        self.is_paused = False

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrapar en URL"""
        if not self.is_running or self.is_paused:
            return {
                "url": url,
                "error": "Scraper is not running or paused",
                "status": "error",
            }

        start_time = time.time()

        try:
            async with self.session.get(url) as response:
                content = await response.text()
                response_time = time.time() - start_time

                # Uppdatera metrics
                self._update_metrics(response.status, response_time, url)

                # Parse content
                soup = BeautifulSoup(content, "html.parser")
                title = soup.find("title")
                title_text = title.get_text() if title else "No title"

                return {
                    "url": url,
                    "title": title_text,
                    "status": response.status,
                    "response_time": response_time,
                    "content_length": len(content),
                    "links": len(soup.find_all("a")),
                }

        except Exception as e:
            self.request_count += 1
            self.error_count += 1
            return {"url": url, "error": str(e), "status": "error"}

    def _update_metrics(self, status: int, response_time: float, url: str):
        """Uppdaterar metrics"""
        self.request_count += 1
        self.success_count += 1
        self.response_times.append(response_time)

        # Timestamp analysis
        hour = datetime.now().hour
        self.hourly_requests[hour] += 1

        day = datetime.now().weekday()
        self.daily_requests[day] += 1

        # Status code tracking
        self.status_codes[status] = self.status_codes.get(status, 0) + 1

        # URL pattern analysis
        domain = url.split("/")[2] if len(url.split("/")) > 2 else "unknown"
        self.url_patterns[domain] = self.url_patterns.get(domain, 0) + 1

        # Simulerad geografisk data
        self.geo_data.append(
            {
                "lat": random.uniform(55.0, 70.0),
                "lng": random.uniform(10.0, 25.0),
                "requests": 1,
                "response_time": response_time,
            }
        )

    def create_job(self, urls: List[str], priority: JobPriority = JobPriority.NORMAL) -> str:
        """Skapar ett nytt scraping-job"""
        return self.job_manager.create_job(urls, priority)

    def start_job(self, job_id: str) -> bool:
        """Startar ett job"""
        return self.job_manager.start_job(job_id)

    def pause_job(self, job_id: str) -> bool:
        """Pausar ett job"""
        return self.job_manager.pause_job(job_id)

    def resume_job(self, job_id: str) -> bool:
        """Återupptar ett job"""
        return self.job_manager.resume_job(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Avbryter ett job"""
        return self.job_manager.cancel_job(job_id)

    def get_metrics(self) -> Dict[str, Any]:
        """Returnerar metrics"""
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
            "is_paused": self.is_paused,
            "requests_per_minute": random.randint(10, 50),
            # Avancerade metrics
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
            "geo_data": self.geo_data[-100:],
            "performance_score": self._calculate_performance_score(),
            # Job metrics
            "job_stats": self.job_manager.get_job_stats(),
            "current_job_id": self.current_job_id,
        }

    def _get_response_time_distribution(self) -> Dict[str, int]:
        """Beräknar response time distribution"""
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
        """Beräknar performance score"""
        if self.request_count == 0:
            return 0.0

        # Success rate (40% vikt)
        success_score = (self.success_count / self.request_count) * 40

        # Response time score (30% vikt)
        if self.response_times:
            avg_rt = sum(self.response_times) / len(self.response_times)
            rt_score = max(0, 30 - (avg_rt * 10))
        else:
            rt_score = 30

        # Request rate score (30% vikt)
        uptime_hours = (time.time() - self.start_time) / 3600
        if uptime_hours > 0:
            requests_per_hour = self.request_count / uptime_hours
            rate_score = min(30, requests_per_hour / 10)
        else:
            rate_score = 0

        return round(success_score + rt_score + rate_score, 1)


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


class ControlDashboardDemo:
    """Control dashboard demo med avancerade kontroller"""

    def __init__(self):
        self.config = Config()
        self.logger = ScrapingLogger(__name__)

        # Skapa controlled scraper
        self.scraper = ControlledScraper()
        self.proxy_manager = MockProxyManager()
        self.webhook_manager = MockWebhookManager()

        # Dashboard med kontroller
        self.dashboard = DashboardApp(self.config)
        self.dashboard.set_components(
            scraper=self.scraper,
            proxy_manager=self.proxy_manager,
            webhook_manager=self.webhook_manager,
        )

    async def start(self):
        """Startar control dashboard demo"""
        self.logger.info("🎮 Starting Control Dashboard Demo")

        # Starta scraper
        await self.scraper.start()

        # Skapa några exempel-jobs
        self._create_sample_jobs()

        # Starta job processing i bakgrunden
        job_thread = threading.Thread(target=self._run_job_processor)
        job_thread.daemon = True
        job_thread.start()

        # Starta dashboard på port 8083
        self.logger.info("🌐 Starting Control Dashboard on http://127.0.0.1:8083")

        dashboard_thread = threading.Thread(target=self._run_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()

        await asyncio.sleep(3)

        self.logger.info("✅ Control Dashboard Demo started successfully!")
        self.logger.info("🎮 Open http://127.0.0.1:8083 to see advanced controls")

    def _create_sample_jobs(self):
        """Skapar exempel-jobs"""
        urls_1 = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml",
        ]

        urls_2 = [
            "https://httpbin.org/headers",
            "https://httpbin.org/user-agent",
            "https://httpbin.org/robots.txt",
        ]

        urls_3 = [
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/2",
            "https://httpbin.org/delay/3",
        ]

        # Skapa jobs med olika prioriteter
        self.scraper.create_job(urls_1, JobPriority.HIGH)
        self.scraper.create_job(urls_2, JobPriority.NORMAL)
        self.scraper.create_job(urls_3, JobPriority.LOW)

        self.logger.info("📋 Created sample jobs with different priorities")

    def _run_job_processor(self):
        """Kör job processor i bakgrunden"""
        while self.scraper.is_running:
            try:
                # Processa aktiva jobs
                for job_id in self.scraper.job_manager.active_jobs[:]:
                    job = self.scraper.job_manager.jobs[job_id]

                    if job.status == JobStatus.RUNNING:
                        # Simulera job processing
                        job.progress += random.uniform(5, 15)

                        if job.progress >= 100:
                            self.scraper.job_manager.complete_job(job_id)
                            self.logger.info(f"✅ Completed job {job_id}")
                        else:
                            # Simulera scraping av en URL
                            if job.metadata["processed_urls"] < job.metadata["total_urls"]:
                                job.metadata["processed_urls"] += 1
                                job.metadata["successful_urls"] += 1

                # Starta nya jobs från kön
                while (
                    len(self.scraper.job_manager.active_jobs) < self.scraper.job_manager.max_concurrent_jobs
                    and self.scraper.job_manager.job_queue
                ):

                    next_job_id = self.scraper.job_manager.job_queue[0]
                    if self.scraper.job_manager.start_job(next_job_id):
                        self.logger.info(f"🚀 Started job {next_job_id}")

                time.sleep(2)

            except Exception as e:
                self.logger.error(f"Error in job processor: {str(e)}")
                time.sleep(5)

    def _run_dashboard(self):
        """Kör dashboard på port 8083"""
        try:
            self.dashboard.run(host="127.0.0.1", port=8083)
        except Exception as e:
            self.logger.error(f"Dashboard error: {str(e)}")


async def main():
    """Huvudfunktion"""
    demo = ControlDashboardDemo()
    await demo.start()

    # Håll igång
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await demo.scraper.stop()
        print("\n👋 Control Dashboard Demo stopped")


if __name__ == "__main__":
    asyncio.run(main())
