#!/usr/bin/env python3
"""
Exempel på användning av Web Scraping Toolkit

Detta exempel visar hur man använder verktyget för att skrapa data från webbplatser
på ett etiskt och effektivt sätt.
"""

import asyncio
import sys
from pathlib import Path

# Lägg till src i Python-sökvägen
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scraper import WebScraper
from utils.logging import get_scraping_logger


async def basic_scraping_example():
    """Grundläggande exempel på web scraping"""
    print("🚀 Startar grundläggande scraping-exempel...")

    # Skapa scraper-instans med standardkonfiguration
    async with WebScraper("config/default.yaml") as scraper:
        # Skrapa en enskild URL
        url = "https://httpbin.org/html"
        result = await scraper.scrape_url(url)

        if result.success:
            print(f"✅ Framgångsrikt skrapat: {url}")
            print(f"   Titel: {result.data.get('title', 'N/A')}")
            print(f"   Response-tid: {result.response_time:.2f}s")
        else:
            print(f"❌ Fel vid scraping: {result.error}")

        # Exportera data
        scraper.export_data(result, format="json", output_path="data/basic_example.json")


async def batch_scraping_example():
    """Exempel på batch-scraping av flera URLs"""
    print("\n📦 Startar batch-scraping exempel...")

    # Lista med URLs att skrapa
    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/xml",
    ]

    async with WebScraper("config/default.yaml") as scraper:
        # Skrapa flera URLs parallellt
        results = await scraper.scrape_multiple(urls)

        # Analysera resultat
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        print(f"✅ Framgångsrika requests: {len(successful)}")
        print(f"❌ Misslyckade requests: {len(failed)}")

        # Exportera alla resultat
        scraper.export_data(results, format="json", output_path="data/batch_example.json")


async def custom_parser_example():
    """Exempel med anpassad HTML-parsing"""
    print("\n🔧 Startar anpassad parser-exempel...")

    # Definiera CSS-selektorer för specifika element
    selectors = {
        "title": "title",
        "headings": "h1, h2, h3",
        "links": "a[href]",
        "images": "img[src]",
    }

    async with WebScraper("config/default.yaml") as scraper:
        url = "https://httpbin.org/html"
        result = await scraper.scrape_url(url)

        if result.success:
            # Använd anpassade selektorer
            from scraper.parsers import HTMLParser

            parser = HTMLParser()

            # Hämta rå HTML och parsa med selektorer
            # (I en riktig implementation skulle detta integreras i WebScraper)
            print(f"✅ Anpassad parsing av: {url}")
            print(f"   Data extraherad: {len(result.data)} fält")


async def data_validation_example():
    """Exempel på data-validering"""
    print("\n✅ Startar data-validering exempel...")

    from scraper.validators import DataValidator

    # Exempel-data att validera
    sample_data = {
        "title": "Exempel Titel",
        "email": "test@example.com",
        "phone": "123-456-7890",
        "url": "https://example.com",
        "price": "99.99",
        "description": "En beskrivning av produkten.",
    }

    # Validera data
    validator = DataValidator()
    validated_data = validator.validate(sample_data)

    # Visa valideringsresultat
    validation = validated_data.get("_validation", {})
    print(f"✅ Validering slutförd:")
    print(f"   Totalt fält: {validation.get('total_fields', 0)}")
    print(f"   Giltiga fält: {validation.get('valid_fields', 0)}")
    print(f"   Övergripande giltig: {validation.get('overall_valid', False)}")


async def export_formats_example():
    """Exempel på olika export-format"""
    print("\n📤 Startar export-format exempel...")

    from scraper.exporters import DataExporter

    # Exempel-data
    sample_data = [
        {"id": 1, "name": "Produkt A", "price": 99.99, "category": "Elektronik"},
        {"id": 2, "name": "Produkt B", "price": 149.99, "category": "Kläder"},
    ]

    exporter = DataExporter()

    # Exportera till olika format
    formats = ["json", "csv", "xml"]

    for format in formats:
        output_path = f"data/export_example.{format}"
        success = exporter.export(sample_data, format, output_path)

        if success:
            print(f"✅ Exporterat till {format.upper()}: {output_path}")
        else:
            print(f"❌ Fel vid export till {format.upper()}")


async def monitoring_example():
    """Exempel på övervakning och loggning"""
    print("\n📊 Startar övervakning-exempel...")

    # Skapa specialiserad logger
    logger = get_scraping_logger("monitoring_example")

    # Simulera en scraping-session
    session_id = "example_session_001"
    urls = ["https://httpbin.org/html", "https://httpbin.org/json"]

    logger.start_session(session_id, urls)

    async with WebScraper("config/default.yaml") as scraper:
        for url in urls:
            logger.log_request(url)
            result = await scraper.scrape_url(url)

            if result.success:
                logger.log_response(url, 200, result.response_time, True)
                logger.log_data_extracted(url, len(result.data), "html")
            else:
                logger.log_response(url, 0, result.response_time, False)
                logger.log_error(url, result.error, "scraping_error")

    logger.end_session(session_id)


async def main():
    """Huvudfunktion som kör alla exempel"""
    print("🎯 Web Scraping Toolkit - Användningsexempel")
    print("=" * 50)

    try:
        # Kör alla exempel
        await basic_scraping_example()
        await batch_scraping_example()
        await custom_parser_example()
        await data_validation_example()
        await export_formats_example()
        await monitoring_example()

        print("\n🎉 Alla exempel slutförda!")
        print("\n📁 Skapade filer:")
        print("   - data/basic_example.json")
        print("   - data/batch_example.json")
        print("   - data/export_example.json")
        print("   - data/export_example.csv")
        print("   - data/export_example.xml")
        print("   - logs/scraper.log")

    except Exception as e:
        print(f"\n❌ Fel i exempel: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Kör huvudfunktionen
    asyncio.run(main())
