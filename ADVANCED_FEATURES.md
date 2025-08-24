# 🚀 Avancerade Funktioner - Web Scraping Toolkit

## Översikt

Detta dokument beskriver alla nya avancerade funktioner som har lagts till i Web Scraping Toolkit för att skapa det mest kraftfulla och skalbara scraping-verktyget.

## 📋 Funktioner

### 1. 🤖 Avancerad Robots.txt-Parsing

**Fil:** `src/scraper/robots_parser.py`

**Funktioner:**
- Fullständig RFC 9309-kompatibilitet
- Intelligent cache-hantering
- Stöd för alla robots.txt-direktiv
- Automatisk crawl-delay och request-rate hantering
- Sitemap-extraktion

**Exempel:**
```python
from src.scraper.robots_parser import AdvancedRobotsParser

robots_parser = AdvancedRobotsParser(config)
can_fetch, crawl_delay = await robots_parser.can_fetch(url, user_agent)
```

### 2. 🌐 Proxy-Rotation med Health Checks

**Fil:** `src/scraper/proxy_manager.py`

**Funktioner:**
- Automatisk proxy-rotation
- Health checks med regelbundna tester
- Flera rotationsstrategier (round_robin, random, health_based, least_used)
- Proxy-prestandaövervakning
- Automatisk proxy-deaktivering vid fel

**Strategier:**
- `round_robin`: Systematisk rotation
- `random`: Slumpmässig val
- `health_based`: Baserat på hälsopoäng
- `least_used`: Minst använda proxy

### 3. 🔄 Distribuerad Scraping med Redis

**Fil:** `src/scraper/distributed.py`

**Funktioner:**
- Redis-baserad kö för uppgifter
- Prioriterad uppgiftshantering
- Worker-processer med heartbeat
- Automatisk retry-logik
- Real-time statusövervakning

**Användning:**
```python
from src.scraper.distributed import DistributedScraper

async with DistributedScraper(config) as scraper:
    task_id = await scraper.add_task(url, priority=1)
    result = await scraper.wait_for_task(task_id)
```

### 4. 🔔 Webhook-Stöd för Real-time Notifieringar

**Fil:** `src/scraper/webhooks.py`

**Funktioner:**
- Real-time händelsenotifieringar
- Stöd för flera webhook-endpoints
- Retry-logik med exponential backoff
- HMAC-signaturverifiering
- Event-driven arkitektur

**Händelsetyper:**
- `task_started`, `task_completed`, `task_failed`
- `scraping_started`, `scraping_completed`, `scraping_failed`
- `rate_limit_hit`, `proxy_failed`
- `worker_started`, `worker_stopped`

### 5. 📊 Web-baserat Dashboard

**Fil:** `src/dashboard/app.py`

**Funktioner:**
- Real-time metrics-visualisering
- WebSocket-baserade uppdateringar
- Interaktiva charts med Chart.js
- Responsiv design
- API-endpoints för statistik

**Features:**
- Live scraping-status
- Request/minut och success rate
- Proxy- och webhook-statistik
- Queue-storlek och worker-status

### 6. 🔌 Plugin-System

**Fil:** `src/scraper/plugins.py`

**Funktioner:**
- Modulärt plugin-system
- Automatisk plugin-upptäckt
- Hot-reloading av plugins
- Plugin-specifik konfiguration
- Inbyggda exempel-plugins

**Plugin-typer:**
- **Parsers:** Anpassade innehållsparsers
- **Validators:** Data-validering
- **Exporters:** Anpassade export-format

**Inbyggda plugins:**
- `NewsParser`: Specialiserad för nyhetssidor
- `EmailValidator`: E-postvalidering
- `JSONLExporter`: JSON Lines export

### 7. 💾 Caching-Lager

**Fil:** `src/scraper/cache.py`

**Funktioner:**
- Multi-lager caching (Memory, Disk, Redis)
- Hybrid cache-strategier
- TTL-hantering och expiration
- LRU-eviction policies
- Cache-statistik och monitoring

**Strategier:**
- `memory`: Snabb minne-baserad cache
- `disk`: Persistent disk-cache
- `redis`: Distribuerad Redis-cache
- `hybrid`: Kombination av lager

### 8. 🤖 Machine Learning (Förberedd)

**Planerade funktioner:**
- Automatisk selektor-generering
- Innehållsklassificering
- Anomaly detection
- Intelligent rate limiting

## 🛠️ Installation och Konfiguration

### 1. Installera Dependencies

```bash
pip install -r requirements.txt
```

### 2. Konfigurera Avancerade Funktioner

Kopiera `config/advanced.yaml` och anpassa:

