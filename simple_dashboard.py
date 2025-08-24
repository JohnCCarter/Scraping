#!/usr/bin/env python3
"""
🚀 ENKEL DASHBOARD - Bara fungerar!
"""

import asyncio
import time
import random
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import aiohttp
from bs4 import BeautifulSoup
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import threading

# Skapa FastAPI app
app = FastAPI(title="🚀 Enkel Dashboard", version="1.0")


# Simulerad data för dashboard
class DashboardData:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.scraped_urls = []
        self.latest_data = []

    def add_request(self, success=True):
        self.request_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def get_stats(self):
        uptime = time.time() - self.start_time
        success_rate = (self.success_count / self.request_count * 100) if self.request_count > 0 else 0

        return {
            "uptime": int(uptime),
            "requests": self.request_count,
            "success": self.success_count,
            "errors": self.error_count,
            "success_rate": round(success_rate, 1),
            "scraped_urls": len(self.scraped_urls),
        }


# Global data
dashboard_data = DashboardData()


# Simulerad scraper
class SimpleScraper:
    def __init__(self):
        self.is_running = False
        self.session = None

    async def start(self):
        """Startar scraper"""
        self.is_running = True
        self.session = aiohttp.ClientSession()
        print("🚀 Scraper startad!")

    async def stop(self):
        """Stoppar scraper"""
        self.is_running = False
        if self.session:
            await self.session.close()
        print("🛑 Scraper stoppad!")

    async def scrape_demo_urls(self):
        """Skrapar demo URLs"""
        demo_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml",
            "https://httpbin.org/headers",
            "https://httpbin.org/user-agent",
        ]

        while self.is_running:
            try:
                url = random.choice(demo_urls)
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, "html.parser")

                        # Extrahera data
                        title = soup.find("title")
                        title_text = title.get_text() if title else "No title"

                        # Lägg till i data
                        dashboard_data.add_request(success=True)
                        dashboard_data.scraped_urls.append(
                            {
                                "url": url,
                                "title": title_text,
                                "timestamp": datetime.now().isoformat(),
                                "status": response.status,
                            }
                        )

                        # Begränsa antal sparade URLs
                        if len(dashboard_data.scraped_urls) > 50:
                            dashboard_data.scraped_urls = dashboard_data.scraped_urls[-50:]

                        print(f"✅ Skrapade {url} - {title_text}")

                    else:
                        dashboard_data.add_request(success=False)
                        print(f"❌ Fel vid scraping {url}: {response.status}")

            except Exception as e:
                dashboard_data.add_request(success=False)
                print(f"❌ Fel: {e}")

            # Vänta lite mellan requests
            await asyncio.sleep(random.uniform(2, 5))


# Skapa scraper
scraper = SimpleScraper()


# API endpoints
@app.get("/")
async def dashboard():
    """Huvudsida"""
    stats = dashboard_data.get_stats()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🚀 Enkel Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
            }}
            .header h1 {{
                font-size: 3em;
                margin: 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }}
            .stat-card {{
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }}
            .stat-card h3 {{
                margin: 0 0 10px 0;
                font-size: 1.2em;
            }}
            .stat-value {{
                font-size: 2em;
                font-weight: bold;
                margin: 10px 0;
            }}
            .success {{ color: #4ade80; }}
            .error {{ color: #f87171; }}
            .info {{ color: #60a5fa; }}
            .urls-section {{
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }}
            .url-item {{
                padding: 10px;
                margin: 5px 0;
                background: rgba(255,255,255,0.05);
                border-radius: 5px;
                border-left: 4px solid #4ade80;
            }}
            .controls {{
                text-align: center;
                margin: 20px 0;
            }}
            .btn {{
                background: rgba(255,255,255,0.2);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 25px;
                cursor: pointer;
                margin: 0 10px;
                font-size: 1em;
                transition: all 0.3s;
            }}
            .btn:hover {{
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
            }}
            .btn:active {{
                transform: translateY(0);
            }}
            .status {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: bold;
            }}
            .status.running {{
                background: #4ade80;
                color: #064e3b;
            }}
            .status.stopped {{
                background: #f87171;
                color: #7f1d1d;
            }}
            @media (max-width: 768px) {{
                .stats-grid {{
                    grid-template-columns: 1fr;
                }}
                .header h1 {{
                    font-size: 2em;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Enkel Dashboard</h1>
                <p>Web scraping dashboard som bara fungerar!</p>
            </div>
            
            <div class="controls">
                <button class="btn" onclick="toggleScraper()">
                    {'🛑 Stoppa' if scraper.is_running else '🚀 Starta'} Scraper
                </button>
                <span class="status {'running' if scraper.is_running else 'stopped'}">
                    {'🟢 Körs' if scraper.is_running else '🔴 Stoppad'}
                </span>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>⏱️ Uptime</h3>
                    <div class="stat-value info">{stats['uptime']}s</div>
                </div>
                <div class="stat-card">
                    <h3>📊 Requests</h3>
                    <div class="stat-value info">{stats['requests']}</div>
                </div>
                <div class="stat-card">
                    <h3>✅ Framgångsrika</h3>
                    <div class="stat-value success">{stats['success']}</div>
                </div>
                <div class="stat-card">
                    <h3>❌ Fel</h3>
                    <div class="stat-value error">{stats['errors']}</div>
                </div>
                <div class="stat-card">
                    <h3>📈 Framgångsgrad</h3>
                    <div class="stat-value success">{stats['success_rate']}%</div>
                </div>
                <div class="stat-card">
                    <h3>🌐 Skrapade URLs</h3>
                    <div class="stat-value info">{stats['scraped_urls']}</div>
                </div>
            </div>
            
            <div class="urls-section">
                <h3>📋 Senaste skrapade URLs</h3>
                <div id="urls-list">
                    {''.join([f'<div class="url-item"><strong>{item["url"]}</strong><br><small>{item["title"]} - {item["timestamp"]}</small></div>' for item in dashboard_data.scraped_urls[-10:]])}
                </div>
            </div>
        </div>
        
        <script>
            // Auto-refresh var 5:e sekund
            setInterval(() => {{
                location.reload();
            }}, 5000);
            
            async function toggleScraper() {{
                const response = await fetch('/toggle', {{
                    method: 'POST'
                }});
                location.reload();
            }}
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html)


@app.post("/toggle")
async def toggle_scraper():
    """Startar/stoppar scraper"""
    if scraper.is_running:
        await scraper.stop()
    else:
        await scraper.start()
        # Starta scraping i bakgrunden
        asyncio.create_task(scraper.scrape_demo_urls())

    return {"status": "success", "running": scraper.is_running}


@app.get("/api/stats")
async def get_stats():
    """API för statistik"""
    return dashboard_data.get_stats()


@app.get("/api/urls")
async def get_urls():
    """API för skrapade URLs"""
    return dashboard_data.scraped_urls


# Starta scraper automatiskt
@app.on_event("startup")
async def startup_event():
    """Startar scraper när servern startar"""
    await scraper.start()
    asyncio.create_task(scraper.scrape_demo_urls())


# Stoppa scraper när servern stängs
@app.on_event("shutdown")
async def shutdown_event():
    """Stoppar scraper när servern stängs"""
    await scraper.stop()


if __name__ == "__main__":
    print("🚀 Startar Enkel Dashboard...")
    print("🌐 Öppna: http://127.0.0.1:8080")
    print("📊 Dashboard med live statistik och auto-refresh")
    print("🎯 En fil, enkel att använda, bara fungerar!")

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
