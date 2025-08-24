"""
🤖 AI-DRIVEN INTELLIGENT SCRAPING MODULE
Revolutionär AI-integration för automatisk web scraping
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union
from abc import ABC, abstractmethod
import base64
import io
from pathlib import Path

import aiohttp
import openai
from PIL import Image
import cv2
import numpy as np
from bs4 import BeautifulSoup
import pytesseract
from transformers import pipeline
import torch

from ..utils.config import Config
from ..utils.logging import ScrapingLogger


class MockOpenAIClient:
    """Mock OpenAI-klient för demo-syfte"""

    class MockMessage:
        def __init__(self, content: str):
            self.content = content

    class MockChoice:
        def __init__(self, content: str):
            self.message = MockOpenAIClient.MockMessage(content)

    class MockResponse:
        def __init__(self, content: str):
            self.choices = [MockOpenAIClient.MockChoice(content)]

    class MockCompletions:
        async def create(self, **kwargs):
            # Simulera AI-svar baserat på prompt
            prompt = kwargs.get("messages", [{}])[-1].get("content", "")

            if "selectors" in prompt.lower():
                mock_response = """
                {
                    "primary_selectors": {
                        "title": ".product-title, h1",
                        "price": ".price, .cost, [class*='price']",
                        "description": ".description, .product-desc"
                    },
                    "fallback_selectors": {
                        "title": ["h1", "h2", ".title"],
                        "price": [".price", ".cost", "[data-price]"]
                    },
                    "reasoning": "AI-genererade selectors baserat på vanliga HTML-mönster",
                    "confidence": 0.85
                }
                """
            elif "analysera" in prompt.lower():
                mock_response = """
                {
                    "intent": "hitta produktpris",
                    "entity": "iPhone 15",
                    "data_type": "pris",
                    "website_hint": "amazon",
                    "expected_format": "numeriskt värde med valuta"
                }
                """
            else:
                mock_response = """
                Baserat på den tillhandahållna datan kan jag ge följande insikter:
                
                1. Prismönster: iPhone 15 är prisat högre än Samsung Galaxy med $100 skillnad
                2. Betyg: Båda produkterna har höga betyg över 4.0, vilket indikerar hög kundnöjdhet
                3. Marknadsposition: Apple fortsätter att ha premium-prissättning
                4. Rekommendation: Övervaka konkurrentpriser för marknadsanalys
                5. Trend: Smartphones över $800 visar stark efterfrågan
                """

            return MockOpenAIClient.MockResponse(mock_response)

    class MockChat:
        def __init__(self):
            self.completions = MockOpenAIClient.MockCompletions()

    def __init__(self):
        self.chat = self.MockChat()


@dataclass
class AIScrapingRequest:
    """AI-scraping request med naturligt språk"""

    query: str
    target_url: Optional[str] = None
    context: Optional[str] = None
    expected_data_type: Optional[str] = None
    confidence_threshold: float = 0.8


@dataclass
class AIScrapingResult:
    """Resultat från AI-driven scraping"""

    success: bool
    data: Dict[str, Any]
    selectors_used: Dict[str, str]
    confidence_score: float
    reasoning: str
    alternative_selectors: List[Dict[str, str]] = field(default_factory=list)
    ai_suggestions: List[str] = field(default_factory=list)


class BaseAIIntelligence(ABC):
    """Abstrakt basklass för AI-intelligens"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = ScrapingLogger(__name__)
        self.openai_client = None
        self._setup_ai_models()

    def _setup_ai_models(self):
        """Konfigurera AI-modeller"""
        try:
            api_key = self.config.get("ai.openai_api_key")
            if api_key:
                openai.api_key = api_key
                self.openai_client = openai.AsyncOpenAI(api_key=api_key)
            else:
                self.logger.info("Använder mock OpenAI-klient för demo")
                self.openai_client = MockOpenAIClient()
        except Exception as e:
            self.logger.warning(f"Kunde inte konfigurera OpenAI, använder mock: {e}")
            self.openai_client = MockOpenAIClient()

    @abstractmethod
    async def process(self, content: str, request: AIScrapingRequest) -> AIScrapingResult:
        """Processa innehåll med AI"""
        # Implementera bas-processering
        selectors = await self.analyze_page_structure(content, request.query)
        return AIScrapingResult(
            success=True,
            data={"selectors": selectors},
            selectors_used=selectors,
            confidence_score=0.8,
            reasoning="AI-genererade selectors från HTML-innehåll",
        )