```yaml
# Aktivera avancerade funktioner
robots:
  enabled: true

proxy:
  enabled: true
  rotation_strategy: "health_based"

redis:
  url: "redis://localhost:6379"

webhooks:
  - url: "https://your-webhook-url.com"
    events: ["task_completed", "task_failed"]

dashboard:
  host: "0.0.0.0"
  port: 8080

plugins:
  enabled: true

cache:
  strategy: "hybrid"
```

### 3. Starta Redis (för distribuerad scraping)

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
redis-server

# macOS
brew install redis
redis-server

# Windows
# Ladda ner Redis för Windows
```

## 📖 Användningsexempel

### Grundläggande Avancerad Scraping

```python
import asyncio
from src.utils.config import Config
from src.scraper.core import WebScraper
from src.scraper.robots_parser import AdvancedRobotsParser
from src.scraper.proxy_manager import ProxyManager
from src.scraper.cache import CacheManager

async def advanced_scraping():
    config = Config("config/advanced.yaml")
    
    # Initiera komponenter
    robots_parser = AdvancedRobotsParser(config)
    proxy_manager = ProxyManager(config)
    cache_manager = CacheManager(config)
    
    await proxy_manager.start()
    await cache_manager.start()
    
    async with WebScraper(config) as scraper:
        url = "https://example.com"
        
        # Kontrollera robots.txt
        can_fetch, delay = await robots_parser.can_fetch(url)
        if not can_fetch:
            return
        
        # Hämta proxy
        proxy = await proxy_manager.get_proxy()
        
        # Kontrollera cache
        cache_key = cache_manager.generate_cache_key(url)
        cached = await cache_manager.get(cache_key)
        
        if cached:
            result = cached
        else:
            result = await scraper.scrape_url(url)
            await cache_manager.set(cache_key, result, ttl=3600)
        
        print(f"Resultat: {result.success}")
    
    await proxy_manager.stop()
    await cache_manager.stop()

asyncio.run(advanced_scraping())
```

### Distribuerad Scraping

```python
async def distributed_scraping():
    config = Config("config/advanced.yaml")
    
    async with DistributedScraper(config) as scraper:
        # Lägg till uppgifter
        urls = ["https://example1.com", "https://example2.com"]
        task_ids = []
        
        for url in urls:
            task_id = await scraper.add_task(url, priority=1)
            task_ids.append(task_id)
        
        # Starta worker
        worker_task = asyncio.create_task(scraper.start_worker())
        
        # Vänta på resultat
        for task_id in task_ids:
            result = await scraper.wait_for_task(task_id)
            print(f"Uppgift {task_id}: {result['status']}")
        
        worker_task.cancel()
```

### Plugin-användning

```python
from src.scraper.plugins import PluginManager

async def use_plugins():
    config = Config("config/advanced.yaml")
    plugin_manager = PluginManager(config)
    
    # Lista plugins
    plugins = plugin_manager.list_plugins()
    print(f"Tillgängliga plugins: {len(plugins)}")
    
    # Använd news parser
    news_parser = plugin_manager.get_plugin("news_parser")
    if news_parser:
        parsed_data = await news_parser.parse(html_content, url)
        print(f"Titel: {parsed_data['title']}")
```

### Dashboard

```python
from src.dashboard.app import DashboardApp

async def start_dashboard():
    config = Config("config/advanced.yaml")
    dashboard = DashboardApp(config)
    
    # Sätt komponenter
    dashboard.set_components(
        scraper=scraper,
        proxy_manager=proxy_manager,
        webhook_manager=webhook_manager
    )
    
    # Starta dashboard
    await dashboard.start_background()
    
    print("Dashboard tillgängligt på http://localhost:8080")
```

## 🔧 Konfiguration

### Robots.txt

```yaml
robots:
  enabled: true
  cache_timeout: 3600
  respect_crawl_delay: true
  respect_request_rate: true
  user_agent: "WebScrapingToolkit/1.0"
```

### Proxy

```yaml
proxy:
  enabled: true
  rotation_strategy: "health_based"
  health_check_interval: 300
  max_failures: 5
  min_success_rate: 0.5
  
  proxy_list:
    - url: "http://proxy1.example.com:8080"
      username: "user"
      password: "pass"
```

### Webhooks

```yaml
webhooks:
  - url: "https://webhook.site/your-url"
    events:
      - "task_started"
      - "task_completed"
      - "task_failed"
    headers:
      Authorization: "Bearer token"
    secret: "your-secret"
```

### Cache

```yaml
cache:
  strategy: "hybrid"
  
  memory:
    max_size: 1000
    default_ttl: 3600
    max_memory_mb: 100
  
  disk:
    directory: "cache"
    max_size_mb: 1000
    default_ttl: 86400
