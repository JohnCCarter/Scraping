"""
Configuration management for the web scraping toolkit
"""

import os
import yaml
import json
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """
    Konfigurationshanterare som stöder YAML, JSON och miljövariabler
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initierar konfiguration

        Args:
            config_path: Sökväg till konfigurationsfil
        """
        self.config_data: Dict[str, Any] = {}

        # Läs standardkonfiguration
        self._load_default_config()

        # Läs användarkonfiguration om den finns
        if config_path:
            self._load_config_file(config_path)

        # Läs miljövariabler (överstiger filkonfiguration)
        self._load_environment_vars()

    def _load_default_config(self):
        """Laddar standardkonfiguration"""
        self.config_data = {
            "scraper": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "timeout": 30,
                "connect_timeout": 10,
                "max_retries": 3,
                "delay_between_requests": 1.0,
                "use_playwright": False,
                "headless": True,
            },
            "rate_limiting": {"requests_per_minute": 60, "max_concurrent": 10, "delay_between_requests": 1.0},
            "logging": {"level": "INFO", "format": "json", "file": "logs/scraper.log"},
            "export": {"default_format": "json", "output_dir": "data"},
            "proxy": {"enabled": False, "url": None, "username": None, "password": None},
        }

    def _load_config_file(self, config_path: str):
        """Laddar konfiguration från fil"""
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            if path.suffix.lower() in [".yaml", ".yml"]:
                with open(path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f)
            elif path.suffix.lower() == ".json":
                with open(path, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {path.suffix}")

            # Merge med befintlig konfiguration
            self._merge_config(file_config)

        except Exception as e:
            raise ValueError(f"Error loading config file {config_path}: {str(e)}")

    def _load_environment_vars(self):
        """Laddar konfiguration från miljövariabler"""
        env_mappings = {
            "SCRAPER_USER_AGENT": "scraper.user_agent",
            "SCRAPER_TIMEOUT": "scraper.timeout",
            "SCRAPER_MAX_RETRIES": "scraper.max_retries",
            "SCRAPER_DELAY": "scraper.delay_between_requests",
            "SCRAPER_USE_PLAYWRIGHT": "scraper.use_playwright",
            "RATE_LIMIT_REQUESTS_PER_MINUTE": "rate_limiting.requests_per_minute",
            "RATE_LIMIT_MAX_CONCURRENT": "rate_limiting.max_concurrent",
            "LOG_LEVEL": "logging.level",
            "PROXY_URL": "proxy.url",
            "PROXY_ENABLED": "proxy.enabled",
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Konvertera till rätt datatyp
                if config_key.endswith(".timeout") or config_key.endswith(".max_retries"):
                    value = int(value)
                elif config_key.endswith(".delay_between_requests") or config_key.endswith(".requests_per_minute"):
                    value = float(value)
                elif config_key.endswith(".use_playwright") or config_key.endswith(".enabled"):
                    value = value.lower() in ["true", "1", "yes"]

                self.set(config_key, value)

    def _merge_config(self, new_config: Dict[str, Any]):
        """Mergar ny konfiguration med befintlig"""

        def merge_dicts(base: Dict[str, Any], update: Dict[str, Any]):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dicts(base[key], value)
                else:
                    base[key] = value

        merge_dicts(self.config_data, new_config)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Hämtar konfigurationsvärde med punktnotation

        Args:
            key: Konfigurationsnyckel (t.ex. "scraper.timeout")
            default: Standardvärde om nyckeln inte finns

        Returns:
            Konfigurationsvärde
        """
        keys = key.split(".")
        value = self.config_data

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """
        Sätter konfigurationsvärde med punktnotation

        Args:
            key: Konfigurationsnyckel
            value: Värde att sätta
        """
        keys = key.split(".")
        config = self.config_data

        # Navigera till rätt nivå
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Sätt värdet
        config[keys[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        """Returnerar hela konfigurationen som dict"""
        return self.config_data.copy()

    def save(self, file_path: str):
        """
        Sparar konfiguration till fil

        Args:
            file_path: Sökväg till fil att spara till
        """
        path = Path(file_path)

        # Skapa mappar om de inte finns
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if path.suffix.lower() in [".yaml", ".yml"]:
                with open(path, "w", encoding="utf-8") as f:
                    yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
            elif path.suffix.lower() == ".json":
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")

        except Exception as e:
            raise ValueError(f"Error saving config to {file_path}: {str(e)}")

    def validate(self) -> bool:
        """
        Validerar konfiguration

        Returns:
            True om konfigurationen är giltig
        """
        try:
            # Kontrollera att obligatoriska fält finns
            required_fields = ["scraper.timeout", "scraper.max_retries", "rate_limiting.requests_per_minute"]

            for field in required_fields:
                if self.get(field) is None:
                    raise ValueError(f"Missing required config field: {field}")

            # Validera värden
            if self.get("scraper.timeout") <= 0:
                raise ValueError("scraper.timeout must be positive")

            if self.get("rate_limiting.requests_per_minute") <= 0:
                raise ValueError("rate_limiting.requests_per_minute must be positive")

            return True

        except Exception as e:
            raise ValueError(f"Configuration validation failed: {str(e)}")