class GPT4SelectorGenerator(BaseAIIntelligence):
    """GPT-4 driven automatisk selector-generering"""

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self.selector_cache = {}
        self.learning_history = []

    async def analyze_page_structure(self, html_content: str, target_data: str) -> Dict[str, str]:
        """
        Analysera HTML-struktur och generera optimala selectors
        """
        # OpenAI-klient finns alltid (antingen verklig eller mock)

        # Skapa prompt för GPT-4
        prompt = self._create_analysis_prompt(html_content, target_data)

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Du är en expert på web scraping och HTML-analys. Generera CSS/XPath selectors för att extrahera specifik data.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            result = response.choices[0].message.content
            selectors = self._parse_selector_response(result)

            # Cache resultatet
            cache_key = f"{hash(html_content)}:{target_data}"
            self.selector_cache[cache_key] = selectors

            return selectors

        except Exception as e:
            self.logger.error(f"GPT-4 selector-generering misslyckades: {e}")
            return {}

    def _create_analysis_prompt(self, html_content: str, target_data: str) -> str:
        """Skapa intelligent prompt för GPT-4"""
        return f"""
        Analysera följande HTML och generera CSS/XPath selectors för att extrahera: "{target_data}"
        
        HTML:
        {html_content[:5000]}  # Begränsa för token-limit
        
        Instruktioner:
        1. Identifiera element som innehåller mål-data
        2. Generera robusta selectors som fungerar även vid mindre ändringar
        3. Prioritera CSS selectors över XPath när möjligt
        4. Inkludera fallback-selectors
        5. Förklara varför varje selector valdes
        
        Returnera resultatet i JSON-format:
        {{
            "primary_selectors": {{
                "title": "selector",
                "price": "selector",
                "description": "selector"
            }},
            "fallback_selectors": {{
                "title": ["selector1", "selector2"],
                "price": ["selector1", "selector2"]
            }},
            "reasoning": "Förklaring av valda selectors",
            "confidence": 0.95
        }}
        """

    def _parse_selector_response(self, response: str) -> Dict[str, str]:
        """Parsa GPT-4 svar till selectors"""
        try:
            # Extrahera JSON från response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("primary_selectors", {})
        except Exception as e:
            self.logger.error(f"Kunde inte parsa selector-response: {e}")

        return {}

    async def self_improving_selectors(
        self, url: str, selectors: Dict[str, str], success_rate: float
    ) -> Dict[str, str]:
        """
        Förbättra selectors baserat på framgångsgrad
        """
        if success_rate < 0.8:  # Om framgångsgrad är låg
            self.learning_history.append(
                {
                    "url": url,
                    "selectors": selectors,
                    "success_rate": success_rate,
                    "timestamp": asyncio.get_event_loop().time(),
                }
            )

            # Analysera mönster i misslyckade försök
            improved_selectors = await self._learn_from_failures(url, selectors)
            return improved_selectors

        return selectors

    async def _learn_from_failures(self, url: str, selectors: Dict[str, str]) -> Dict[str, str]:
        """Lär från misslyckade scraping-försök"""
        # Här skulle vi implementera ML-algoritmer för att förbättra selectors
        # För nu returnerar vi förbättrade versioner baserat på heuristik
        improved = {}
        for key, selector in selectors.items():
            # Lägg till fallback-selectors
            if "class" in selector:
                improved[key] = f"{selector}, [class*='{selector.split('.')[-1]}']"
            else:
                improved[key] = selector

        return improved

    async def process(self, content: str, request: AIScrapingRequest) -> AIScrapingResult:
        """Processa innehåll med GPT-4 selector-generering"""
        selectors = await self.analyze_page_structure(content, request.query)
        return AIScrapingResult(
            success=True,
            data={"selectors": selectors},
            selectors_used=selectors,
            confidence_score=0.85,
            reasoning="GPT-4 genererade selectors från HTML-innehåll",
        )


