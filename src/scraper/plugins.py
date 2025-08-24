"""
Plugin-system för anpassade parsers och validators
"""

import asyncio
import importlib
import inspect
import json
import os
import sys
from typing import Dict, List, Optional, Any, Type, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import structlog

from ..utils.config import Config


class BasePlugin(ABC):
    """Basklass för alla plugins"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = structlog.get_logger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin-namn"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin-version"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin-beskrivning"""
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        """Hämtar plugin-specifik konfiguration"""
        plugin_key = f"plugins.{self.name}.{key}"
        return self.config.get(plugin_key, default)

    def set_config(self, key: str, value: Any):
        """Sätter plugin-specifik konfiguration"""
        plugin_key = f"plugins.{self.name}.{key}"
        self.config.set(plugin_key, value)


class BaseParser(BasePlugin):
    """Basklass för anpassade parsers"""

    @abstractmethod
    async def parse(self, content: str, url: str, **kwargs) -> Dict[str, Any]:
        """Parsar innehåll och returnerar strukturerad data"""
        pass

    def can_parse(self, content: str, url: str, content_type: str) -> bool:
        """Kontrollerar om parsern kan hantera innehållet"""
        return True

    def get_supported_content_types(self) -> List[str]:
        """Returnerar stödda content-types"""
        return ["text/html", "application/json", "text/plain"]


