# Web Scraping Toolkit

Ett robust och skalbart verktyg för web scraping med fokus på etik, prestanda och underhållbarhet.

## 🎯 Funktioner

- **Asynkron scraping** för hög prestanda
- **Automatisk retry-logik** med exponential backoff
- **Rate limiting** för att respektera servrar
- **Flexibel konfiguration** via YAML/JSON
- **Strukturerad loggning** för debugging
- **Data-validering** och export
- **Proxy-stöd** för IP-rotation
- **JavaScript-rendering** med Playwright/Selenium

## 🚀 Snabbstart

### Installation

```bash
# Klona repository
git clone <repository-url>
cd scraping

# Installera dependencies
pip install -r requirements.txt

# Installera Playwright browsers
playwright install
```

### Grundläggande användning

```python
from scraper import WebScraper

# Skapa scraper-instans
scraper = WebScraper(config_path="config.yaml")

# Skrapa en sida
data = await scraper.scrape_url("https://example.com")

# Exportera data
scraper.export_data(data, format="json")
```

## 📁 Projektstruktur

```
scraping/
├── src/
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── core.py          # Huvudscraper-klass
│   │   ├── parsers.py       # HTML-parsers
│   │   ├── validators.py    # Data-validering
│   │   └── exporters.py     # Data-export
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py        # Konfigurationshantering
│   │   ├── logging.py       # Loggning
│   │   └── helpers.py       # Hjälpfunktioner
│   └── tests/
│       ├── __init__.py
│       ├── test_scraper.py
│       └── test_parsers.py
├── config/
│   ├── default.yaml         # Standardkonfiguration
│   └── examples/
├── data/                    # Skrapad data
├── logs/                    # Loggfiler
├── requirements.txt
└── README.md
```

## ⚙️ Konfiguration

Skapa en `config.yaml`-fil:

```yaml
scraper:
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  timeout: 30
  max_retries: 3
  delay_between_requests: 1.0
  
rate_limiting:
  requests_per_minute: 60
  burst_size: 10
  
logging:
  level: "INFO"
  format: "json"
  
export:
  default_format: "json"
  output_dir: "./data"
```

## 🧪 Testning

```bash
# Kör alla tester
pytest

# Kör med coverage
pytest --cov=src

# Kör specifika tester
pytest tests/test_scraper.py
```

## 📊 Övervakning

Verktyget inkluderar inbyggd övervakning:
- Request/response-tider
- Success/failure rates
- Data-volym per session
- Minnesanvändning

## 🔒 Säkerhet och Etik

- Respekterar robots.txt
- Implementerar rate limiting
- Roterar User-Agent headers
- Stöd för proxy-användning
- Loggar alla aktiviteter för granskning

## 🤝 Bidrag

1. Fork repository
2. Skapa feature branch
3. Commit ändringar
4. Push till branch
5. Skapa Pull Request

## 📄 Licens

MIT License - se LICENSE-fil för detaljer.