class ComputerVisionScraper(BaseAIIntelligence):
    """Computer vision för dynamisk content detection"""

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self.ocr_pipeline = None
        self.object_detection_model = None
        self._setup_cv_models()

    def _setup_cv_models(self):
        """Konfigurera computer vision modeller"""
        try:
            # OCR pipeline
            self.ocr_pipeline = pipeline("text-generation", model="gpt2")

            # Object detection (förenklad version)
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                self.object_detection_model = cv2.CascadeClassifier(cascade_path)
                if self.object_detection_model.empty():
                    self.logger.warning("Kunde inte ladda cascade-fil, använder alternativ metod")
                    self.object_detection_model = None
            except Exception as e:
                self.logger.warning(f"Cascade-fil misslyckades, använder alternativ: {e}")
                self.object_detection_model = None
        except Exception as e:
            self.logger.warning(f"Kunde inte konfigurera CV-modeller: {e}")

    async def extract_text_from_images(self, image_data: bytes) -> List[str]:
        """OCR för att läsa text från bilder"""
        try:
            # Konvertera bytes till PIL Image
            image = Image.open(io.BytesIO(image_data))

            # Konvertera till OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # OCR med Tesseract
            text = pytesseract.image_to_string(cv_image, lang="eng+swe")

            # Rensa och strukturera text
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            return lines

        except Exception as e:
            self.logger.error(f"OCR misslyckades: {e}")
            return []

    async def detect_ui_elements(self, screenshot: bytes) -> Dict[str, List[Tuple[int, int, int, int]]]:
        """Identifierar UI-element via computer vision"""
        try:
            image = Image.open(io.BytesIO(screenshot))
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Konvertera till gråskala
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

            # Detektera konturer (för att hitta knappar, formulär, etc.)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            ui_elements = {"buttons": [], "forms": [], "tables": [], "text_areas": []}

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h

                # Klassificera element baserat på storlek och form
                if 50 < area < 5000:  # Knapp-storlek
                    ui_elements["buttons"].append((x, y, w, h))
                elif area > 10000:  # Större element
                    aspect_ratio = w / h
                    if 0.5 < aspect_ratio < 2.0:
                        ui_elements["forms"].append((x, y, w, h))
                    else:
                        ui_elements["tables"].append((x, y, w, h))

            return ui_elements

        except Exception as e:
            self.logger.error(f"UI-element detection misslyckades: {e}")
            return {}

    async def process(self, content: str, request: AIScrapingRequest) -> AIScrapingResult:
        """Processa innehåll med computer vision"""
        # Implementation för computer vision processing
        pass