class BaseValidator(BasePlugin):
    """Basklass för anpassade validators"""

    @abstractmethod
    async def validate(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Validerar data och returnerar resultat"""
        pass

    def get_validation_rules(self) -> Dict[str, Any]:
        """Returnerar valideringsregler"""
        return {}


class BaseExporter(BasePlugin):
    """Basklass för anpassade exporters"""

    @abstractmethod
    async def export(self, data: Dict[str, Any], output_path: str, **kwargs) -> bool:
        """Exporterar data till fil"""
        pass

    def get_supported_formats(self) -> List[str]:
        """Returnerar stödda export-format"""
        return []


@dataclass
class PluginInfo:
    """Information om ett plugin"""

    name: str
    version: str
    description: str
    type: str  # parser, validator, exporter
    class_name: str
    module_path: str
    is_enabled: bool = True
    config: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konverterar till dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "type": self.type,
            "class_name": self.class_name,
            "module_path": self.module_path,
            "is_enabled": self.is_enabled,
            "config": self.config or {},
        }


class PluginManager:
    """
    Hanterar plugin-systemet
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = structlog.get_logger(__name__)

        # Plugin-register
        self.plugins: Dict[str, PluginInfo] = {}
        self.instances: Dict[str, BasePlugin] = {}

        # Plugin-kataloger
        self.plugin_dirs = self.config.get("plugins.directories", ["plugins", "src/plugins", "custom_plugins"])

        # Ladda plugins
        self._discover_plugins()
        self._load_enabled_plugins()

    def _discover_plugins(self):
        """Upptäcker tillgängliga plugins"""
        for plugin_dir in self.plugin_dirs:
            if os.path.exists(plugin_dir):
                self._scan_plugin_directory(plugin_dir)

    def _scan_plugin_directory(self, directory: str):
        """Skannar en plugin-katalog"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    module_path = os.path.join(root, file)
                    self._load_plugin_module(module_path)

    def _load_plugin_module(self, module_path: str):
        """Laddar en plugin-modul"""
        try:
            # Konvertera fil-sökväg till modul-sökväg
            module_name = os.path.splitext(module_path)[0].replace(os.sep, ".")

            # Lägg till katalogen i Python-sökvägen
            module_dir = os.path.dirname(module_path)
            if module_dir not in sys.path:
                sys.path.insert(0, module_dir)

            # Importera modulen
            module = importlib.import_module(module_name)

            # Hitta plugin-klasser
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BasePlugin)
                    and obj != BasePlugin
                    and obj != BaseParser
                    and obj != BaseValidator
                    and obj != BaseExporter
                ):

                    self._register_plugin(obj, module_name)

        except Exception as e:
            self.logger.error(f"Error loading plugin module {module_path}: {str(e)}")

    def _register_plugin(self, plugin_class: Type[BasePlugin], module_path: str):
        """Registrerar ett plugin"""
        try:
            # Skapa temporär instans för att hämta metadata
            temp_instance = plugin_class(self.config)

            plugin_type = self._get_plugin_type(plugin_class)

            plugin_info = PluginInfo(
                name=temp_instance.name,
                version=temp_instance.version,
                description=temp_instance.description,
                type=plugin_type,
                class_name=plugin_class.__name__,
                module_path=module_path,
                is_enabled=self.config.get(f"plugins.{temp_instance.name}.enabled", True),
            )

            self.plugins[temp_instance.name] = plugin_info
            self.logger.info(f"Registered plugin: {temp_instance.name} ({plugin_type})")

        except Exception as e:
            self.logger.error(f"Error registering plugin {plugin_class.__name__}: {str(e)}")

    def _get_plugin_type(self, plugin_class: Type[BasePlugin]) -> str:
        """Bestämmer plugin-typ"""
        if issubclass(plugin_class, BaseParser):
            return "parser"
        elif issubclass(plugin_class, BaseValidator):
            return "validator"
        elif issubclass(plugin_class, BaseExporter):
            return "exporter"
        else:
            return "unknown"

    def _load_enabled_plugins(self):
        """Laddar aktiverade plugins"""
        for plugin_name, plugin_info in self.plugins.items():
            if plugin_info.is_enabled:
                self._load_plugin_instance(plugin_name)

    def _load_plugin_instance(self, plugin_name: str):
        """Laddar en plugin-instans"""
        try:
            plugin_info = self.plugins[plugin_name]

            # Importera modulen
            module = importlib.import_module(plugin_info.module_path)

            # Hitta plugin-klassen
            plugin_class = getattr(module, plugin_info.class_name)

            # Skapa instans
            instance = plugin_class(self.config)
            self.instances[plugin_name] = instance

            self.logger.info(f"Loaded plugin instance: {plugin_name}")

        except Exception as e:
            self.logger.error(f"Error loading plugin instance {plugin_name}: {str(e)}")

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Hämtar en plugin-instans"""
        return self.instances.get(name)

    def get_plugins_by_type(self, plugin_type: str) -> List[BasePlugin]:
        """Hämtar plugins av en specifik typ"""
        plugins = []
        for plugin_name, plugin_info in self.plugins.items():
            if plugin_info.type == plugin_type and plugin_info.is_enabled and plugin_name in self.instances:
                plugins.append(self.instances[plugin_name])
        return plugins

    def enable_plugin(self, name: str) -> bool:
        """Aktiverar ett plugin"""
        if name in self.plugins:
            plugin_info = self.plugins[name]
            plugin_info.is_enabled = True
            self.config.set(f"plugins.{name}.enabled", True)

            if name not in self.instances:
                self._load_plugin_instance(name)

            self.logger.info(f"Enabled plugin: {name}")
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """Inaktiverar ett plugin"""
        if name in self.plugins:
            plugin_info = self.plugins[name]
            plugin_info.is_enabled = False
            self.config.set(f"plugins.{name}.enabled", False)

            if name in self.instances:
                del self.instances[name]

            self.logger.info(f"Disabled plugin: {name}")
            return True
        return False

    def reload_plugin(self, name: str) -> bool:
        """Laddar om ett plugin"""
        if name in self.plugins:
            # Ta bort befintlig instans
            if name in self.instances:
                del self.instances[name]

            # Ladda om
            self._load_plugin_instance(name)
            self.logger.info(f"Reloaded plugin: {name}")
            return True
        return False

    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """Hämtar plugin-information"""
        return self.plugins.get(name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Listar alla plugins"""
        return [plugin_info.to_dict() for plugin_info in self.plugins.values()]

    def get_plugin_stats(self) -> Dict[str, Any]:
        """Returnerar plugin-statistik"""
        total_plugins = len(self.plugins)
        enabled_plugins = len([p for p in self.plugins.values() if p.is_enabled])

        type_counts = {}
        for plugin_info in self.plugins.values():
            plugin_type = plugin_info.type
            type_counts[plugin_type] = type_counts.get(plugin_type, 0) + 1

        return {
            "total_plugins": total_plugins,
            "enabled_plugins": enabled_plugins,
            "disabled_plugins": total_plugins - enabled_plugins,
            "type_distribution": type_counts,
        }


# Exempel på anpassade plugins


class NewsParser(BaseParser):
    """Exempel på en anpassad parser för nyhetssidor"""

    @property
    def name(self) -> str:
        return "news_parser"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Parser för nyhetssidor med artikel-extraktion"

    def can_parse(self, content: str, url: str, content_type: str) -> bool:
        """Kontrollerar om det är en nyhetssida"""
        news_domains = self.get_config("news_domains", ["news.yahoo.com", "bbc.com", "cnn.com", "reuters.com"])

        from urllib.parse import urlparse

        parsed_url = urlparse(url)
        return any(domain in parsed_url.netloc for domain in news_domains)

    async def parse(self, content: str, url: str, **kwargs) -> Dict[str, Any]:
        """Parsar nyhetsartikel"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, "html.parser")

        # Extrahera artikel-information
        article_data = {
            "title": self._extract_title(soup),
            "author": self._extract_author(soup),
            "published_date": self._extract_date(soup),
            "content": self._extract_content(soup),
            "summary": self._extract_summary(soup),
            "tags": self._extract_tags(soup),
            "url": url,
        }

        return article_data

    def _extract_title(self, soup) -> str:
        """Extraherar artikel-titel"""
        selectors = ["h1", ".article-title", ".headline", "title"]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()

        return ""

    def _extract_author(self, soup) -> str:
        """Extraherar författare"""
        selectors = [".author", ".byline", "[rel='author']", ".writer"]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()

        return ""

    def _extract_date(self, soup) -> str:
        """Extraherar publiceringsdatum"""
        selectors = [".published-date", ".date", "time", ".timestamp"]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()

        return ""

    def _extract_content(self, soup) -> str:
        """Extraherar artikel-innehåll"""
        selectors = [".article-content", ".story-body", ".content", "article"]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()

        return ""

    def _extract_summary(self, soup) -> str:
        """Extraherar sammanfattning"""
        selectors = [".summary", ".excerpt", ".description", "meta[name='description']"]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if selector == "meta[name='description']":
                    return element.get("content", "")
                else:
                    return element.get_text().strip()

        return ""

    def _extract_tags(self, soup) -> List[str]:
        """Extraherar taggar"""
        selectors = [".tags a", ".categories a", ".keywords a"]

        tags = []
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                tag = element.get_text().strip()
                if tag:
                    tags.append(tag)

        return tags


class EmailValidator(BaseValidator):
    """Exempel på en anpassad validator för e-postadresser"""

    @property
    def name(self) -> str:
        return "email_validator"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Validerar och normaliserar e-postadresser"

    async def validate(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Validerar e-postadresser i data"""
        import re

        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        validated_data = data.copy()
        validation_errors = []

        # Hitta och validera e-postadresser
        for key, value in data.items():
            if isinstance(value, str) and "@" in value:
                if email_pattern.match(value):
                    # Normalisera e-postadress
                    validated_data[key] = value.lower().strip()
                else:
                    validation_errors.append(f"Invalid email format: {value}")
                    validated_data[key] = None

        return {
            "data": validated_data,
            "is_valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "validated_emails": [value for value in validated_data.values() if isinstance(value, str) and "@" in value],
        }

    def get_validation_rules(self) -> Dict[str, Any]:
        return {
            "email_format": "RFC 5322 compliant",
            "normalization": "lowercase and trim",
            "validation": "regex pattern matching",
        }


class JSONLExporter(BaseExporter):
    """Exempel på en anpassad exporter för JSONL-format"""

    @property
    def name(self) -> str:
        return "jsonl_exporter"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Exporterar data till JSONL-format (JSON Lines)"

    async def export(self, data: Dict[str, Any], output_path: str, **kwargs) -> bool:
        """Exporterar data till JSONL-format"""
        try:
            # Skapa output-katalog om den inte finns
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                # Skriv varje rad som JSON
                json.dump(data, f, ensure_ascii=False)
                f.write("\n")

            self.logger.info(f"Exported data to JSONL: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting to JSONL: {str(e)}")
            return False

    def get_supported_formats(self) -> List[str]:
        return ["jsonl", "jsonl.gz"]


# Plugin-registrering
def register_builtin_plugins(plugin_manager: PluginManager):
    """Registrerar inbyggda plugins"""
    builtin_plugins = [NewsParser, EmailValidator, JSONLExporter]

    for plugin_class in builtin_plugins:
        plugin_manager._register_plugin(plugin_class, __name__)
