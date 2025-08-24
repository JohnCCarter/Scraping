"""
Avancerat exempel på Web Scraping Toolkit med alla nya funktioner
"""

import asyncio
import json
import time
from typing import List, Dict, Any

from src.utils.config import Config
from src.scraper.core import WebScraper
from src.scraper.robots_parser import AdvancedRobotsParser
from src.scraper.proxy_manager import ProxyManager
from src.scraper.distributed import DistributedScraper
from src.scraper.webhooks import WebhookManager, WebhookEvent
from src.scraper.plugins import PluginManager
from src.scraper.cache import CacheManager
from src.dashboard.app import DashboardApp


async def advanced_scraping_example():
    """Exempel på avancerad scraping med alla nya funktioner"""

    print("🚀 Startar avancerat Web Scraping Toolkit...")

    # Ladda avancerad konfiguration
    config = Config("config/advanced.yaml")

    # Initiera alla komponenter
    robots_parser = AdvancedRobotsParser(config)
    proxy_manager = ProxyManager(config)
    webhook_manager = WebhookManager(config)
    plugin_manager = PluginManager(config)
    cache_manager = CacheManager(config)

    # Starta komponenter
    await proxy_manager.start()
    await webhook_manager.start()
    await cache_manager.start()

    # Skapa dashboard
    dashboard = DashboardApp(config)
    dashboard.set_components(
        scraper=None,  # Sätts senare
        proxy_manager=proxy_manager,
        webhook_manager=webhook_manager,
    )

    print("✅ Alla komponenter startade")

    # Exempel 1: Grundläggande scraping med robots.txt och caching
    print("\n📄 Exempel 1: Grundläggande scraping med avancerade funktioner")

    async with WebScraper(config) as scraper:
        # Sätt scraper i dashboard
        dashboard.set_components(scraper=scraper)

        # Kontrollera robots.txt
        url = "https://httpbin.org/html"
        can_fetch, crawl_delay = await robots_parser.can_fetch(url)

        if can_fetch:
            print(f"✅ URL tillåten enligt robots.txt (crawl_delay: {crawl_delay})")

            # Hämta proxy
            proxy = await proxy_manager.get_proxy()
            if proxy:
                print(f"🌐 Använder proxy: {proxy.url}")

            # Skapa cache-nyckel
            cache_key = cache_manager.generate_cache_key(url)

            # Kontrollera cache först
            cached_data = await cache_manager.get(cache_key)
            if cached_data:
                print("📦 Data hittad i cache")
                result = cached_data
            else:
                print("🌐 Hämtar data från webben...")

                # Skicka webhook-notifiering
                await webhook_manager.send_event(
                    WebhookEvent.SCRAPING_STARTED,
                    {"url": url, "timestamp": time.time()},
                )

                # Utför scraping
                result = await scraper.scrape_url(url)

                # Spara i cache
                await cache_manager.set(cache_key, result, ttl=3600)

                # Skicka webhook-notifiering
                await webhook_manager.send_event(
                    WebhookEvent.SCRAPING_COMPLETED,
                    {"url": url, "success": result.success, "timestamp": time.time()},
                )

            print(f"📊 Resultat: {result.success}")
            if result.data:
                print(f"📝 Titel: {result.data.get('title', 'N/A')}")

        else:
            print("❌ URL blockerad enligt robots.txt")

    # Exempel 2: Distribuerad scraping med Redis
    print("\n🔄 Exempel 2: Distribuerad scraping med Redis")

    try:
        async with DistributedScraper(config) as distributed_scraper:
            # Lägg till uppgifter i kön
            urls = [
                "https://httpbin.org/html",
                "https://httpbin.org/json",
                "https://httpbin.org/xml",
            ]

            task_ids = []
            for url in urls:
                task_id = await distributed_scraper.add_task(url)
                task_ids.append(task_id)
                print(f"📋 Lade till uppgift {task_id} för {url}")

            # Starta worker
            worker_task = asyncio.create_task(distributed_scraper.start_worker())

            # Vänta på resultat
            print("⏳ Väntar på att uppgifter ska slutföras...")
            for task_id in task_ids:
                result = await distributed_scraper.wait_for_task(task_id, timeout=60)
                if result:
                    print(f"✅ Uppgift {task_id} slutförd: {result['status']}")
                else:
                    print(f"❌ Uppgift {task_id} timeout")

            # Stoppa worker
            worker_task.cancel()

            # Hämta statistik
            stats = await distributed_scraper.get_queue_stats()
            print(f"📊 Queue-statistik: {stats}")

    except Exception as e:
        print(f"⚠️ Redis inte tillgängligt: {e}")
        print("💡 Starta Redis med: redis-server")

    # Exempel 3: Plugin-system
    print("\n🔌 Exempel 3: Plugin-system")

    # Lista tillgängliga plugins
    plugins = plugin_manager.list_plugins()
    print(f"📦 Tillgängliga plugins: {len(plugins)}")

    for plugin in plugins:
        print(f"  - {plugin['name']} ({plugin['type']}): {plugin['description']}")

    # Använd news parser plugin
    news_parser = plugin_manager.get_plugin("news_parser")
    if news_parser:
        print("📰 Testar news parser plugin...")

        # Simulera nyhetsartikel
        test_html = """
        <html>
            <head><title>Breaking News: Important Event</title></head>
            <body>
                <h1>Breaking News: Important Event</h1>
                <div class="author">By John Doe</div>
                <div class="published-date">2024-01-15</div>
                <div class="article-content">
                    <p>This is the main content of the article...</p>
                </div>
                <div class="summary">A brief summary of the article</div>
                <div class="tags">
                    <a href="#">news</a>
                    <a href="#">breaking</a>
                </div>
            </body>
        </html>
        """

        parsed_data = await news_parser.parse(test_html, "https://news.example.com/article")
        print(f"📝 Parsad artikel: {parsed_data['title']}")
        print(f"👤 Författare: {parsed_data['author']}")
        print(f"🏷️ Taggar: {parsed_data['tags']}")

    # Exempel 4: Webhook-notifieringar
    print("\n🔔 Exempel 4: Webhook-notifieringar")

    # Skicka test-notifieringar
    test_events = [
        (
            WebhookEvent.TASK_STARTED,
            {"task_id": "test-123", "url": "https://example.com"},
        ),
        (WebhookEvent.RATE_LIMIT_HIT, {"url": "https://example.com", "delay": 5.0}),
        (
            WebhookEvent.PROXY_FAILED,
            {"proxy_url": "http://proxy.example.com", "error": "Connection timeout"},
        ),
    ]

    for event, data in test_events:
        await webhook_manager.send_event(event, data)
        print(f"📤 Skickade {event.value}: {data}")

    # Exempel 5: Cache-statistik
    print("\n💾 Exempel 5: Cache-statistik")

    cache_stats = cache_manager.get_stats()
    print(f"📊 Cache-strategi: {cache_stats['strategy']}")

    for layer_name, layer_stats in cache_stats["layers"].items():
        print(f"  {layer_name}: {layer_stats['total_entries']} poster, " f"{layer_stats['total_size_bytes']} bytes")

    # Exempel 6: Proxy-statistik
    print("\n🌐 Exempel 6: Proxy-statistik")

    proxy_stats = proxy_manager.get_stats()
    print(f"📊 Proxy-statistik: {proxy_stats}")

    # Visa detaljerad proxy-information
    proxy_details = proxy_manager.get_proxy_details()
    for proxy in proxy_details:
        print(
            f"  {proxy['url']}: "
            f"aktiv={proxy['is_active']}, "
            f"framgångsgrad={proxy['success_rate']:.2%}, "
            f"hälsopoäng={proxy['health_score']:.2f}"
        )

    # Exempel 7: Batch-scraping med validering
    print("\n📋 Exempel 7: Batch-scraping med validering")

    urls_to_scrape = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/xml",
    ]

    results = []
    async with WebScraper(config) as scraper:
        for url in urls_to_scrape:
            print(f"🌐 Skrapar {url}...")

            # Kontrollera robots.txt
            can_fetch, _ = await robots_parser.can_fetch(url)
            if not can_fetch:
                print(f"❌ {url} blockerad av robots.txt")
                continue

            # Utför scraping
            result = await scraper.scrape_url(url)
            results.append(result)

            # Validera data med email validator plugin
            email_validator = plugin_manager.get_plugin("email_validator")
            if email_validator and result.data:
                validation_result = await email_validator.validate(result.data)
                if validation_result["is_valid"]:
                    print(f"✅ Data validerad för {url}")
                else:
                    print(f"⚠️ Valideringsfel för {url}: {validation_result['errors']}")

            # Rate limiting
            await asyncio.sleep(1)

    print(f"📊 Batch-scraping slutförd: {len(results)} resultat")

    # Exempel 8: Dashboard
    print("\n📊 Exempel 8: Dashboard")

    # Starta dashboard i bakgrunden
    dashboard_task = asyncio.create_task(dashboard.start_background())

    print("🌐 Dashboard startat på http://localhost:8080")
    print("📱 Öppna webbläsaren för att se real-time metrics")

    # Vänta lite så användaren kan titta på dashboard
    await asyncio.sleep(10)

    # Stoppa dashboard
    dashboard_task.cancel()

    # Stoppa alla komponenter
    print("\n🛑 Stoppar alla komponenter...")

    await proxy_manager.stop()
    await webhook_manager.stop()
    await cache_manager.stop()

    print("✅ Alla komponenter stoppade")

    # Visa slutstatistik
    print("\n📈 Slutstatistik:")

    final_stats = {
        "robots_cache": robots_parser.get_cache_stats(),
        "proxy": proxy_manager.get_stats(),
        "webhook": webhook_manager.get_stats(),
        "plugin": plugin_manager.get_plugin_stats(),
        "cache": cache_manager.get_stats(),
    }

    for component, stats in final_stats.items():
        print(f"  {component}: {stats}")


