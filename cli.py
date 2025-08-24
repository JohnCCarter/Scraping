#!/usr/bin/env python3
"""
CLI för Web Scraping Toolkit

Användning:
    python cli.py scrape <url> [options]
    python cli.py batch <urls_file> [options]
    python cli.py config [options]
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Lägg till src i Python-sökvägen
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scraper import WebScraper
from utils.config import Config
from utils.logging import setup_logger


async def scrape_single_url(url: str, config_path: Optional[str], output_format: str, output_path: Optional[str]):
    """Skrapar en enskild URL"""
    print(f"🔍 Skrapar: {url}")

    async with WebScraper(config_path) as scraper:
        result = await scraper.scrape_url(url)

        if result.success:
            print(f"✅ Framgångsrikt skrapat!")
            print(f"   Response-tid: {result.response_time:.2f}s")
            print(f"   Data-fält: {len(result.data)}")

            # Exportera data
            if not output_path:
                output_path = f"data/scraped_{int(result.response_time)}.{output_format}"

            scraper.export_data(result, output_format, output_path)
            print(f"📁 Data exporterad till: {output_path}")

        else:
            print(f"❌ Fel vid scraping: {result.error}")
            sys.exit(1)


async def scrape_multiple_urls(
    urls: List[str],
    config_path: Optional[str],
    output_format: str,
    output_path: Optional[str],
):
    """Skrapar flera URLs"""
    print(f"🔍 Skrapar {len(urls)} URLs...")

    async with WebScraper(config_path) as scraper:
        results = await scraper.scrape_multiple(urls)

        # Analysera resultat
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        print(f"✅ Framgångsrika: {len(successful)}")
        print(f"❌ Misslyckade: {len(failed)}")

        if failed:
            print("\nMisslyckade URLs:")
            for result in failed:
                print(f"  - {result.url}: {result.error}")

        # Exportera data
        if not output_path:
            output_path = f"data/batch_scraped_{len(urls)}.{output_format}"

        scraper.export_data(results, output_format, output_path)
        print(f"📁 Data exporterad till: {output_path}")


def load_urls_from_file(file_path: str) -> List[str]:
    """Laddar URLs från fil"""
    urls = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
        return urls
    except Exception as e:
        print(f"❌ Fel vid läsning av URL-fil: {str(e)}")
        sys.exit(1)


def show_config_info(config_path: Optional[str]):
    """Visar konfigurationsinformation"""
    try:
        config = Config(config_path)

        print("⚙️  Konfigurationsinformation:")
        print(f"   Timeout: {config.get('scraper.timeout')}s")
        print(f"   Max retries: {config.get('scraper.max_retries')}")
        print(f"   Rate limit: {config.get('rate_limiting.requests_per_minute')} requests/min")
        print(f"   Concurrent: {config.get('rate_limiting.max_concurrent')}")
        print(f"   Use Playwright: {config.get('scraper.use_playwright')}")

        # Visa User-Agent
        user_agent = config.get("scraper.user_agent")
        if user_agent:
            print(f"   User-Agent: {user_agent[:50]}...")

    except Exception as e:
        print(f"❌ Fel vid läsning av konfiguration: {str(e)}")
        sys.exit(1)


def create_sample_config():
    """Skapar en exempelkonfigurationsfil"""
    config_path = "config/my_config.yaml"

    try:
        config = Config()
        config.save(config_path)
        print(f"✅ Exempelkonfiguration skapad: {config_path}")
        print("   Redigera filen för att anpassa inställningar")

    except Exception as e:
        print(f"❌ Fel vid skapande av konfiguration: {str(e)}")
        sys.exit(1)


def main():
    """Huvudfunktion för CLI"""
    parser = argparse.ArgumentParser(
        description="Web Scraping Toolkit - Kommandoradsverktyg",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exempel:
  python cli.py scrape https://example.com
  python cli.py scrape https://example.com --format csv --output data.csv
  python cli.py batch urls.txt --config my_config.yaml
  python cli.py config --show
  python cli.py config --create
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Tillgängliga kommandon")

    # Scrape-kommando
    scrape_parser = subparsers.add_parser("scrape", help="Skrapa en enskild URL")
    scrape_parser.add_argument("url", help="URL att skrapa")
    scrape_parser.add_argument("--config", "-c", help="Sökväg till konfigurationsfil")
    scrape_parser.add_argument(
        "--format",
        "-f",
        default="json",
        choices=["json", "csv", "excel", "xml"],
        help="Export-format (standard: json)",
    )
    scrape_parser.add_argument("--output", "-o", help="Sökväg för output-fil")

    # Batch-kommando
    batch_parser = subparsers.add_parser("batch", help="Skrapa flera URLs")
    batch_parser.add_argument("urls_file", help="Fil med URLs (en per rad)")
    batch_parser.add_argument("--config", "-c", help="Sökväg till konfigurationsfil")
    batch_parser.add_argument(
        "--format",
        "-f",
        default="json",
        choices=["json", "csv", "excel", "xml"],
        help="Export-format (standard: json)",
    )
    batch_parser.add_argument("--output", "-o", help="Sökväg för output-fil")

    # Config-kommando
    config_parser = subparsers.add_parser("config", help="Hantera konfiguration")
    config_parser.add_argument("--show", "-s", action="store_true", help="Visa aktuell konfiguration")
    config_parser.add_argument("--create", action="store_true", help="Skapa exempelkonfiguration")
    config_parser.add_argument("--config", "-c", help="Sökväg till konfigurationsfil")

    # Globala argument
    parser.add_argument("--verbose", "-v", action="store_true", help="Visa detaljerad output")

    args = parser.parse_args()

    # Konfigurera loggning
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logger("cli", log_level=log_level)

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "scrape":
            asyncio.run(scrape_single_url(args.url, args.config, args.format, args.output))

        elif args.command == "batch":
            urls = load_urls_from_file(args.urls_file)
            if not urls:
                print("❌ Ingen URL hittades i filen")
                sys.exit(1)

            asyncio.run(scrape_multiple_urls(urls, args.config, args.format, args.output))

        elif args.command == "config":
            if args.create:
                create_sample_config()
            elif args.show:
                show_config_info(args.config)
            else:
                config_parser.print_help()

    except KeyboardInterrupt:
        print("\n⏹️  Avbruten av användaren")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Oväntat fel: {str(e)}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
