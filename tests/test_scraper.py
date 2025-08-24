import pytest
import tempfile
import os
import sys

# Lägg till projektets root i Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ULTIMATE_MAGNIFICENT_SCRAPER import UltimateMagnificentScraper, MagnificentAI, MagnificentDatabase, ScrapingMode


class TestUltimateMagnificentScraper:
    """Testar Ultimate Magnificent Scraper"""

    def setup_method(self):
        """Setup för varje test"""
        self.scraper = UltimateMagnificentScraper()
        self.ai = MagnificentAI()

    def test_scraper_initialization(self):
        """Testar att scrapern initialiseras korrekt"""
        assert self.scraper is not None
        assert self.scraper.mode == ScrapingMode.MAGNIFICENT
        assert self.scraper.is_running == False

    def test_ai_initialization(self):
        """Testar att AI:n initialiseras korrekt"""
        assert self.ai is not None
        assert hasattr(self.ai, "vectorizer")
        assert hasattr(self.ai, "cluster_model")

    def test_add_url(self):
        """Testar att lägga till URL"""
        test_url = "example.com"
        self.scraper.add_url(test_url)
        assert not self.scraper.url_queue.empty()

    def test_ai_sentiment_analysis(self):
        """Testar AI sentiment-analys"""
        test_text = "Detta är en positiv text som borde ge bra sentiment!"
        result = self.ai.analyze_content_magnificently(test_text, "test.com", "<html>test</html>")

        assert "sentiment" in result
        assert "quality_score" in result
        assert "topics" in result

    def test_database_operations(self):
        """Testar databas-operationer"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db = MagnificentDatabase(tmp_db.name)

            # Testa att skapa tabeller
            db._create_tables()

            # Testa att spara och hämta data
            test_data = {
                "url": "test.com",
                "success": True,
                "data": {"text": "test"},
                "metadata": {"status": 200},
                "performance": {"time": 1.0},
                "ai_insights": {"sentiment": "positive"},
                "security_analysis": {"safe": True},
                "timestamp": "2024-01-01",
                "hash": "test_hash",
                "quality_score": 0.8,
            }

            db.save_magnificent_result(test_data)

            # Hämta statistik
            stats = db.get_stats()
            assert stats["total_requests"] >= 0

            # Rensa upp
            os.unlink(tmp_db.name)

    def test_scraping_modes(self):
        """Testar olika scraping-läge"""
        modes = [
            ScrapingMode.MAGNIFICENT,
            ScrapingMode.INTELLIGENT,
            ScrapingMode.AGGRESSIVE,
            ScrapingMode.STEALTH,
            ScrapingMode.AI_POWERED,
        ]

        for mode in modes:
            self.scraper.mode = mode
            assert self.scraper.mode == mode

    def test_headers_generation(self):
        """Testar header-generering"""
        headers = self.scraper._get_magnificent_headers()
        assert isinstance(headers, dict)
        assert "User-Agent" in headers

    def test_url_normalization(self):
        """Testar URL-normalisering"""
        test_urls = ["example.com", "http://example.com", "https://example.com"]

        for url in test_urls:
            normalized = self.scraper._normalize_url(url)
            assert normalized.startswith("https://")


if __name__ == "__main__":
    pytest.main([__file__])