async def machine_learning_example():
    """Exempel på machine learning-funktioner (valfritt)"""

    print("\n🤖 Exempel på Machine Learning-funktioner")

    # Detta skulle implementeras med scikit-learn
    # för automatisk selektor-generering och innehållsklassificering

    print("💡 Machine learning-funktioner kräver:")
    print("  - scikit-learn för modellträning")
    print("  - Träningsdata för selektor-generering")
    print("  - Modeller för innehållsklassificering")
    print("  - Konfiguration i config/advanced.yaml")


def main():
    """Huvudfunktion"""
    print("🎯 Avancerat Web Scraping Toolkit - Komplett exempel")
    print("=" * 60)

    # Kör huvudexemplet
    asyncio.run(advanced_scraping_example())

    # Kör ML-exemplet (valfritt)
    asyncio.run(machine_learning_example())

    print("\n🎉 Exempel slutfört!")
    print("\n💡 Tips för produktion:")
    print("  - Konfigurera Redis för distribuerad scraping")
    print("  - Sätt upp webhooks för notifieringar")
    print("  - Konfigurera proxy-servrar")
    print("  - Anpassa cache-strategier")
    print("  - Implementera monitoring och alerting")
    print("  - Följ GDPR och andra compliance-krav")


if __name__ == "__main__":
    main()
