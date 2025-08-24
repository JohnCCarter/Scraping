"""
HTML and JSON parsers for extracting data from web pages
"""

import json
import re
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
import structlog


class HTMLParser:
    """
    Parser för HTML-innehåll med stöd för CSS-selektorer och XPath-liknande funktionalitet
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    def parse(self, html_content: str, selectors: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Parsar HTML-innehåll och extraherar data baserat på selektorer

        Args:
            html_content: HTML-innehåll att parsa
            selectors: Dict med namn -> CSS-selektor mappningar

        Returns:
            Dict med extraherad data
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            if selectors:
                return self._extract_with_selectors(soup, selectors)
            else:
                return self._extract_common_data(soup)

        except Exception as e:
            self.logger.error(f"Error parsing HTML: {str(e)}")
            return {}

    def _extract_with_selectors(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extraherar data med specifika CSS-selektorer"""
        result = {}

        for name, selector in selectors.items():
            try:
                elements = soup.select(selector)

                if len(elements) == 1:
                    result[name] = self._extract_text(elements[0])
                elif len(elements) > 1:
                    result[name] = [self._extract_text(el) for el in elements]
                else:
                    result[name] = None

            except Exception as e:
                self.logger.warning(f"Error extracting {name} with selector {selector}: {str(e)}")
                result[name] = None

        return result

    def _extract_common_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extraherar vanlig data från HTML (titel, länkar, etc.)"""
        result = {}

        # Titel
        title_tag = soup.find("title")
        if title_tag:
            result["title"] = title_tag.get_text(strip=True)

        # Meta-beskrivning
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            result["description"] = meta_desc.get("content", "")

        # H1-rubriker
        h1_tags = soup.find_all("h1")
        if h1_tags:
            result["h1_headings"] = [h1.get_text(strip=True) for h1 in h1_tags]

        # Länkar
        links = soup.find_all("a", href=True)
        if links:
            result["links"] = []
            for link in links:
                href = link.get("href")
                text = link.get_text(strip=True)
                if href and text:
                    result["links"].append({"url": href, "text": text})

        # Bilder
        images = soup.find_all("img")
        if images:
            result["images"] = []
            for img in images:
                src = img.get("src")
                alt = img.get("alt", "")
                if src:
                    result["images"].append({"src": src, "alt": alt})

        # Text-innehåll (förenklad)
        text_content = soup.get_text()
        if text_content:
            # Rensa whitespace och extra whitespace
            cleaned_text = re.sub(r"\s+", " ", text_content).strip()
            result["text_content"] = cleaned_text[:1000] + "..." if len(cleaned_text) > 1000 else cleaned_text

        return result

    def _extract_text(self, element: Tag) -> str:
        """Extraherar text från ett HTML-element"""
        if element is None:
            return ""

        # Ta bort script och style element
        for script in element(["script", "style"]):
            script.decompose()

        text = element.get_text()
        # Rensa whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return text

    def extract_links(self, html_content: str, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Extraherar alla länkar från HTML

        Args:
            html_content: HTML-innehåll
            base_url: Bas-URL för att göra relativa länkar absoluta

        Returns:
            Lista med länkar
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            links = soup.find_all("a", href=True)

            result = []
            for link in links:
                href = link.get("href")
                text = link.get_text(strip=True)

                if href:
                    # Gör relativa länkar absoluta
                    if base_url and not href.startswith(("http://", "https://")):
                        href = urljoin(base_url, href)

                    result.append({"url": href, "text": text, "title": link.get("title", "")})

            return result

        except Exception as e:
            self.logger.error(f"Error extracting links: {str(e)}")
            return []

    def extract_forms(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extraherar formulär från HTML

        Args:
            html_content: HTML-innehåll

        Returns:
            Lista med formulär
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            forms = soup.find_all("form")

            result = []
            for form in forms:
                form_data = {"action": form.get("action", ""), "method": form.get("method", "get"), "inputs": []}

                # Extrahera input-fält
                inputs = form.find_all(["input", "textarea", "select"])
                for input_elem in inputs:
                    input_data = {
                        "type": input_elem.get("type", input_elem.name),
                        "name": input_elem.get("name", ""),
                        "value": input_elem.get("value", ""),
                        "required": input_elem.get("required") is not None,
                    }
                    form_data["inputs"].append(input_data)

                result.append(form_data)

            return result

        except Exception as e:
            self.logger.error(f"Error extracting forms: {str(e)}")
            return []


class JSONParser:
    """
    Parser för JSON-innehåll
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    def parse(self, json_content: str) -> Dict[str, Any]:
        """
        Parsar JSON-innehåll

        Args:
            json_content: JSON-sträng att parsa

        Returns:
            Parsad JSON-data
        """
        try:
            # Försök hitta JSON i HTML (vanligt för API-responses)
            json_match = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', json_content, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)

            # Rensa whitespace och parsa
            json_content = json_content.strip()
            return json.loads(json_content)

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {str(e)}")
            return {}
        except Exception as e:
            self.logger.error(f"Error parsing JSON: {str(e)}")
            return {}

    def extract_json_ld(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extraherar JSON-LD structured data från HTML

        Args:
            html_content: HTML-innehåll

        Returns:
            Lista med JSON-LD objekt
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            json_ld_scripts = soup.find_all("script", type="application/ld+json")

            result = []
            for script in json_ld_scripts:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, list):
                        result.extend(json_data)
                    else:
                        result.append(json_data)
                except json.JSONDecodeError:
                    continue

            return result

        except Exception as e:
            self.logger.error(f"Error extracting JSON-LD: {str(e)}")
            return []

    def extract_meta_tags(self, html_content: str) -> Dict[str, str]:
        """
        Extraherar meta-taggar från HTML

        Args:
            html_content: HTML-innehåll

        Returns:
            Dict med meta-taggar
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            meta_tags = soup.find_all("meta")

            result = {}
            for meta in meta_tags:
                name = meta.get("name") or meta.get("property")
                content = meta.get("content")

                if name and content:
                    result[name] = content

            return result

        except Exception as e:
            self.logger.error(f"Error extracting meta tags: {str(e)}")
            return {}


class DataExtractor:
    """
    Kombinerad data-extraktor som använder både HTML och JSON parsers
    """

    def __init__(self):
        self.html_parser = HTMLParser()
        self.json_parser = JSONParser()
        self.logger = structlog.get_logger(__name__)

    def extract_all(self, content: str, content_type: str = "auto") -> Dict[str, Any]:
        """
        Extraherar all tillgänglig data från innehåll

        Args:
            content: Innehåll att extrahera från
            content_type: Innehållstyp ("html", "json", "auto")

        Returns:
            Dict med all extraherad data
        """
        result = {}

        try:
            if content_type == "auto":
                content_type = self._detect_content_type(content)

            if content_type == "html":
                # HTML-extraktion
                result.update(self.html_parser.parse(content))
                result["json_ld"] = self.json_parser.extract_json_ld(content)
                result["meta_tags"] = self.json_parser.extract_meta_tags(content)
                result["links"] = self.html_parser.extract_links(content)
                result["forms"] = self.html_parser.extract_forms(content)

            elif content_type == "json":
                # JSON-extraktion
                result.update(self.json_parser.parse(content))

            # Lägg till metadata
            result["_metadata"] = {
                "content_type": content_type,
                "content_length": len(content),
                "extraction_timestamp": self._get_timestamp(),
            }

        except Exception as e:
            self.logger.error(f"Error in data extraction: {str(e)}")
            result["_error"] = str(e)

        return result

    def _detect_content_type(self, content: str) -> str:
        """Detekterar innehållstyp automatiskt"""
        content = content.strip()

        # Kontrollera om det är JSON
        if content.startswith("{") or content.startswith("["):
            return "json"

        # Kontrollera om det är HTML
        if "<html" in content.lower() or "<!doctype" in content.lower():
            return "html"

        # Standard är HTML
        return "html"

    def _get_timestamp(self) -> str:
        """Returnerar aktuell timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()
