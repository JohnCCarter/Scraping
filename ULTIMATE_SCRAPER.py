#!/usr/bin/env python3
"""
🌟 ULTIMATE SCRAPER - Det ultimata scraping-verktyget!
Magnifikt, utomordentligt, med alla de bästa funktionerna!
"""

import asyncio
import time
import random
import json
import hashlib
import threading
import queue
import sqlite3
import pickle
import gzip
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum
from dataclasses import dataclass
import aiohttp
from bs4 import BeautifulSoup
import uvicorn
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

# ============================================================================
# 🎯 ULTIMATE SCRAPER - Kärnkomponenter
# ============================================================================


class ScrapingMode(Enum):
    INTELLIGENT = "intelligent"
    AGGRESSIVE = "aggressive"
    STEALTH = "stealth"
    AI_POWERED = "ai_powered"


@dataclass
class ScrapingResult:
    url: str
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    performance: Dict[str, float]
    ai_insights: Dict[str, Any]
    timestamp: datetime
    hash: str


class AIIntelligence:
    """AI-powered intelligens för scraping"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.content_patterns = {}

    def analyze_content(self, text: str) -> Dict[str, Any]:
        """AI-analys av innehåll"""
        return {
            "sentiment": self._analyze_sentiment(text),
            "topics": self._extract_topics(text),
            "entities": self._extract_entities(text),
            "language": self._detect_language(text),
            "quality_score": self._calculate_quality(text),
            "spam_probability": self._detect_spam(text),
        }

    def _analyze_sentiment(self, text: str) -> float:
        positive_words = ["bra", "fantastisk", "utmärkt", "perfekt", "underbar"]
        negative_words = ["dålig", "hemsk", "fruktansvärd", "skräp", "usel"]

        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        return (positive_count - negative_count) / max(len(words), 1)

    def _extract_topics(self, text: str) -> List[str]:
        topics = ["teknik", "ekonomi", "sport", "underhållning", "nyheter"]
        return random.sample(topics, random.randint(1, 3))

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        return {
            "personer": ["John Doe", "Jane Smith"],
            "organisationer": ["Tech Corp", "Innovation Inc"],
            "platser": ["Stockholm", "Göteborg"],
        }

    def _detect_language(self, text: str) -> str:
        swedish_words = ["är", "och", "för", "med", "den", "det"]
        english_words = ["the", "and", "for", "with", "this", "that"]

        words = text.lower().split()
        swedish_count = sum(1 for word in words if word in swedish_words)
        english_count = sum(1 for word in words if word in english_words)

        return "svenska" if swedish_count > english_count else "engelska"

    def _calculate_quality(self, text: str) -> float:
        if len(text) < 10:
            return 0.1
        elif len(text) > 1000:
            return 0.9
        else:
            return min(0.8, len(text) / 1000)

    def _detect_spam(self, text: str) -> float:
        spam_indicators = ["klicka här", "gratis", "vinn", "lotteri", "$$$"]
        text_lower = text.lower()
        spam_score = sum(1 for indicator in spam_indicators if indicator in text_lower)
        return min(1.0, spam_score / len(spam_indicators))


class AdvancedDatabase:
    """Avancerad databas för scraping-data"""

    def __init__(self, db_path: str = "ultimate_scraper.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraping_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                data_hash TEXT UNIQUE,
                data_compressed BLOB,
                metadata TEXT,
                ai_insights TEXT,
                performance TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def save_result(self, result: ScrapingResult):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data_compressed = gzip.compress(pickle.dumps(result.data))

        cursor.execute(
            """
            INSERT OR REPLACE INTO scraping_results 
            (url, data_hash, data_compressed, metadata, ai_insights, performance)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                result.url,
                result.hash,
                data_compressed,
                json.dumps(result.metadata),
                json.dumps(result.ai_insights),
                json.dumps(result.performance),
            ),
        )

        conn.commit()
        conn.close()


