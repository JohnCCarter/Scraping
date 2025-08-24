"""
Webhook-stöd för real-time notifieringar
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

from ..utils.config import Config


class WebhookEvent(Enum):
    """Typer av webhook-händelser"""

    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    SCRAPING_STARTED = "scraping_started"
    SCRAPING_COMPLETED = "scraping_completed"
    SCRAPING_FAILED = "scraping_failed"
    RATE_LIMIT_HIT = "rate_limit_hit"
    PROXY_FAILED = "proxy_failed"
    HEALTH_CHECK_FAILED = "health_check_failed"
    WORKER_STARTED = "worker_started"
    WORKER_STOPPED = "worker_stopped"


@dataclass
class WebhookPayload:
    """Webhook-payload"""

    event: WebhookEvent
    timestamp: float
    data: Dict[str, Any]
    source: str = "web_scraping_toolkit"

    def to_dict(self) -> Dict[str, Any]:
        """Konverterar till dictionary"""
        return {"event": self.event.value, "timestamp": self.timestamp, "data": self.data, "source": self.source}


@dataclass
class WebhookConfig:
    """Konfiguration för en webhook"""

    url: str
    events: List[WebhookEvent]
    headers: Optional[Dict[str, str]] = None
    timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 5.0
    is_active: bool = True
    secret: Optional[str] = None  # För signature verification

    def to_dict(self) -> Dict[str, Any]:
        """Konverterar till dictionary"""
        return {
            "url": self.url,
            "events": [event.value for event in self.events],
            "headers": self.headers or {},
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "is_active": self.is_active,
            "secret": self.secret,
        }


class WebhookManager:
    """
    Hanterar webhook-notifieringar
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = structlog.get_logger(__name__)

        # Webhook-konfigurationer
        self.webhooks: List[WebhookConfig] = []

        # Event handlers
        self.event_handlers: Dict[WebhookEvent, List[Callable]] = {}

        # Sending task
        self.sending_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Event queue
        self.event_queue: asyncio.Queue = asyncio.Queue()

        # Ladda webhooks från konfiguration
        self._load_webhooks()

    def _load_webhooks(self):
        """Laddar webhook-konfigurationer"""
        webhook_configs = self.config.get("webhooks", [])

        for webhook_data in webhook_configs:
            if isinstance(webhook_data, dict):
                events = [WebhookEvent(event) for event in webhook_data.get("events", [])]

                webhook_config = WebhookConfig(
                    url=webhook_data.get("url"),
                    events=events,
                    headers=webhook_data.get("headers"),
                    timeout=webhook_data.get("timeout", 30.0),
                    retry_count=webhook_data.get("retry_count", 3),
                    retry_delay=webhook_data.get("retry_delay", 5.0),
                    secret=webhook_data.get("secret"),
                )

                self.webhooks.append(webhook_config)

        self.logger.info(f"Loaded {len(self.webhooks)} webhook configurations")

    async def start(self):
        """Startar webhook-manager"""
        self.is_running = True
        self.sending_task = asyncio.create_task(self._sending_loop())
        self.logger.info("Webhook manager started")

    async def stop(self):
        """Stoppar webhook-manager"""
        self.is_running = False

        if self.sending_task:
            self.sending_task.cancel()
            try:
                await self.sending_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Webhook manager stopped")

    async def send_event(self, event: WebhookEvent, data: Dict[str, Any]):
        """Skickar en händelse till alla registrerade webhooks"""
        payload = WebhookPayload(event=event, timestamp=time.time(), data=data)

        await self.event_queue.put(payload)

        # Anropa lokala event handlers
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(payload)
                    else:
                        handler(payload)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event}: {str(e)}")

    def add_event_handler(self, event: WebhookEvent, handler: Callable):
        """Lägger till en lokal event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []

        self.event_handlers[event].append(handler)
        self.logger.info(f"Added event handler for {event}")

    def remove_event_handler(self, event: WebhookEvent, handler: Callable):
        """Tar bort en lokal event handler"""
        if event in self.event_handlers and handler in self.event_handlers[event]:
            self.event_handlers[event].remove(handler)
            self.logger.info(f"Removed event handler for {event}")

    async def _sending_loop(self):
        """Loop för att skicka webhook-händelser"""
        while self.is_running:
            try:
                # Vänta på händelser
                payload = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                # Skicka till alla relevanta webhooks
                await self._send_to_webhooks(payload)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in webhook sending loop: {str(e)}")

    async def _send_to_webhooks(self, payload: WebhookPayload):
        """Skickar payload till alla relevanta webhooks"""
        tasks = []

        for webhook in self.webhooks:
            if not webhook.is_active:
                continue

            if payload.event in webhook.events:
                task = asyncio.create_task(self._send_webhook(webhook, payload))
                tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_webhook(self, webhook: WebhookConfig, payload: WebhookPayload):
        """Skickar en webhook med retry-logik"""
        payload_dict = payload.to_dict()

        # Lägg till signature om secret finns
        if webhook.secret:
            import hmac
            import hashlib

            payload_str = json.dumps(payload_dict, sort_keys=True)
            signature = hmac.new(webhook.secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()

            if webhook.headers is None:
                webhook.headers = {}
            webhook.headers["X-Webhook-Signature"] = f"sha256={signature}"

        for attempt in range(webhook.retry_count + 1):
            try:
                await self._make_webhook_request(webhook, payload_dict)
                self.logger.debug(f"Webhook sent successfully to {webhook.url}")
                return

            except Exception as e:
                self.logger.warning(f"Webhook attempt {attempt + 1} failed for {webhook.url}: {str(e)}")

                if attempt < webhook.retry_count:
                    await asyncio.sleep(webhook.retry_delay)
                else:
                    self.logger.error(f"Webhook failed after {webhook.retry_count} attempts: {webhook.url}")

    async def _make_webhook_request(self, webhook: WebhookConfig, payload: Dict[str, Any]):
        """Gör HTTP-request till webhook"""
        import aiohttp

        headers = {"Content-Type": "application/json", "User-Agent": "WebScrapingToolkit/1.0"}

        if webhook.headers:
            headers.update(webhook.headers)

        timeout = aiohttp.ClientTimeout(total=webhook.timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(webhook.url, json=payload, headers=headers) as response:
                if response.status >= 400:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")

    def add_webhook(self, webhook_config: WebhookConfig):
        """Lägger till en ny webhook"""
        self.webhooks.append(webhook_config)
        self.logger.info(f"Added webhook: {webhook_config.url}")

    def remove_webhook(self, url: str):
        """Tar bort en webhook"""
        self.webhooks = [w for w in self.webhooks if w.url != url]
        self.logger.info(f"Removed webhook: {url}")

    def get_webhooks(self) -> List[Dict[str, Any]]:
        """Returnerar alla webhook-konfigurationer"""
        return [webhook.to_dict() for webhook in self.webhooks]

    def enable_webhook(self, url: str):
        """Aktiverar en webhook"""
        for webhook in self.webhooks:
            if webhook.url == url:
                webhook.is_active = True
                self.logger.info(f"Enabled webhook: {url}")
                break

    def disable_webhook(self, url: str):
        """Inaktiverar en webhook"""
        for webhook in self.webhooks:
            if webhook.url == url:
                webhook.is_active = False
                self.logger.info(f"Disabled webhook: {url}")
                break

    async def test_webhook(self, url: str) -> bool:
        """Testar en webhook-URL"""
        try:
            test_payload = WebhookPayload(
                event=WebhookEvent.SCRAPING_STARTED,
                timestamp=time.time(),
                data={"test": True, "message": "Webhook test"},
            )

            webhook_config = WebhookConfig(url=url, events=[WebhookEvent.SCRAPING_STARTED], timeout=10.0, retry_count=0)

            await self._send_webhook(webhook_config, test_payload)
            return True

        except Exception as e:
            self.logger.error(f"Webhook test failed for {url}: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Returnerar statistik för webhooks"""
        total_webhooks = len(self.webhooks)
        active_webhooks = len([w for w in self.webhooks if w.is_active])

        event_counts = {}
        for webhook in self.webhooks:
            for event in webhook.events:
                event_counts[event.value] = event_counts.get(event.value, 0) + 1

        return {
            "total_webhooks": total_webhooks,
            "active_webhooks": active_webhooks,
            "event_distribution": event_counts,
            "queue_size": self.event_queue.qsize(),
        }