```

### Plugins

```yaml
plugins:
  enabled: true
  directories:
    - "plugins"
    - "src/plugins"
    - "custom_plugins"
  
  news_parser:
    enabled: true
    news_domains:
      - "news.yahoo.com"
      - "bbc.com"
```

## 📊 Monitoring och Metrics

### Dashboard Metrics

- **Scraping Status**: Online/Offline
- **Requests/Minut**: Real-time throughput
- **Success Rate**: Framgångsgrad över tid
- **Active Proxies**: Antal aktiva proxies
- **Queue Size**: Antal väntande uppgifter
- **Active Webhooks**: Antal aktiva webhooks

### API Endpoints

- `GET /api/stats` - Allmän statistik
- `GET /api/scraping/stats` - Scraping-statistik
- `GET /api/proxy/stats` - Proxy-statistik
- `GET /api/webhook/stats` - Webhook-statistik
- `GET /api/distributed/stats` - Distribuerad statistik

### WebSocket Events

Real-time uppdateringar via WebSocket på `/ws`:
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    updateDashboard(data);
};
```

## 🔒 Säkerhet och Compliance

### GDPR-kompatibilitet

```yaml
compliance:
  gdpr:
    enabled: true
    data_retention_days: 90
    anonymize_personal_data: true
```

### Rate Limiting

```yaml
security:
  domain_rate_limits:
    default: 60  # requests per minute
    strict: 30   # för känsliga domäner
```

### Input Validation

```yaml
security:
  validate_urls: true
  max_url_length: 2048
  allowed_schemes: ["http", "https"]
```

## 🚀 Prestanda-optimering

### Connection Pooling

```yaml
performance:
  connection_pool_size: 100
  connection_timeout: 30
  keep_alive: true
```

### Concurrent Requests

```yaml
performance:
  max_concurrent_requests: 10
  semaphore_limit: 20
```

### Memory Management

```yaml
performance:
  max_memory_usage_mb: 512
  garbage_collection_interval: 300
```

## 🧪 Testing

### Enhetstester

```bash
pytest src/tests/ -v
```

### Integrationstester

```bash
pytest src/tests/test_integration.py -v
```

### Load Testing

```python
# Exempel på load test
async def load_test():
    config = Config("config/advanced.yaml")
    
    async with DistributedScraper(config) as scraper:
        # Lägg till 1000 uppgifter
        urls = [f"https://httpbin.org/html?i={i}" for i in range(1000)]
        
        for url in urls:
            await scraper.add_task(url)
        
        # Starta flera workers
        workers = []
        for _ in range(5):
            worker = asyncio.create_task(scraper.start_worker())
            workers.append(worker)
        
        # Vänta på slutförande
        await asyncio.gather(*workers, return_exceptions=True)
```

## 📈 Skalbarhet

### Vertikal Skalbarhet

- Öka `max_concurrent_requests`
- Öka `connection_pool_size`
- Öka `max_memory_usage_mb`

### Horisontell Skalbarhet

- Flera Redis-instanser
- Flera worker-processer
- Load balancer för dashboard

### Monitoring vid Skalning

- Prometheus metrics
- Grafana dashboards
- Alerting vid tröskelvärden

## 🔮 Framtida Funktioner

### Machine Learning

- Automatisk selektor-generering
- Innehållsklassificering
- Anomaly detection
- Intelligent rate limiting

### Avancerad Analytics

- Trend-analys
- Predictive analytics
- A/B testing för scraping-strategier

### Cloud Integration

- AWS Lambda support
- Kubernetes deployment
- Serverless scraping

## 📚 Resurser

### Dokumentation

- [README.md](README.md) - Grundläggande användning
- [QUICKSTART.md](QUICKSTART.md) - Snabbstart
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Projektöversikt

### Exempel

- [example_usage.py](example_usage.py) - Grundläggande exempel
- [advanced_example.py](advanced_example.py) - Avancerade exempel

### Konfiguration

- [config/default.yaml](config/default.yaml) - Standardkonfiguration
- [config/advanced.yaml](config/advanced.yaml) - Avancerad konfiguration

## 🤝 Bidrag

För att bidra till projektet:

1. Forka repository
2. Skapa feature branch
3. Implementera funktioner
4. Lägg till tester
5. Uppdatera dokumentation
6. Skicka pull request

## 📄 Licens

MIT License - se [LICENSE](LICENSE) för detaljer.

---

**Web Scraping Toolkit** - Det mest avancerade och skalbara scraping-verktyget för professionell användning.