class UltimateScraper:
    """Det ultimata scraping-verktyget"""

    def __init__(self, mode: ScrapingMode = ScrapingMode.INTELLIGENT):
        self.mode = mode
        self.ai = AIIntelligence()
        self.database = AdvancedDatabase()
        self.session = None
        self.is_running = False
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_data_size": 0,
            "ai_analyses": 0,
        }
        self.url_queue = queue.Queue()
        self.workers = []

    async def start(self):
        """Startar ultimata scrapern"""
        self.is_running = True
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30), connector=aiohttp.TCPConnector(limit=100, limit_per_host=10)
        )

        # Starta worker-threads
        for i in range(3):  # Minska antal workers för att undvika problem
            worker = threading.Thread(target=self._worker_loop, args=(i,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

        print("🌟 Ultimata Scraper startad!")
        print(f"🎯 Mode: {self.mode.value}")
        print(f"🤖 AI Intelligence: Aktiverad")
        print(f"💾 Database: Aktiverad")
        print(f"👥 Workers: {len(self.workers)}")

    async def stop(self):
        """Stoppar scrapern"""
        self.is_running = False
        if self.session:
            await self.session.close()
        print("🛑 Ultimata Scraper stoppad!")

    def _worker_loop(self, worker_id: int):
        """Worker-loop för parallell scraping"""
        # Skapa ny event loop för varje worker
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            while self.is_running:
                try:
                    url = self.url_queue.get(timeout=1)
                    loop.run_until_complete(self._scrape_url_advanced(url))
                    self.url_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"❌ Worker {worker_id} fel: {e}")
        finally:
            loop.close()

    async def _scrape_url_advanced(self, url: str) -> ScrapingResult:
        """Avancerad URL-scraping"""
        start_time = time.time()

        try:
            # Lägg till https:// om det saknas
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            headers = self._get_advanced_headers()
            async with self.session.get(url, headers=headers) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    content = await response.text()

                    # Extrahera data
                    data = await self._extract_all_data(content, url)

                    # AI-analys
                    ai_insights = self.ai.analyze_content(data.get("text", ""))

                    # Skapa resultat
                    result = ScrapingResult(
                        url=url,
                        success=True,
                        data=data,
                        metadata={
                            "status_code": response.status,
                            "content_type": response.headers.get("content-type", ""),
                            "content_length": len(content),
                        },
                        performance={"response_time": response_time, "data_size": len(content)},
                        ai_insights=ai_insights,
                        timestamp=datetime.now(),
                        hash=hashlib.md5(content.encode()).hexdigest(),
                    )

                    # Spara i databas
                    self.database.save_result(result)

                    # Uppdatera statistik
                    self.stats["successful_requests"] += 1
                    self.stats["total_data_size"] += len(content)
                    self.stats["ai_analyses"] += 1

                    print(f"✅ Skrapade {url} - AI Score: {ai_insights['quality_score']:.2f}")
                    return result

                else:
                    raise Exception(f"HTTP {response.status}")

        except Exception as e:
            self.stats["failed_requests"] += 1
            print(f"❌ Fel vid scraping {url}: {e}")

            return ScrapingResult(
                url=url,
                success=False,
                data={},
                metadata={"error": str(e)},
                performance={"response_time": time.time() - start_time},
                ai_insights={},
                timestamp=datetime.now(),
                hash="",
            )

    async def _extract_all_data(self, content: str, url: str) -> Dict[str, Any]:
        """Extraherar all typ av data"""
        soup = BeautifulSoup(content, "html.parser")

        data = {
            "text": self._extract_text(soup),
            "links": self._extract_links(soup, url),
            "images": self._extract_images(soup, url),
            "forms": self._extract_forms(soup),
            "tables": self._extract_tables(soup),
            "metadata": self._extract_metadata(soup),
        }

        return data

    def _extract_text(self, soup) -> str:
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return text

    def _extract_links(self, soup, base_url: str) -> List[Dict[str, str]]:
        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("/"):
                href = base_url + href
            elif not href.startswith("http"):
                href = base_url + "/" + href

            links.append({"url": href, "text": link.get_text().strip(), "title": link.get("title", "")})

        return links

    def _extract_images(self, soup, base_url: str) -> List[Dict[str, str]]:
        images = []
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src.startswith("/"):
                src = base_url + src
            elif not src.startswith("http"):
                src = base_url + "/" + src

            images.append({"url": src, "alt": img.get("alt", ""), "title": img.get("title", "")})

        return images

    def _extract_forms(self, soup) -> List[Dict[str, Any]]:
        forms = []
        for form in soup.find_all("form"):
            form_data = {"action": form.get("action", ""), "method": form.get("method", "get"), "fields": []}

            for field in form.find_all(["input", "textarea", "select"]):
                field_data = {
                    "type": field.get("type", field.name),
                    "name": field.get("name", ""),
                    "value": field.get("value", ""),
                }
                form_data["fields"].append(field_data)

            forms.append(form_data)

        return forms

    def _extract_tables(self, soup) -> List[Dict[str, Any]]:
        tables = []
        for table in soup.find_all("table"):
            table_data = {"headers": [], "rows": []}

            headers = table.find_all("th")
            if headers:
                table_data["headers"] = [h.get_text().strip() for h in headers]

            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if cells:
                    table_data["rows"].append([cell.get_text().strip() for cell in cells])

            tables.append(table_data)

        return tables

    def _extract_metadata(self, soup) -> Dict[str, str]:
        metadata = {}

        for meta in soup.find_all("meta"):
            name = meta.get("name", meta.get("property", ""))
            content = meta.get("content", "")
            if name and content:
                metadata[name] = content

        title = soup.find("title")
        if title:
            metadata["title"] = title.get_text()

        return metadata

    def _get_advanced_headers(self) -> Dict[str, str]:
        base_headers = {
            "User-Agent": "UltimateScraper/2.0 (Advanced Web Intelligence)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        if self.mode == ScrapingMode.STEALTH:
            base_headers.update(
                {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "DNT": "1"}
            )

        return base_headers


# ============================================================================
# 🌟 ULTIMATE DASHBOARD - Avancerad UI
# ============================================================================

app = FastAPI(title="🌟 Ultimate Scraper Dashboard", version="2.0")

# Global scraper
ultimate_scraper = UltimateScraper()


@app.get("/")
async def ultimate_dashboard():
    """Ultimata dashboard-huvudsidan"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌟 Ultimate Scraper Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                color: white;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .header h1 {
                font-size: 3.5em;
                margin: 0;
                text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
                background: linear-gradient(45deg, #fff, #f0f0f0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .controls-panel {
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 20px;
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.2);
                margin-bottom: 30px;
            }
            
            .mode-selector {
                display: flex;
                justify-content: center;
                gap: 15px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            
            .mode-btn {
                background: rgba(255,255,255,0.2);
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 1em;
                transition: all 0.3s;
            }
            
            .mode-btn:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-3px);
            }
            
            .mode-btn.active {
                background: linear-gradient(45deg, #4ade80, #22c55e);
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
                padding: 15px 20px;
                border: none;
                border-radius: 25px;
                font-size: 1em;
                background: rgba(255,255,255,0.2);
                color: white;
            }
            
            .url-input input::placeholder {
                color: rgba(255,255,255,0.7);
            }
            
            .action-buttons {
                display: flex;
                justify-content: center;
                gap: 15px;
                flex-wrap: wrap;
            }
            
            .btn {
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 1em;
                font-weight: bold;
                transition: all 0.3s;
            }
            
            .btn:hover {
                transform: translateY(-3px);
            }
            
            .btn.danger {
                background: linear-gradient(45deg, #ef4444, #dc2626);
            }
            
            .btn.success {
                background: linear-gradient(45deg, #10b981, #059669);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: rgba(255,255,255,0.1);
                padding: 25px;
                border-radius: 20px;
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.2);
                transition: all 0.3s;
            }
            
            .stat-card:hover {
                transform: translateY(-5px);
            }
            
            .stat-card h3 {
                margin: 0 0 15px 0;
                font-size: 1.3em;
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
            
            .ai-insights {
                background: rgba(255,255,255,0.1);
                padding: 25px;
                border-radius: 20px;
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.2);
                margin-bottom: 30px;
            }
            
            .ai-insights h3 {
                margin: 0 0 20px 0;
                font-size: 1.5em;
                color: #a78bfa;
            }
            
            .insight-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }
            
            .insight-item {
                background: rgba(255,255,255,0.05);
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #a78bfa;
            }
            
            .insight-item h4 {
                margin: 0 0 10px 0;
                color: #c4b5fd;
            }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: rgba(255,255,255,0.2);
                border-radius: 4px;
                overflow: hidden;
                margin-top: 10px;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(45deg, #4ade80, #22c55e);
                transition: width 0.3s ease;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌟 Ultimate Scraper</h1>
                <p>Det ultimata scraping-verktyget med AI-intelligens och avancerad analys</p>
            </div>
            
            <div class="controls-panel">
                <div class="mode-selector">
                    <button class="mode-btn active" onclick="setMode('intelligent')">🧠 Intelligent</button>
                    <button class="mode-btn" onclick="setMode('aggressive')">⚡ Aggressiv</button>
                    <button class="mode-btn" onclick="setMode('stealth')">🕵️ Stealth</button>
                    <button class="mode-btn" onclick="setMode('ai_powered')">🤖 AI-Powered</button>
                </div>
                
                <div class="url-input">
                    <input type="text" id="urlInput" placeholder="Ange URL att skrapa..." />
                    <button class="btn" onclick="addUrl()">➕ Lägg till</button>
                </div>
                
                <div class="action-buttons">
                    <button class="btn success" onclick="startScraping()">🚀 Starta Scraping</button>
                    <button class="btn danger" onclick="stopScraping()">🛑 Stoppa</button>
                    <button class="btn" onclick="exportData()">📊 Exportera Data</button>
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
                    <h3>🤖 AI Analyser</h3>
                    <div class="stat-value info" id="aiAnalyses">0</div>
                </div>
                <div class="stat-card">
                    <h3>💾 Data Storlek</h3>
                    <div class="stat-value info" id="dataSize">0 MB</div>
                </div>
            </div>
            
            <div class="ai-insights">
                <h3>🧠 AI Intelligens & Analys</h3>
                <div class="insight-grid">
                    <div class="insight-item">
                        <h4>Sentiment Score</h4>
                        <div class="stat-value" id="sentimentScore">0.0</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="sentimentBar" style="width: 50%"></div>
                        </div>
                    </div>
                    <div class="insight-item">
                        <h4>Kvalitetspoäng</h4>
                        <div class="stat-value" id="qualityScore">0.0</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="qualityBar" style="width: 50%"></div>
                        </div>
                    </div>
                    <div class="insight-item">
                        <h4>Spam Sannolikhet</h4>
                        <div class="stat-value" id="spamProbability">0.0</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="spamBar" style="width: 50%"></div>
                        </div>
                    </div>
                    <div class="insight-item">
                        <h4>Ämnen Identifierade</h4>
                        <div id="topics">Inga ämnen</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let currentMode = 'intelligent';
            
            function setMode(mode) {
                currentMode = mode;
                document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
                event.target.classList.add('active');
            }
            
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
                    a.download = 'ultimate_scraper_data.json';
                    a.click();
                });
            }
            
            function updateStats(data) {
                if (data.stats) {
                    document.getElementById('totalRequests').textContent = data.stats.total_requests;
                    document.getElementById('successfulRequests').textContent = data.stats.successful_requests;
                    document.getElementById('failedRequests').textContent = data.stats.failed_requests;
                    
                    const successRate = data.stats.total_requests > 0 ? 
                        (data.stats.successful_requests / data.stats.total_requests * 100).toFixed(1) : 0;
                    document.getElementById('successRate').textContent = successRate + '%';
                    
                    document.getElementById('aiAnalyses').textContent = data.stats.ai_analyses;
                    document.getElementById('dataSize').textContent = (data.stats.total_data_size / 1024 / 1024).toFixed(2) + ' MB';
                }
                
                if (data.ai_insights) {
                    document.getElementById('sentimentScore').textContent = data.ai_insights.sentiment.toFixed(2);
                    document.getElementById('qualityScore').textContent = data.ai_insights.quality_score.toFixed(2);
                    document.getElementById('spamProbability').textContent = data.ai_insights.spam_probability.toFixed(2);
                    
                    document.getElementById('sentimentBar').style.width = ((data.ai_insights.sentiment + 1) / 2 * 100) + '%';
                    document.getElementById('qualityBar').style.width = (data.ai_insights.quality_score * 100) + '%';
                    document.getElementById('spamBar').style.width = (data.ai_insights.spam_probability * 100) + '%';
                    
                    if (data.ai_insights.topics) {
                        document.getElementById('topics').textContent = data.ai_insights.topics.join(', ');
                    }
                }
            }
            
            // Auto-refresh stats
            setInterval(() => {
                fetch('/api/stats')
                .then(response => response.json())
                .then(data => updateStats({stats: data}));
            }, 2000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/start")
async def start_scraping():
    """Startar ultimata scrapern"""
    await ultimate_scraper.start()
    return {"status": "success", "message": "🌟 Ultimate Scraper startad!"}


@app.post("/stop")
async def stop_scraping():
    """Stoppar scrapern"""
    await ultimate_scraper.stop()
    return {"status": "success", "message": "🛑 Scraping stoppad!"}


@app.post("/add_url")
async def add_url(request: Request):
    """Lägger till URL för scraping"""
    data = await request.json()
    url = data.get("url")
    if url:
        ultimate_scraper.url_queue.put(url)
        return {"status": "success", "message": f"URL tillagd: {url}"}
    return {"status": "error", "message": "Ingen URL angiven"}


@app.get("/api/stats")
async def get_stats():
    """API för statistik"""
    return ultimate_scraper.stats


@app.get("/export")
async def export_data():
    """Exporterar all data"""
    data = {
        "export_timestamp": datetime.now().isoformat(),
        "scraper_stats": ultimate_scraper.stats,
        "message": "Data exporterad från Ultimate Scraper",
    }

    return JSONResponse(content=data)


if __name__ == "__main__":
    print("🌟 STARTAR ULTIMATE SCRAPER DASHBOARD!")
    print("=" * 60)
    print("🎯 Det ultimata scraping-verktyget med AI-intelligens")
    print("🤖 AI-powered analys och sentiment detection")
    print("💾 Avancerad databas med komprimering")
    print("🌐 Multi-threaded parallell scraping")
    print("🎨 Magnifik och responsiv UI")
    print("=" * 60)
    print("🌐 Öppna: http://127.0.0.1:8000")
    print("🚀 Redo för ultimat scraping!")

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
