"""
Structured logging setup for the web scraping toolkit
"""

import sys
import logging
from pathlib import Path
from typing import Optional

import structlog
from structlog.stdlib import LoggerFactory


def setup_logger(
    name: str, log_level: str = "INFO", log_file: Optional[str] = None, log_format: str = "json"
) -> structlog.BoundLogger:
    """
    Konfigurerar strukturerad loggning

    Args:
        name: Logger-namn
        log_level: Loggnivå (DEBUG, INFO, WARNING, ERROR)
        log_file: Sökväg till loggfil (valfritt)
        log_format: Loggformat ("json" eller "console")

    Returns:
        Konfigurerad logger
    """

    # Skapa logs-mapp om den inte finns
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Konfigurera structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Lägg till formatter baserat på format
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Konfigurera standard logging
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=getattr(logging, log_level.upper()))

    # Lägg till filhandler om log_file är specificerat
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, log_level.upper()))

        # Konfigurera filhandler för JSON-format
        if log_format == "json":
            file_handler.setFormatter(logging.Formatter("%(message)s"))
        else:
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        logging.getLogger().addHandler(file_handler)

    return structlog.get_logger(name)


class ScrapingLogger:
    """
    Specialiserad logger för scraping-operationer med inbyggda metrics
    """

    def __init__(self, name: str = "scraper"):
        self.logger = setup_logger(name)
        self.metrics = {"requests": 0, "successes": 0, "failures": 0, "start_time": None, "end_time": None}

    def start_session(self, session_id: str, urls: list):
        """Loggar start av scraping-session"""
        self.metrics["start_time"] = structlog.processors.TimeStamper(fmt="iso")
        self.metrics["requests"] = len(urls)

        self.logger.info(
            "Starting scraping session",
            session_id=session_id,
            url_count=len(urls),
            urls=urls[:5] if len(urls) > 5 else urls,  # Logga bara första 5 URLs
        )

    def end_session(self, session_id: str):
        """Loggar slut av scraping-session"""
        self.metrics["end_time"] = structlog.processors.TimeStamper(fmt="iso")

        success_rate = (
            (self.metrics["successes"] / self.metrics["requests"]) * 100 if self.metrics["requests"] > 0 else 0
        )

        self.logger.info(
            "Scraping session completed",
            session_id=session_id,
            total_requests=self.metrics["requests"],
            successful_requests=self.metrics["successes"],
            failed_requests=self.metrics["failures"],
            success_rate=f"{success_rate:.1f}%",
        )

    def log_request(self, url: str, method: str = "GET"):
        """Loggar enskild request"""
        self.logger.debug("Making request", url=url, method=method)

    def log_response(self, url: str, status_code: int, response_time: float, success: bool):
        """Loggar response från request"""
        if success:
            self.metrics["successes"] += 1
            self.logger.info(
                "Request successful", url=url, status_code=status_code, response_time=f"{response_time:.2f}s"
            )
        else:
            self.metrics["failures"] += 1
            self.logger.warning(
                "Request failed", url=url, status_code=status_code, response_time=f"{response_time:.2f}s"
            )

    def log_error(self, url: str, error: str, error_type: str = "unknown"):
        """Loggar fel från scraping"""
        self.logger.error("Scraping error", url=url, error=error, error_type=error_type)

    def log_rate_limit(self, delay: float, reason: str = "rate_limit"):
        """Loggar rate limiting"""
        self.logger.info("Rate limiting applied", delay=f"{delay:.2f}s", reason=reason)

    def log_data_extracted(self, url: str, data_count: int, data_type: str = "unknown"):
        """Loggar extraherad data"""
        self.logger.info("Data extracted", url=url, data_count=data_count, data_type=data_type)

    def log_export(self, file_path: str, data_count: int, format: str):
        """Loggar data-export"""
        self.logger.info("Data exported", file_path=file_path, data_count=data_count, format=format)

    def info(self, message: str, **kwargs):
        """Allmän info-logging"""
        self.logger.info(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Allmän error-logging"""
        self.logger.error(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Allmän warning-logging"""
        self.logger.warning(message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Allmän debug-logging"""
        self.logger.debug(message, **kwargs)


# Global logger-instans för enkel åtkomst
def get_logger(name: str = "scraper") -> structlog.BoundLogger:
    """Hjälpfunktion för att få logger-instans"""
    return setup_logger(name)


def get_scraping_logger(name: str = "scraper") -> ScrapingLogger:
    """Hjälpfunktion för att få ScrapingLogger-instans"""
    return ScrapingLogger(name)