class NaturalLanguageQueryInterface(BaseAIIntelligence):
    """Naturligt språk query interface"""

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self.selector_generator = GPT4SelectorGenerator(config)
        self.query_cache = {}

    async def query(self, question: str, target_url: Optional[str] = None) -> AIScrapingResult:
        """
        Ställ frågor på naturligt språk
        Exempel: "Vad kostar iPhone 15 på Amazon?"
        """
        # Analysera frågan
        parsed_query = await self._parse_natural_language_query(question)

        # Hitta rätt webbplats om inte specificerad
        if not target_url:
            target_url = await self._find_relevant_website(parsed_query)

        # Generera selectors baserat på frågan
        selectors = await self._generate_selectors_from_query(parsed_query, target_url)

        # Utför scraping
        result = await self._execute_scraping(target_url, selectors, parsed_query)

        return result

    async def _parse_natural_language_query(self, question: str) -> Dict[str, Any]:
        """Parsa naturligt språk till strukturerad data"""
        # OpenAI-klient finns alltid (antingen verklig eller mock)

        prompt = f"""
        Analysera följande fråga och extrahera strukturerad information:
        
        Fråga: "{question}"
        
        Returnera JSON med:
        {{
            "intent": "vad användaren vill veta",
            "entity": "vad som söks efter",
            "data_type": "pris|recension|beskrivning|etc",
            "website_hint": "föreslagna webbplatser",
            "expected_format": "svar-format"
        }}
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Du är en expert på att analysera naturligt språk för web scraping."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )

            result = response.choices[0].message.content
            return json.loads(result)

        except Exception as e:
            self.logger.error(f"Query parsing misslyckades: {e}")
            return {"intent": "unknown", "entity": question}

    async def _find_relevant_website(self, parsed_query: Dict[str, Any]) -> str:
        """Hitta relevant webbplats baserat på query"""
        # Enkel heuristik för att hitta webbplatser
        entity = parsed_query.get("entity", "").lower()
        website_hint = parsed_query.get("website_hint", "")

        # Mappning av vanliga webbplatser
        website_mapping = {
            "amazon": "https://www.amazon.com",
            "ebay": "https://www.ebay.com",
            "google": "https://www.google.com",
            "wikipedia": "https://www.wikipedia.org",
        }

        for keyword, url in website_mapping.items():
            if keyword in entity or keyword in website_hint:
                return url

        # Fallback till Google
        return "https://www.google.com"

    async def _generate_selectors_from_query(self, parsed_query: Dict[str, Any], url: str) -> Dict[str, str]:
        """Generera selectors baserat på parsed query"""
        intent = parsed_query.get("intent", "")
        data_type = parsed_query.get("data_type", "")

        # Mappning av vanliga data-typer till selectors
        selector_mapping = {
            "pris": {
                "price": ".price, .cost, [class*='price'], [class*='cost']",
                "currency": "[class*='currency'], .currency",
            },
            "recension": {
                "rating": ".rating, .stars, [class*='rating']",
                "review_text": ".review, .comment, [class*='review']",
            },
            "beskrivning": {
                "description": ".description, .details, [class*='description']",
                "title": ".title, .name, h1, h2",
            },
        }

        return selector_mapping.get(data_type, {})

    async def _execute_scraping(
        self, url: str, selectors: Dict[str, str], parsed_query: Dict[str, Any]
    ) -> AIScrapingResult:
        """Utför faktisk scraping"""
        # Här skulle vi integrera med huvud-scraping-modulen
        # För nu returnerar vi en mock-resultat

        return AIScrapingResult(
            success=True,
            data={"answer": f"Simulerat svar för: {parsed_query.get('intent', '')}"},
            selectors_used=selectors,
            confidence_score=0.9,
            reasoning="AI-genererat svar baserat på naturligt språk query",
        )

    async def process(self, content: str, request: AIScrapingRequest) -> AIScrapingResult:
        """Processa innehåll med naturligt språk"""
        return await self.query(request.query, request.target_url)


class AIIntelligenceOrchestrator:
    """Orchestrator för alla AI-intelligens moduler"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = ScrapingLogger(__name__)

        # Initiera alla AI-moduler
        self.gpt4_generator = GPT4SelectorGenerator(config)
        self.cv_scraper = ComputerVisionScraper(config)
        self.nl_interface = NaturalLanguageQueryInterface(config)

        # AI-modeller pipeline
        self.ai_pipeline = [self.gpt4_generator, self.cv_scraper, self.nl_interface]

    async def intelligent_scrape(self, request: AIScrapingRequest, html_content: str = None) -> AIScrapingResult:
        """
        Intelligent scraping med alla AI-moduler
        """
        self.logger.info(f"Startar intelligent scraping för: {request.query}")

        # Försök med naturligt språk först
        if "?" in request.query or any(
            word in request.query.lower() for word in ["vad", "hur", "när", "var", "vilken"]
        ):
            return await self.nl_interface.query(request.query, request.target_url)

        # Annars använd GPT-4 för selector-generering
        if html_content:
            selectors = await self.gpt4_generator.analyze_page_structure(html_content, request.query)

            # Utför scraping med genererade selectors
            result = await self._execute_with_selectors(request.target_url, selectors)

            # Förbättra selectors baserat på resultat
            improved_selectors = await self.gpt4_generator.self_improving_selectors(
                request.target_url, selectors, result.confidence_score
            )

            if improved_selectors != selectors:
                result = await self._execute_with_selectors(request.target_url, improved_selectors)
                result.selectors_used = improved_selectors

            return result

        return AIScrapingResult(
            success=False,
            data={},
            selectors_used={},
            confidence_score=0.0,
            reasoning="Inget HTML-innehåll tillhandahållet",
        )

    async def _execute_with_selectors(self, url: str, selectors: Dict[str, str]) -> AIScrapingResult:
        """Utför scraping med givna selectors"""
        # Här skulle vi integrera med huvud-scraping-modulen
        # För nu returnerar vi en mock-resultat

        return AIScrapingResult(
            success=True,
            data={"extracted_data": "Simulerat data från AI-selectors"},
            selectors_used=selectors,
            confidence_score=0.85,
            reasoning="AI-genererade selectors användes framgångsrikt",
        )

    async def get_ai_insights(self, scraped_data: Dict[str, Any]) -> List[str]:
        """Få AI-insikter från scraped data"""
        # OpenAI-klient finns alltid (antingen verklig eller mock)

        try:
            prompt = f"""
            Analysera följande scraped data och ge insikter:
            
            Data: {json.dumps(scraped_data, indent=2)}
            
            Ge 3-5 insikter om:
            1. Mönster i datan
            2. Avvikelser eller intressanta observationer
            3. Rekommendationer för vidare analys
            """

            response = await self.gpt4_generator.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Du är en expert på data-analys och insikter."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            insights = response.choices[0].message.content.split("\n")
            return [insight.strip() for insight in insights if insight.strip()]

        except Exception as e:
            self.logger.error(f"AI-insikter misslyckades: {e}")
            return []


