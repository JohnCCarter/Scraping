#!/usr/bin/env python3
"""
Test för dashboard-fix
"""

import asyncio
import time
import random
from typing import Dict, Any


class MockScraper:
    """Mock scraper för demo-data"""

    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()

    def get_metrics(self) -> Dict[str, Any]:
        """Returnerar mock metrics"""
        return {
            "requests_total": self.request_count,
            "requests_success": self.success_count,
            "requests_error": self.error_count,
            "success_rate": (self.success_count / max(self.request_count, 1)) * 100,
            "uptime_seconds": time.time() - self.start_time,
            "current_rate": random.randint(10, 50),
            "active_sessions": random.randint(1, 5),
            "is_running": True,  # Detta fixar "Offline" problemet
            "requests_per_minute": random.randint(10, 50),  # Detta behövs för JavaScript
        }

    def simulate_request(self):
        """Simulerar en request"""
        self.request_count += 1
        if random.random() > 0.1:
            self.success_count += 1
        else:
            self.error_count += 1


async def test_mock_data():
    """Testar mock-data"""
    scraper = MockScraper()

    # Simulera några requests
    for _ in range(5):
        scraper.simulate_request()

    metrics = scraper.get_metrics()
    print("🔧 TEST AV MOCK-DATA:")
    print(f"is_running: {metrics.get('is_running', 'MISSING')}")
    print(f"requests_per_minute: {metrics.get('requests_per_minute', 'MISSING')}")
    print(f"success_rate: {metrics.get('success_rate', 'MISSING')}%")
    print(f"requests_total: {metrics.get('requests_total', 'MISSING')}")

    # Kontrollera att alla nödvändiga fält finns
    required_fields = ["is_running", "requests_per_minute", "success_rate"]
    missing_fields = [field for field in required_fields if field not in metrics]

    if missing_fields:
        print(f"❌ MISSING FIELDS: {missing_fields}")
    else:
        print("✅ ALLA FÄLT FINNS!")


if __name__ == "__main__":
    asyncio.run(test_mock_data())
