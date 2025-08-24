"""
Distribuerad scraping med Redis-queue för storskalig scraping
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

from .core import WebScraper, ScrapingResult
from ..utils.config import Config


class TaskStatus(Enum):
    """Status för scraping-uppgifter"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScrapingTask:
    """En scraping-uppgift"""

    id: str
    url: str
    selectors: Optional[Dict[str, str]] = None
    parser_config: Optional[Dict[str, Any]] = None
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    worker_id: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Konverterar till dictionary för Redis-lagring"""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScrapingTask":
        """Skapar från dictionary från Redis"""
        data["status"] = TaskStatus(data["status"])
        return cls(**data)


class DistributedScraper:
    """
    Distribuerad scraper med Redis-queue
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = structlog.get_logger(__name__)

        # Redis-konfiguration
        self.redis_url = self.config.get("redis.url", "redis://localhost:6379")
        self.queue_name = self.config.get("redis.queue_name", "scraping_tasks")
        self.result_queue = self.config.get("redis.result_queue", "scraping_results")
        self.worker_id = str(uuid.uuid4())

        # Worker-konfiguration
        self.max_concurrent_tasks = self.config.get("distributed.max_concurrent_tasks", 5)
        self.task_timeout = self.config.get("distributed.task_timeout", 300)
        self.heartbeat_interval = self.config.get("distributed.heartbeat_interval", 30)

        # Redis-klient
        self.redis = None
        self.scraper = None

        # Worker-state
        self.is_running = False
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.heartbeat_task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Startar distribuerad scraper"""
        try:
            # Initiera Redis-klient
            import aioredis

            self.redis = aioredis.from_url(self.redis_url)

            # Testa Redis-anslutning
            await self.redis.ping()
            self.logger.info(f"Connected to Redis: {self.redis_url}")

            # Initiera scraper
            self.scraper = WebScraper(self.config)
            await self.scraper.start()

            # Starta worker
            self.is_running = True
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            self.logger.info(f"Distributed scraper started with worker ID: {self.worker_id}")

        except Exception as e:
            self.logger.error(f"Failed to start distributed scraper: {str(e)}")
            raise

    async def stop(self):
        """Stoppar distribuerad scraper"""
        self.is_running = False

        # Stoppa alla aktiva uppgifter
        for task in self.active_tasks.values():
            task.cancel()

        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)

        # Stoppa heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        # Stoppa scraper
        if self.scraper:
            await self.scraper.stop()

        # Stäng Redis-anslutning
        if self.redis:
            await self.redis.close()

        self.logger.info("Distributed scraper stopped")

    async def add_task(
        self,
        url: str,
        selectors: Optional[Dict[str, str]] = None,
        parser_config: Optional[Dict[str, Any]] = None,
        priority: int = 0,
    ) -> str:
        """Lägger till en scraping-uppgift i kön"""
        task = ScrapingTask(
            id=str(uuid.uuid4()), url=url, selectors=selectors, parser_config=parser_config, priority=priority
        )

        # Lägg till i Redis-queue (prioriterad)
        await self.redis.zadd(self.queue_name, {json.dumps(task.to_dict()): priority})

        self.logger.info(f"Added task {task.id} for URL: {url}")
        return task.id

    async def add_batch_tasks(
        self,
        urls: List[str],
        selectors: Optional[Dict[str, str]] = None,
        parser_config: Optional[Dict[str, Any]] = None,
        priority: int = 0,
    ) -> List[str]:
        """Lägger till flera scraping-uppgifter"""
        task_ids = []

        for url in urls:
            task_id = await self.add_task(url, selectors, parser_config, priority)
            task_ids.append(task_id)

        self.logger.info(f"Added {len(task_ids)} batch tasks")
        return task_ids

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Hämtar status för en uppgift"""
        try:
            # Sök i resultat-kön
            result_data = await self.redis.hget(self.result_queue, task_id)
            if result_data:
                return json.loads(result_data)

            # Sök i aktiv-kön
            active_data = await self.redis.hget(f"{self.queue_name}:active", task_id)
            if active_data:
                return json.loads(active_data)

            return None

        except Exception as e:
            self.logger.error(f"Error getting task status for {task_id}: {str(e)}")
            return None

    async def cancel_task(self, task_id: str) -> bool:
        """Avbryter en uppgift"""
        try:
            # Markera som avbruten i resultat-kön
            result_data = {"id": task_id, "status": TaskStatus.CANCELLED.value, "cancelled_at": time.time()}

            await self.redis.hset(self.result_queue, task_id, json.dumps(result_data))

            # Ta bort från aktiv-kön
            await self.redis.hdel(f"{self.queue_name}:active", task_id)

            self.logger.info(f"Cancelled task {task_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return False

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Hämtar statistik för kön"""
        try:
            pending_count = await self.redis.zcard(self.queue_name)
            active_count = await self.redis.hlen(f"{self.queue_name}:active")
            completed_count = await self.redis.hlen(self.result_queue)

            return {
                "pending_tasks": pending_count,
                "active_tasks": active_count,
                "completed_tasks": completed_count,
                "worker_id": self.worker_id,
                "is_running": self.is_running,
            }

        except Exception as e:
            self.logger.error(f"Error getting queue stats: {str(e)}")
            return {}

    async def start_worker(self):
        """Startar worker-processen"""
        self.logger.info(f"Starting worker {self.worker_id}")

        while self.is_running:
            try:
                # Hämta nästa uppgift från kön
                task_data = await self._get_next_task()
                if not task_data:
                    await asyncio.sleep(1)
                    continue

                # Kontrollera antal aktiva uppgifter
                if len(self.active_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.1)
                    continue

                # Starta uppgift
                task = asyncio.create_task(self._process_task(task_data))
                self.active_tasks[task_data["id"]] = task

                # Rensa slutförda uppgifter
                await self._cleanup_completed_tasks()

            except Exception as e:
                self.logger.error(f"Error in worker loop: {str(e)}")
                await asyncio.sleep(1)

    async def _get_next_task(self) -> Optional[Dict[str, Any]]:
        """Hämtar nästa uppgift från kön"""
        try:
            # Hämta högst prioriterad uppgift
            result = await self.redis.zpopmax(self.queue_name, 1)
            if not result:
                return None

            task_json, priority = result[0]
            task_data = json.loads(task_json)

            # Markera som aktiv
            task_data["status"] = TaskStatus.PROCESSING.value
            task_data["started_at"] = time.time()
            task_data["worker_id"] = self.worker_id

            await self.redis.hset(f"{self.queue_name}:active", task_data["id"], json.dumps(task_data))

            return task_data

        except Exception as e:
            self.logger.error(f"Error getting next task: {str(e)}")
            return None

    async def _process_task(self, task_data: Dict[str, Any]):
        """Bearbetar en scraping-uppgift"""
        task_id = task_data["id"]
        url = task_data["url"]

        try:
            self.logger.info(f"Processing task {task_id}: {url}")

            # Utför scraping
            result = await self.scraper.scrape_url(
                url=url, selectors=task_data.get("selectors"), parser_config=task_data.get("parser_config")
            )

            # Uppdatera resultat
            task_data["status"] = TaskStatus.COMPLETED.value
            task_data["completed_at"] = time.time()
            task_data["result"] = result.to_dict() if result else None

        except Exception as e:
            self.logger.error(f"Error processing task {task_id}: {str(e)}")

            # Hantera retry
            retry_count = task_data.get("retry_count", 0)
            max_retries = task_data.get("max_retries", 3)

            if retry_count < max_retries:
                task_data["retry_count"] = retry_count + 1
                task_data["status"] = TaskStatus.PENDING.value

                # Lägg tillbaka i kön
                await self.redis.zadd(self.queue_name, {json.dumps(task_data): task_data.get("priority", 0)})
            else:
                task_data["status"] = TaskStatus.FAILED.value
                task_data["completed_at"] = time.time()
                task_data["error"] = str(e)

        finally:
            # Ta bort från aktiv-kön
            await self.redis.hdel(f"{self.queue_name}:active", task_id)

            # Spara resultat
            await self.redis.hset(self.result_queue, task_id, json.dumps(task_data))

            # Ta bort från aktiva uppgifter
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    async def _cleanup_completed_tasks(self):
        """Rensar slutförda uppgifter från aktiva listan"""
        completed_tasks = []

        for task_id, task in self.active_tasks.items():
            if task.done():
                completed_tasks.append(task_id)

        for task_id in completed_tasks:
            del self.active_tasks[task_id]

    async def _heartbeat_loop(self):
        """Heartbeat-loop för worker"""
        while self.is_running:
            try:
                heartbeat_data = {
                    "worker_id": self.worker_id,
                    "timestamp": time.time(),
                    "active_tasks": len(self.active_tasks),
                    "is_running": self.is_running,
                }

                await self.redis.hset(f"{self.queue_name}:heartbeat", self.worker_id, json.dumps(heartbeat_data))

                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {str(e)}")
                await asyncio.sleep(5)

    async def get_worker_stats(self) -> Dict[str, Any]:
        """Hämtar statistik för alla workers"""
        try:
            heartbeats = await self.redis.hgetall(f"{self.queue_name}:heartbeat")
            workers = []

            for worker_id, heartbeat_json in heartbeats.items():
                heartbeat_data = json.loads(heartbeat_json)
                workers.append(heartbeat_data)

            return {"workers": workers, "total_workers": len(workers)}

        except Exception as e:
            self.logger.error(f"Error getting worker stats: {str(e)}")
            return {"workers": [], "total_workers": 0}

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Väntar på att en uppgift ska slutföras"""
        start_time = time.time()

        while True:
            result = await self.get_task_status(task_id)

            if result and result.get("status") in [
                TaskStatus.COMPLETED.value,
                TaskStatus.FAILED.value,
                TaskStatus.CANCELLED.value,
            ]:
                return result

            if timeout and (time.time() - start_time) > timeout:
                return None

            await asyncio.sleep(1)

    async def get_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Hämtar slutförda resultat"""
        try:
            results = []
            cursor = 0

            while True:
                cursor, items = await self.redis.hscan(self.result_queue, cursor, count=limit)

                for task_id, result_json in items:
                    result_data = json.loads(result_json)
                    if result_data.get("status") in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                        results.append(result_data)

                if cursor == 0 or len(results) >= limit:
                    break

            return results[:limit]

        except Exception as e:
            self.logger.error(f"Error getting results: {str(e)}")
            return []