# Exempel på användning
async def demo_ai_intelligence():
    """Demo av AI-intelligens funktioner"""

    # Konfigurera med OpenAI API key
    config = Config()
    config.set("ai.openai_api_key", "your-openai-api-key-here")

    orchestrator = AIIntelligenceOrchestrator(config)

    # Exempel 1: Naturligt språk query
    request1 = AIScrapingRequest(query="Vad kostar iPhone 15 på Amazon?", target_url="https://www.amazon.com")

    result1 = await orchestrator.intelligent_scrape(request1)
    print(f"Resultat 1: {result1.data}")

    # Exempel 2: AI-selector generering
    html_content = """
    <html>
        <body>
            <div class="product">
                <h1 class="product-title">iPhone 15</h1>
                <span class="price">$999</span>
                <p class="description">Latest iPhone model</p>
            </div>
        </body>
    </html>
    """

    request2 = AIScrapingRequest(query="Extrahera produktinformation", target_url="https://example.com")

    result2 = await orchestrator.intelligent_scrape(request2, html_content)
    print(f"Resultat 2: {result2.selectors_used}")

    # Exempel 3: AI-insikter
    scraped_data = {
        "products": [
            {"name": "iPhone 15", "price": 999, "rating": 4.5},
            {"name": "Samsung Galaxy", "price": 899, "rating": 4.3},
        ]
    }

    insights = await orchestrator.get_ai_insights(scraped_data)
    print(f"AI-insikter: {insights}")


if __name__ == "__main__":
    asyncio.run(demo_ai_intelligence())
