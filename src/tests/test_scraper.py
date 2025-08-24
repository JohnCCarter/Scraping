"""
Tester för WebScraper-klassen
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from pathlib import Path

# Lägg till src i Python-sökvägen
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from scraper.core import WebScraper, ScrapingResult
from scraper.parsers import HTMLParser, JSONParser
from scraper.validators import DataValidator
from scraper.exporters import DataExporter


class TestScrapingResult:
    """Tester för ScrapingResult-klassen"""

    def test_scraping_result_creation(self):
        """Testar skapande av ScrapingResult"""
        result = ScrapingResult(url="https://example.com", success=True, data={"title": "Test"}, response_time=1.5)

        assert result.url == "https://example.com"
        assert result.success is True
        assert result.data == {"title": "Test"}
        assert result.response_time == 1.5
        assert result.error is None

    def test_scraping_result_error(self):
        """Testar ScrapingResult med fel"""
        result = ScrapingResult(url="https://example.com", success=False, error="Connection failed", response_time=0.5)

        assert result.url == "https://example.com"
        assert result.success is False
        assert result.error == "Connection failed"
        assert result.data is None


class TestHTMLParser:
    """Tester för HTMLParser-klassen"""

    def setup_method(self):
        """Setup för varje test"""
        self.parser = HTMLParser()

    def test_parse_basic_html(self):
        """Testar grundläggande HTML-parsing"""
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Heading</h1>
                <p>Some text</p>
                <a href="https://example.com">Link</a>
            </body>
        </html>
        """

        result = self.parser.parse(html)

        assert result["title"] == "Test Page"
        assert "Main Heading" in result["h1_headings"]
        assert len(result["links"]) > 0
        assert result["links"][0]["url"] == "https://example.com"

    def test_parse_with_selectors(self):
        """Testar parsing med CSS-selektorer"""
        html = """
        <div class="product">
            <h2 class="title">Product Name</h2>
            <span class="price">$99.99</span>
        </div>
        """

        selectors = {"name": ".product .title", "price": ".product .price"}

        result = self.parser.parse(html, selectors)

        assert result["name"] == "Product Name"
        assert result["price"] == "$99.99"


class TestJSONParser:
    """Tester för JSONParser-klassen"""

    def setup_method(self):
        """Setup för varje test"""
        self.parser = JSONParser()

    def test_parse_valid_json(self):
        """Testar parsing av giltig JSON"""
        json_data = '{"name": "Test", "value": 123}'

        result = self.parser.parse(json_data)

        assert result["name"] == "Test"
        assert result["value"] == 123

    def test_parse_invalid_json(self):
        """Testar parsing av ogiltig JSON"""
        invalid_json = '{"name": "Test", "value": 123'  # Saknar }

        result = self.parser.parse(invalid_json)

        assert result == {}


class TestDataValidator:
    """Tester för DataValidator-klassen"""

    def setup_method(self):
        """Setup för varje test"""
        self.validator = DataValidator()

    def test_validate_valid_data(self):
        """Testar validering av giltig data"""
        data = {"title": "Test Title", "email": "test@example.com", "url": "https://example.com"}

        result = self.validator.validate(data)

        assert "_validation" in result
        assert result["_validation"]["overall_valid"] is True

    def test_validate_invalid_email(self):
        """Testar validering av ogiltig e-post"""
        data = {"email": "invalid-email"}

        result = self.validator.validate(data)

        assert result["_validation"]["overall_valid"] is False
        assert "email" in result["_validation"]["field_results"]

    def test_validate_empty_data(self):
        """Testar validering av tom data"""
        data = {}

        result = self.validator.validate(data)

        assert "_validation" in result
        assert result["_validation"]["total_fields"] == 0


class TestDataExporter:
    """Tester för DataExporter-klassen"""

    def setup_method(self):
        """Setup för varje test"""
        self.exporter = DataExporter()

    def test_export_json(self, tmp_path):
        """Testar JSON-export"""
        data = [{"name": "Test", "value": 123}]
        output_path = tmp_path / "test.json"

        success = self.exporter.export(data, "json", str(output_path))

        assert success is True
        assert output_path.exists()

    def test_export_csv(self, tmp_path):
        """Testar CSV-export"""
        data = [{"name": "Test", "value": 123}]
        output_path = tmp_path / "test.csv"

        success = self.exporter.export(data, "csv", str(output_path))

        assert success is True
        assert output_path.exists()

    def test_export_invalid_format(self, tmp_path):
        """Testar export med ogiltigt format"""
        data = [{"name": "Test"}]
        output_path = tmp_path / "test.xyz"

        success = self.exporter.export(data, "xyz", str(output_path))

        assert success is False


@pytest.mark.asyncio
class TestWebScraper:
    """Tester för WebScraper-klassen"""

    async def test_scraper_initialization(self):
        """Testar initiering av WebScraper"""
        scraper = WebScraper()

        assert scraper.config is not None
        assert scraper.html_parser is not None
        assert scraper.json_parser is not None
        assert scraper.validator is not None
        assert scraper.exporter is not None

    @patch("aiohttp.ClientSession.get")
    async def test_scrape_url_success(self, mock_get):
        """Testar framgångsrik URL-scraping"""
        # Mock response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = asyncio.coroutine(lambda: "<html><title>Test</title></html>")
        mock_get.return_value.__aenter__.return_value = mock_response

        async with WebScraper() as scraper:
            result = await scraper.scrape_url("https://example.com")

            assert result.success is True
            assert result.url == "https://example.com"
            assert result.data is not None

    @patch("aiohttp.ClientSession.get")
    async def test_scrape_url_failure(self, mock_get):
        """Testar misslyckad URL-scraping"""
        # Mock response med fel
        mock_response = Mock()
        mock_response.status = 404
        mock_response.reason = "Not Found"
        mock_get.return_value.__aenter__.return_value = mock_response

        async with WebScraper() as scraper:
            result = await scraper.scrape_url("https://example.com")

            assert result.success is False
            assert "404" in result.error

    async def test_scrape_multiple_urls(self):
        """Testar batch-scraping"""
        urls = ["https://example1.com", "https://example2.com"]

        async with WebScraper() as scraper:
            # Mock scrape_url-metoden
            scraper.scrape_url = Mock()
            scraper.scrape_url.return_value = ScrapingResult(
                url="https://example.com", success=True, data={"title": "Test"}
            )

            results = await scraper.scrape_multiple(urls)

            assert len(results) == 2
            assert all(r.success for r in results)


if __name__ == "__main__":
    pytest.main([__file__])
