# 🚀 Snabbstart - Web Scraping Toolkit

## Installation

### 1. Klona och installera dependencies
```bash
# Navigera till projektmappen
cd scraping

# Installera Python-dependencies
pip install -r requirements.txt

# Installera Playwright browsers (valfritt, för JavaScript-rendering)
playwright install
```

### 2. Verifiera installation
```bash
# Testa att allt fungerar
python -c "from src.scraper import WebScraper; print('✅ Installation lyckades!')"
```

## Snabbstart-exempel

### Exempel 1: Skrapa en enskild sida
```python
import asyncio
from src.scraper import WebScraper

async def main():
    async with WebScraper() as scraper:
        result = await scraper.scrape_url("https://httpbin.org/html")
        
        if result.success:
            print(f"✅ Titel: {result.data.get('title', 'N/A')}")
            print(f"⏱️  Response-tid: {result.response_time:.2f}s")
            
            # Exportera data
            scraper.export_data(result, "json", "data/första_scraping.json")
        else:
            print(f"❌ Fel: {result.error}")

asyncio.run(main())
```

### Exempel 2: Batch-scraping av flera sidor
```python
import asyncio
from src.scraper import WebScraper

async def main():
    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/xml"
    ]
    
    async with WebScraper() as scraper:
        results = await scraper.scrape_multiple(urls)
        
        successful = [r for r in results if r.success]
        print(f"✅ Framgångsrika: {len(successful)}/{len(urls)}")
        
        # Exportera alla resultat
        scraper.export_data(results, "json", "data/batch_resultat.json")

asyncio.run(main())
```

### Exempel 3: Använd CLI-verktyget
```bash
# Skrapa enskild URL
python cli.py scrape https://httpbin.org/html --format json

# Skrapa flera URLs från fil
echo "https://httpbin.org/html" > urls.txt
echo "https://httpbin.org/json" >> urls.txt
python cli.py batch urls.txt --format csv

# Visa konfiguration
python cli.py config --show
```

## Konfiguration

### Skapa anpassad konfiguration
```bash
# Skapa exempelkonfiguration
python cli.py config --create

# Redigera config/config/my_config.yaml
# Använd din konfiguration
python cli.py scrape https://example.com --config config/my_config.yaml
```

### Viktiga konfigurationsinställningar
```yaml
scraper:
  timeout: 30                    # Timeout i sekunder
  delay_between_requests: 1.0    # Paus mellan requests
  use_playwright: false          # Aktivera för JavaScript-sidor

rate_limiting:
  requests_per_minute: 60        # Max requests per minut
  max_concurrent: 10             # Samtidiga requests

logging:
  level: "INFO"                  # DEBUG, INFO, WARNING, ERROR
  format: "json"                 # json eller console
```

## Vanliga användningsfall

### 1. Skrapa produktdata
```python
from src.scraper import WebScraper
from src.scraper.parsers import HTMLParser

async def scrape_products():
    async with WebScraper() as scraper:
        # Använd anpassade CSS-selektorer
        selectors = {
            "title": ".product-title",
            "price": ".product-price",
            "description": ".product-description"
        }
        
        result = await scraper.scrape_url("https://example-shop.com/product")
        
        if result.success:
            # Använd HTMLParser för anpassad extraktion
            parser = HTMLParser()
            custom_data = parser.parse(result.data.get('raw_html', ''), selectors)
            
            print(f"Produkt: {custom_data.get('title')}")
            print(f"Pris: {custom_data.get('price')}")
```

### 2. Validera skrapad data
```python
from src.scraper.validators import DataValidator

# Validera data
validator = DataValidator()
validated_data = validator.validate({
    "title": "Produktnamn",
    "email": "kontakt@företag.se",
    "price": "299.99"
})

# Kontrollera valideringsresultat
validation = validated_data.get('_validation', {})
print(f"Giltig data: {validation.get('overall_valid')}")
```

### 3. Exportera till olika format
```python
from src.scraper.exporters import DataExporter

exporter = DataExporter()

# Exportera till JSON
exporter.export(data, "json", "data/produkter.json")

# Exportera till CSV
exporter.export(data, "csv", "data/produkter.csv")

# Exportera till Excel
exporter.export(data, "excel", "data/produkter.xlsx")
```

## Felsökning

### Vanliga problem och lösningar

**Problem: "ModuleNotFoundError: No module named 'src'"**
```bash
# Lösning: Lägg till src i Python-sökvägen
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**Problem: "Playwright not installed"**
```bash
# Lösning: Installera Playwright browsers
playwright install
```

**Problem: "Rate limiting too aggressive"**
```yaml
# Lösning: Justera rate limiting i config
rate_limiting:
  requests_per_minute: 120  # Öka från 60
  delay_between_requests: 0.5  # Minska från 1.0
```

**Problem: "Timeout errors"**
```yaml
# Lösning: Öka timeout
scraper:
  timeout: 60  # Öka från 30
  connect_timeout: 20  # Öka från 10
```

## Nästa steg

1. **Läs dokumentationen**: Se `README.md` för detaljerad information
2. **Kör testerna**: `pytest src/tests/` för att verifiera funktionalitet
3. **Utforska exempel**: Se `example_usage.py` för fler användningsexempel
4. **Anpassa konfiguration**: Skapa din egen config-fil för dina behov
5. **Utöka funktionalitet**: Lägg till anpassade parsers eller validators

## Support

- **Dokumentation**: `README.md` och `PROJECT_SUMMARY.md`
- **Exempel**: `example_usage.py`
- **Tester**: `src/tests/test_scraper.py`
- **CLI-hjälp**: `python cli.py --help`

---

🎉 **Grattis!** Du är nu redo att börja med etisk och effektiv web scraping!
