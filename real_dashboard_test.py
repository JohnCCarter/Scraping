#!/usr/bin/env python3
"""
🚀 REAL DASHBOARD - Enkel och fungerande scraper!
"""

import time
import json
import hashlib
import sqlite3
import threading
import queue
from datetime import datetime
from typing import Dict, Any, List
import requests
from bs4 import BeautifulSoup
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="🚀 Real Dashboard", version="1.0")


class SimpleScraper:
    """Enkel och fungerande scraper"""

    def __init__(self):
        self.is_running = False
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_data_size": 0,
        }
        self.url_queue = queue.Queue()
        self.worker_thread = None
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

        # Initiera databas
        self.init_database()

    def init_database(self):
        """Initierar SQLite-databas"""
        conn = sqlite3.connect("scraper_data.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraped_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                text_content TEXT,
                links_count INTEGER,
                images_count INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.commit()
        conn.close()

    def start(self):
        """Startar scrapern"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop)
            self.worker_thread.daemon = True
            self.worker_thread.start()
            print("🚀 Scraper startad!")

    def stop(self):
        """Stoppar scrapern"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1)
        print("🛑 Scraper stoppad!")

    def add_url(self, url: str):
        """Lägger till URL för scraping"""
        self.url_queue.put(url)
        print(f"➕ URL tillagd: {url}")

    def _worker_loop(self):
        """Worker-loop som körs i separat tråd"""
        while self.is_running:
            try:
                url = self.url_queue.get(timeout=1)
                self._scrape_url(url)
                self.url_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Fel i worker: {e}")

    def _scrape_url(self, url: str):
        """Skrapar en URL"""
        self.stats["total_requests"] += 1

        try:
            # Lägg till https:// om det saknas
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            print(f"🌐 Skrapar: {url}")

            # Gör HTTP-request
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")

            # Extrahera data
            title = soup.find("title")
            title_text = title.get_text().strip() if title else "Ingen titel"

            # Extrahera text
            for script in soup(["script", "style"]):
                script.decompose()
            text_content = soup.get_text()
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = " ".join(chunk for chunk in chunks if chunk)

            # Räkna länkar och bilder
            links_count = len(soup.find_all("a"))
            images_count = len(soup.find_all("img"))

            # Spara i databas
            self._save_to_database(url, title_text, text_content, links_count, images_count)

            # Uppdatera statistik
            self.stats["successful_requests"] += 1
            self.stats["total_data_size"] += len(response.content)

            print(f"✅ Framgångsrik: {url} - {title_text[:50]}...")

        except Exception as e:
            self.stats["failed_requests"] += 1
            print(f"❌ Fel vid scraping {url}: {e}")

    def _save_to_database(
        self,
        url: str,
        title: str,
        text_content: str,
        links_count: int,
        images_count: int,
    ):
        """Sparar data i databas"""
        conn = sqlite3.connect("scraper_data.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO scraped_data (url, title, text_content, links_count, images_count)
            VALUES (?, ?, ?, ?, ?)
        """,
            (url, title, text_content[:1000], links_count, images_count),
        )
        conn.commit()
        conn.close()

    def get_stats(self):
        """Returnerar statistik"""
        return self.stats.copy()


# Global scraper-instans
scraper = SimpleScraper()


@app.get("/")
async def dashboard():
    """Dashboard-huvudsidan"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🚀 Real Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .header h1 {
                font-size: 3em;
                margin: 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .controls {
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                margin-bottom: 30px;
            }
            
            .url-input {
                display: flex;
                gap: 15px;
                margin-bottom: 20px;
                justify-content: center;
            }
            
            .url-input input {
                flex: 1;
                max-width: 500px;
                padding: 15px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                background: rgba(255,255,255,0.2);
                color: white;
            }
            
            .url-input input::placeholder {
                color: rgba(255,255,255,0.7);
            }
            
            .buttons {
                display: flex;
                justify-content: center;
                gap: 15px;
                flex-wrap: wrap;
            }
            
            .btn {
                background: linear-gradient(45deg, #4ade80, #22c55e);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 10px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                transition: all 0.3s;
            }
            
            .btn:hover {
                transform: translateY(-2px);
            }
            
            .btn.danger {
                background: linear-gradient(45deg, #ef4444, #dc2626);
            }
            
            .btn.secondary {
                background: linear-gradient(45deg, #3b82f6, #2563eb);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: rgba(255,255,255,0.1);
                padding: 25px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                text-align: center;
                transition: all 0.3s;
            }
            
            .stat-card:hover {
                transform: translateY(-5px);
            }
            
            .stat-card h3 {
                margin: 0 0 15px 0;
                font-size: 1.2em;
                color: #fbbf24;
            }
            
            .stat-value {
                font-size: 2.5em;
                font-weight: bold;
                margin: 10px 0;
            }
            
            .success { color: #4ade80; }
            .error { color: #f87171; }
            .info { color: #60a5fa; }
            
            .demo-urls {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                margin-top: 20px;
            }
            
            .demo-urls h3 {
                margin: 0 0 15px 0;
                color: #fbbf24;
            }
            
            .demo-urls button {
                background: rgba(255,255,255,0.2);
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
                transition: all 0.3s;
            }
            
            .demo-urls button:hover {
                background: rgba(255,255,255,0.3);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Real Dashboard</h1>
                <p>Enkel och fungerande web scraper</p>
            </div>
            
            <div class="controls">
                <div class="url-input">
                    <input type="text" id="urlInput" placeholder="Ange URL att skrapa..." />
                    <button class="btn" onclick="addUrl()">➕ Lägg till</button>
                </div>
                
                <div class="buttons">
                    <button class="btn" onclick="startScraping()">🚀 Starta Scraping</button>
                    <button class="btn danger" onclick="stopScraping()">🛑 Stoppa</button>
                    <button class="btn secondary" onclick="exportData()">📊 Exportera</button>
                </div>
                
                <div class="demo-urls">
                    <h3>🎯 Testa med dessa URLs:</h3>
                    <button onclick="addDemoUrl('httpbin.org/html')">httpbin.org/html</button>
                    <button onclick="addDemoUrl('example.com')">example.com</button>
                    <button onclick="addDemoUrl('httpbin.org/json')">httpbin.org/json</button>
                    <button onclick="addDemoUrl('httpbin.org/headers')">httpbin.org/headers</button>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>📊 Total Requests</h3>
                    <div class="stat-value info" id="totalRequests">0</div>
                </div>
                <div class="stat-card">
                    <h3>✅ Framgångsrika</h3>
                    <div class="stat-value success" id="successfulRequests">0</div>
                </div>
                <div class="stat-card">
                    <h3>❌ Misslyckade</h3>
                    <div class="stat-value error" id="failedRequests">0</div>
                </div>
                <div class="stat-card">
                    <h3>📈 Framgångsgrad</h3>
                    <div class="stat-value success" id="successRate">0%</div>
                </div>
                <div class="stat-card">
                    <h3>💾 Data Storlek</h3>
                    <div class="stat-value info" id="dataSize">0 KB</div>
                </div>
            </div>
        </div>
        
        <script>
            function addUrl() {
                const url = document.getElementById('urlInput').value;
                if (url) {
                    fetch('/add_url', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({url: url})
                    });
                    document.getElementById('urlInput').value = '';
                }
            }
            
            function addDemoUrl(url) {
                document.getElementById('urlInput').value = url;
                addUrl();
            }
            
            function startScraping() {
                fetch('/start', {method: 'POST'});
            }
            
            function stopScraping() {
                fetch('/stop', {method: 'POST'});
            }
            
            function exportData() {
                fetch('/export')
                .then(response => response.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'scraper_data.json';
                    a.click();
                });
            }
            
            function updateStats(data) {
                document.getElementById('totalRequests').textContent = data.total_requests;
                document.getElementById('successfulRequests').textContent = data.successful_requests;
                document.getElementById('failedRequests').textContent = data.failed_requests;
                
                const successRate = data.total_requests > 0 ? 
                    (data.successful_requests / data.total_requests * 100).toFixed(1) : 0;
                document.getElementById('successRate').textContent = successRate + '%';
                
                const dataSizeKB = (data.total_data_size / 1024).toFixed(1);
                document.getElementById('dataSize').textContent = dataSizeKB + ' KB';
            }
            
            // Auto-refresh stats var 2:e sekund
            setInterval(() => {
                fetch('/api/stats')
                .then(response => response.json())
                .then(data => updateStats(data));
            }, 2000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/start")
async def start_scraping():
    """Startar scrapern"""
    scraper.start()
    return {"status": "success", "message": "🚀 Scraping startad!"}


@app.post("/stop")
async def stop_scraping():
    """Stoppar scrapern"""
    scraper.stop()
    return {"status": "success", "message": "🛑 Scraping stoppad!"}


@app.post("/add_url")
async def add_url(request: Request):
    """Lägger till URL för scraping"""
    data = await request.json()
    url = data.get("url")
    if url:
        scraper.add_url(url)
        return {"status": "success", "message": f"URL tillagd: {url}"}
    return {"status": "error", "message": "Ingen URL angiven"}


@app.get("/api/stats")
async def get_stats():
    """API för statistik"""
    return scraper.get_stats()


@app.get("/export")
async def export_data():
    """Exporterar data från databas"""
    conn = sqlite3.connect("scraper_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scraped_data ORDER BY timestamp DESC LIMIT 100")
    rows = cursor.fetchall()
    conn.close()

    data = {
        "export_timestamp": datetime.now().isoformat(),
        "total_records": len(rows),
        "records": [
            {
                "url": row[1],
                "title": row[2],
                "text_preview": row[3][:200] + "..." if len(row[3]) > 200 else row[3],
                "links_count": row[4],
                "images_count": row[5],
                "timestamp": row[6],
            }
            for row in rows
        ],
    }

    return JSONResponse(content=data)


if __name__ == "__main__":
    print("🚀 STARTAR REAL DASHBOARD!")
    print("=" * 50)
    print("🎯 Enkel och fungerande web scraper")
    print("🌐 Öppna: http://127.0.0.1:8080")
    print("=" * 50)

    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