# Convenience functions för vanliga händelser
async def notify_task_started(webhook_manager: WebhookManager, task_id: str, url: str):
    """Notifierar om att en uppgift har startat"""
    await webhook_manager.send_event(
        WebhookEvent.TASK_STARTED, {"task_id": task_id, "url": url, "timestamp": time.time()}
    )


async def notify_task_completed(webhook_manager: WebhookManager, task_id: str, url: str, result: Dict[str, Any]):
    """Notifierar om att en uppgift har slutförts"""
    await webhook_manager.send_event(
        WebhookEvent.TASK_COMPLETED, {"task_id": task_id, "url": url, "result": result, "timestamp": time.time()}
    )


async def notify_task_failed(webhook_manager: WebhookManager, task_id: str, url: str, error: str):
    """Notifierar om att en uppgift har misslyckats"""
    await webhook_manager.send_event(
        WebhookEvent.TASK_FAILED, {"task_id": task_id, "url": url, "error": error, "timestamp": time.time()}
    )


async def notify_rate_limit_hit(webhook_manager: WebhookManager, url: str, delay: float):
    """Notifierar om rate limiting"""
    await webhook_manager.send_event(
        WebhookEvent.RATE_LIMIT_HIT, {"url": url, "delay": delay, "timestamp": time.time()}
    )


async def notify_proxy_failed(webhook_manager: WebhookManager, proxy_url: str, error: str):
    """Notifierar om proxy-fel"""
    await webhook_manager.send_event(
        WebhookEvent.PROXY_FAILED, {"proxy_url": proxy_url, "error": error, "timestamp": time.time()}
    )
