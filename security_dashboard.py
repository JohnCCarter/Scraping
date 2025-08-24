#!/usr/bin/env python3
"""
🔒 SECURITY DASHBOARD - SECURITY & COMPLIANCE
Steg E: Security-first design, GDPR compliance, security auditing, threat detection
"""

import asyncio
import time
import threading
import random
import json
import hashlib
import hmac
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
from bs4 import BeautifulSoup
import ssl
import socket

# Importera våra moduler
from src.dashboard.app import DashboardApp
from src.utils.config import Config
from src.utils.logging import ScrapingLogger


class SecurityLevel(Enum):
    """Security levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceType(Enum):
    """Compliance types"""

    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"


class ThreatType(Enum):
    """Threat types"""

    RATE_LIMITING = "rate_limiting"
    IP_BLOCKING = "ip_blocking"
    CAPTCHA = "captcha"
    BOT_DETECTION = "bot_detection"
    SSL_ERRORS = "ssl_errors"
    MALWARE = "malware"


class SecurityScraper:
    """Security-focused scraper med compliance monitoring"""

    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.session = None
        self.is_running = False

        # Security-specific features
        self.security_level = SecurityLevel.HIGH
        self.compliance_status = {}
        self.threat_detection = []
        self.security_metrics = {}
        self.encryption_status = {}

        # GDPR compliance
        self.gdpr_compliance = {
            "data_minimization": True,
            "consent_management": True,
            "data_encryption": True,
            "access_controls": True,
            "audit_trail": True,
            "data_retention": True,
        }

        # Security monitoring
        self.security_monitoring = {
            "ssl_verification": True,
            "rate_limiting": True,
            "ip_rotation": True,
            "user_agent_rotation": True,
            "request_signatures": True,
            "threat_detection": True,
        }

        # Threat detection
        self.threats_detected = []
        self.blocked_requests = 0
        self.suspicious_activity = 0

    async def start(self):
        """Startar security scraper"""
        # Skapa säker session med SSL verification
        connector = aiohttp.TCPConnector(ssl=False)  # För demo
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={
                "User-Agent": "SecurityScraper/1.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            },
            connector=connector,
        )
        self.is_running = True

    async def stop(self):
        """Stoppar security scraper"""
        if self.session:
            await self.session.close()
        self.is_running = False

    async def scrape_with_security(self, url: str) -> Dict[str, Any]:
        """Scrapar med security-förbättringar"""
        if not self.is_running:
            return {"url": url, "error": "Scraper is not running", "status": "error"}

        start_time = time.time()

        try:
            # Security checks före request
            security_check = await self._perform_security_checks(url)
            if not security_check["safe_to_proceed"]:
                self.blocked_requests += 1
                return {
                    "url": url,
                    "error": security_check["reason"],
                    "status": "blocked",
                    "security_level": self.security_level.value,
                }

            # Säker request med headers
            headers = self._get_secure_headers(url)

            async with self.session.get(url, headers=headers) as response:
                content = await response.text()
                response_time = time.time() - start_time

                # Security analysis av response
                security_analysis = await self._analyze_security_response(response, content, url)

                # Uppdatera metrics
                self._update_security_metrics(response.status, response_time, security_analysis)

                return {
                    "url": url,
                    "status": response.status,
                    "response_time": response_time,
                    "security_analysis": security_analysis,
                    "content_length": len(content),
                    "security_level": self.security_level.value,
                    "gdpr_compliant": self._check_gdpr_compliance(content),
                }

        except Exception as e:
            self.request_count += 1
            self.error_count += 1

            # Threat detection
            threat = self._detect_threat_from_error(str(e))
            if threat:
                self.threats_detected.append(threat)

            return {"url": url, "error": str(e), "status": "error", "threat_detected": threat}

    async def _perform_security_checks(self, url: str) -> Dict[str, Any]:
        """Utför security checks före request"""
        checks = {"safe_to_proceed": True, "reason": None, "checks_passed": []}

        # SSL/TLS check
        try:
            parsed_url = aiohttp.URL(url)
            if parsed_url.scheme == "https":
                # Simulera SSL check
                checks["checks_passed"].append("ssl_verification")
        except Exception:
            checks["safe_to_proceed"] = False
            checks["reason"] = "Invalid URL format"

        # Rate limiting check
        if self.request_count > 1000:  # Simulera rate limiting
            checks["safe_to_proceed"] = False
            checks["reason"] = "Rate limit exceeded"
        else:
            checks["checks_passed"].append("rate_limiting")

        # URL blacklist check
        blacklisted_domains = ["malware.example.com", "phishing.example.com"]
        if any(domain in url for domain in blacklisted_domains):
            checks["safe_to_proceed"] = False
            checks["reason"] = "URL is blacklisted"
        else:
            checks["checks_passed"].append("url_validation")

        return checks

    def _get_secure_headers(self, url: str) -> Dict[str, str]:
        """Genererar säkra headers"""
        headers = {
            "User-Agent": f"SecurityScraper/1.0 (SecurityLevel: {self.security_level.value})",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

        # Lägg till security headers
        if self.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            headers["X-Requested-With"] = "XMLHttpRequest"
            headers["X-Forwarded-For"] = self._generate_secure_ip()

        return headers

    def _generate_secure_ip(self) -> str:
        """Genererar säker IP för rotation"""
        # Simulera IP rotation
        ips = ["192.168.1.100", "10.0.0.50", "172.16.0.25", "203.0.113.10"]
        return random.choice(ips)

    async def _analyze_security_response(self, response, content: str, url: str) -> Dict[str, Any]:
        """Analyserar response för security threats"""
        analysis = {
            "ssl_secure": True,
            "threats_detected": [],
            "compliance_issues": [],
            "security_score": 100,
            "gdpr_violations": [],
        }

        try:
            soup = BeautifulSoup(content, "html.parser")

            # Kolla efter security threats
            if "blocked" in content.lower() or "forbidden" in content.lower():
                analysis["threats_detected"].append("Access blocked")
                analysis["security_score"] -= 30

            # Kolla efter CAPTCHA
            captcha_indicators = ["captcha", "recaptcha", "verify you are human"]
            if any(indicator in content.lower() for indicator in captcha_indicators):
                analysis["threats_detected"].append("CAPTCHA detected")
                analysis["security_score"] -= 20

            # Kolla efter GDPR compliance
            gdpr_issues = self._check_gdpr_compliance_detailed(soup)
            analysis["gdpr_violations"] = gdpr_issues
            if gdpr_issues:
                analysis["security_score"] -= len(gdpr_issues) * 10

            # Kolla efter SSL issues
            if response.url.scheme != "https":
                analysis["ssl_secure"] = False
                analysis["security_score"] -= 25

            # Kolla efter suspicious patterns
            suspicious_patterns = ["hack", "exploit", "vulnerability"]
            if any(pattern in content.lower() for pattern in suspicious_patterns):
                analysis["threats_detected"].append("Suspicious content detected")
                analysis["security_score"] -= 15

        except Exception as e:
            analysis["error"] = str(e)
            analysis["security_score"] -= 10

        return analysis

    def _check_gdpr_compliance_detailed(self, soup) -> List[str]:
        """Kontrollerar GDPR compliance i detalj"""
        violations = []

        # Kolla efter cookies utan consent
        cookie_scripts = soup.find_all("script", string=lambda text: text and "cookie" in text.lower())
        if cookie_scripts and not soup.find("div", string=lambda text: text and "consent" in text.lower()):
            violations.append("Cookies without consent")

        # Kolla efter tracking scripts
        tracking_scripts = soup.find_all(
            "script",
            src=lambda src: src
            and any(tracker in src.lower() for tracker in ["google-analytics", "facebook", "twitter"]),
        )
        if tracking_scripts:
            violations.append("Tracking scripts detected")

        # Kolla efter personuppgifter
        personal_data_patterns = ["email", "phone", "address", "ssn", "personal"]
        for pattern in personal_data_patterns:
            if soup.find(string=lambda text: text and pattern in text.lower()):
                violations.append(f"Personal data pattern: {pattern}")
                break

        return violations

    def _check_gdpr_compliance(self, content: str) -> bool:
        """Enkel GDPR compliance check"""
        # Simulera GDPR compliance check
        return random.choice([True, True, True, False])  # 75% compliance

    def _detect_threat_from_error(self, error: str) -> Optional[Dict[str, Any]]:
        """Detekterar threats från error messages"""
        threat_indicators = {
            "rate limiting": ThreatType.RATE_LIMITING,
            "blocked": ThreatType.IP_BLOCKING,
            "captcha": ThreatType.CAPTCHA,
            "bot": ThreatType.BOT_DETECTION,
            "ssl": ThreatType.SSL_ERRORS,
            "malware": ThreatType.MALWARE,
        }

        for indicator, threat_type in threat_indicators.items():
            if indicator in error.lower():
                return {
                    "type": threat_type.value,
                    "timestamp": datetime.now().isoformat(),
                    "error": error,
                    "severity": "high",
                }

        return None

    def _update_security_metrics(self, status: int, response_time: float, security_analysis: Dict[str, Any]):
        """Uppdaterar security metrics"""
        self.request_count += 1
        self.success_count += 1

        # Uppdatera security metrics
        self.security_metrics = {
            "security_score_avg": security_analysis.get("security_score", 100),
            "threats_detected_count": len(self.threats_detected),
            "blocked_requests": self.blocked_requests,
            "gdpr_compliance_rate": self._calculate_gdpr_compliance_rate(),
            "ssl_secure_requests": 1 if security_analysis.get("ssl_secure", True) else 0,
            "suspicious_activity": self.suspicious_activity,
        }

        # Uppdatera compliance status
        self.compliance_status = {
            "gdpr": self._calculate_gdpr_compliance_rate(),
            "ccpa": random.uniform(85, 95),
            "hipaa": random.uniform(90, 98),
            "sox": random.uniform(88, 96),
            "pci_dss": random.uniform(92, 99),
        }

    def _calculate_gdpr_compliance_rate(self) -> float:
        """Beräknar GDPR compliance rate"""
        compliance_items = sum(self.gdpr_compliance.values())
        total_items = len(self.gdpr_compliance)
        return (compliance_items / total_items) * 100

    def set_security_level(self, level: SecurityLevel):
        """Sätter security level"""
        self.security_level = level

    def get_security_metrics(self) -> Dict[str, Any]:
        """Returnerar security metrics"""
        total_requests = max(self.request_count, 1)
        success_rate = min((self.success_count / total_requests) * 100, 100.0)

        return {
            # Grundläggande metrics
            "requests_total": self.request_count,
            "requests_success": self.success_count,
            "requests_error": self.error_count,
            "success_rate": success_rate,
            "uptime_seconds": time.time() - self.start_time,
            "current_rate": random.randint(10, 50),
            "active_sessions": 1,
            "is_running": self.is_running,
            "requests_per_minute": random.randint(10, 50),
            # Security-specific metrics
            "security_level": self.security_level.value,
            "security_score_avg": self.security_metrics.get("security_score_avg", 100),
            "threats_detected_count": len(self.threats_detected),
            "blocked_requests": self.blocked_requests,
            "gdpr_compliance_rate": self._calculate_gdpr_compliance_rate(),
            "ssl_secure_requests": self.security_metrics.get("ssl_secure_requests", 0),
            "suspicious_activity": self.suspicious_activity,
            "compliance_gdpr": self.compliance_status.get("gdpr", 0),
            "compliance_ccpa": self.compliance_status.get("ccpa", 0),
            "compliance_hipaa": self.compliance_status.get("hipaa", 0),
            "compliance_sox": self.compliance_status.get("sox", 0),
            "compliance_pci_dss": self.compliance_status.get("pci_dss", 0),
        }


class MockProxyManager:
    """Mock proxy manager med security features"""

    def __init__(self):
        self.total_proxies = 15
        self.active_proxies = 12
        self.failed_proxies = 3
        self.secure_proxies = 10

    def get_stats(self) -> Dict[str, Any]:
        success_rate = min((self.active_proxies / self.total_proxies) * 100, 100.0)
        security_rate = min((self.secure_proxies / self.total_proxies) * 100, 100.0)
        return {
            "total_proxies": self.total_proxies,
            "active_proxies": self.active_proxies,
            "failed_proxies": self.failed_proxies,
            "secure_proxies": self.secure_proxies,
            "success_rate": success_rate,
            "security_rate": security_rate,
            "average_response_time": random.uniform(0.5, 2.0),
            "requests_per_proxy": random.randint(50, 200),
        }


class MockWebhookManager:
    """Mock webhook manager med security features"""

    def __init__(self):
        self.total_webhooks = 8
        self.active_webhooks = 7
        self.sent_events = 250
        self.failed_events = 3
        self.secure_webhooks = 6

    def get_stats(self) -> Dict[str, Any]:
        total_events = max(self.sent_events + self.failed_events, 1)
        success_rate = min((self.sent_events / total_events) * 100, 100.0)
        security_rate = min((self.secure_webhooks / self.total_webhooks) * 100, 100.0)
        return {
            "total_webhooks": self.total_webhooks,
            "active_webhooks": self.active_webhooks,
            "secure_webhooks": self.secure_webhooks,
            "sent_events": self.sent_events,
            "failed_events": self.failed_events,
            "success_rate": success_rate,
            "security_rate": security_rate,
            "last_event_time": time.time() - random.randint(0, 300),
        }


class SecurityDashboardDemo:
    """Security dashboard demo med compliance monitoring"""

    def __init__(self):
        self.config = Config()
        self.logger = ScrapingLogger(__name__)

        # Skapa security scraper
        self.scraper = SecurityScraper()
        self.proxy_manager = MockProxyManager()
        self.webhook_manager = MockWebhookManager()

        # Dashboard med security features
        self.dashboard = DashboardApp(self.config)
        self.dashboard.set_components(
            scraper=self.scraper, proxy_manager=self.proxy_manager, webhook_manager=self.webhook_manager
        )

    async def start(self):
        """Startar security dashboard demo"""
        self.logger.info("🔒 Starting Security Dashboard Demo")

        # Starta security scraper
        await self.scraper.start()

        # Starta security scraping i bakgrunden
        scraping_thread = threading.Thread(target=self._run_security_scraping)
        scraping_thread.daemon = True
        scraping_thread.start()

        # Starta dashboard på port 8086
        self.logger.info("🌐 Starting Security Dashboard on http://127.0.0.1:8086")

        dashboard_thread = threading.Thread(target=self._run_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()

        await asyncio.sleep(3)

        self.logger.info("✅ Security Dashboard Demo started successfully!")
        self.logger.info("🔒 Open http://127.0.0.1:8086 to see security & compliance features")

    def _run_security_scraping(self):
        """Kör security scraping i bakgrunden"""
        urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml",
            "https://httpbin.org/headers",
            "https://httpbin.org/user-agent",
        ]

        while self.scraper.is_running:
            try:
                # Välj slumpmässig URL
                url = random.choice(urls)

                # Simulera security scraping
                asyncio.run(self.scraper.scrape_with_security(url))

                time.sleep(random.uniform(2, 5))

            except Exception as e:
                self.logger.error(f"Error in security scraping: {str(e)}")
                time.sleep(5)

    def _run_dashboard(self):
        """Kör dashboard på port 8086"""
        try:
            self.dashboard.run(host="127.0.0.1", port=8086)
        except Exception as e:
            self.logger.error(f"Dashboard error: {str(e)}")


async def main():
    """Huvudfunktion"""
    demo = SecurityDashboardDemo()
    await demo.start()

    # Håll igång
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await demo.scraper.stop()
        print("\n👋 Security Dashboard Demo stopped")


if __name__ == "__main__":
    asyncio.run(main())
