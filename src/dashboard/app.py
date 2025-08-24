"""
Web-baserat dashboard för visualisering av scraping-metrics
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from ..utils.config import Config
from ..scraper.core import WebScraper
from ..scraper.distributed import DistributedScraper
from ..scraper.proxy_manager import ProxyManager
from ..scraper.webhooks import WebhookManager


class DashboardConfig(BaseModel):
    """Konfiguration för dashboard"""

    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    title: str = "Web Scraping Dashboard"
    refresh_interval: int = 5000  # ms


class DashboardApp:
    """
    Web-baserat dashboard för scraping-metrics
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = structlog.get_logger(__name__)

        # Dashboard-konfiguration
        self.dashboard_config = DashboardConfig(
            host=self.config.get("dashboard.host", "0.0.0.0"),
            port=self.config.get("dashboard.port", 8080),
            debug=self.config.get("dashboard.debug", False),
            title=self.config.get("dashboard.title", "Web Scraping Dashboard"),
            refresh_interval=self.config.get("dashboard.refresh_interval", 5000),
        )

        # FastAPI-app
        self.app = FastAPI(title=self.dashboard_config.title)

        # WebSocket-anslutningar
        self.active_connections: List[WebSocket] = []

        # Komponenter
        self.scraper: Optional[WebScraper] = None
        self.distributed_scraper: Optional[DistributedScraper] = None
        self.proxy_manager: Optional[ProxyManager] = None
        self.webhook_manager: Optional[WebhookManager] = None

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Sätter upp API-routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            """Huvudsida för dashboard"""
            return self._get_dashboard_html()

        @self.app.get("/api/stats")
        async def get_stats():
            """Hämtar aktuell statistik"""
            return await self._get_current_stats()

        @self.app.get("/api/scraping/stats")
        async def get_scraping_stats():
            """Hämtar scraping-statistik"""
            if self.scraper:
                return self.scraper.get_metrics()
            return {}

        @self.app.get("/api/distributed/stats")
        async def get_distributed_stats():
            """Hämtar distribuerad scraping-statistik"""
            if self.distributed_scraper:
                return await self.distributed_scraper.get_queue_stats()
            return {}

        @self.app.get("/api/proxy/stats")
        async def get_proxy_stats():
            """Hämtar proxy-statistik"""
            if self.proxy_manager:
                return self.proxy_manager.get_stats()
            return {}

        @self.app.get("/api/webhook/stats")
        async def get_webhook_stats():
            """Hämtar webhook-statistik"""
            if self.webhook_manager:
                return self.webhook_manager.get_stats()
            return {}

        @self.app.get("/api/proxy/details")
        async def get_proxy_details():
            """Hämtar detaljerad proxy-information"""
            if self.proxy_manager:
                return self.proxy_manager.get_proxy_details()
            return []

        @self.app.get("/api/webhook/list")
        async def get_webhook_list():
            """Hämtar webhook-lista"""
            if self.webhook_manager:
                return self.webhook_manager.get_webhooks()
            return []

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket-endpoint för real-time updates"""
            await websocket.accept()
            self.active_connections.append(websocket)

            try:
                while True:
                    # Skicka uppdateringar var 5:e sekund
                    stats = await self._get_current_stats()
                    await websocket.send_text(json.dumps(stats))
                    await asyncio.sleep(5)

            except WebSocketDisconnect:
                self.active_connections.remove(websocket)

    def _get_dashboard_html(self) -> str:
        """Returnerar HTML för avancerad dashboard"""
        try:
            with open("security_dashboard.html", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            try:
                with open("mobile_dashboard.html", "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                try:
                    with open("ai_dashboard.html", "r", encoding="utf-8") as f:
                        return f.read()
                except FileNotFoundError:
                    try:
                        with open("control_dashboard.html", "r", encoding="utf-8") as f:
                            return f.read()
                    except FileNotFoundError:
                        try:
                            with open("advanced_dashboard.html", "r", encoding="utf-8") as f:
                                return f.read()
                        except FileNotFoundError:
                            # Fallback till enkel version om avancerad HTML inte finns
                            return self._get_simple_dashboard_html()

    def _get_simple_dashboard_html(self) -> str:
        """Fallback till enkel dashboard HTML"""
        return f"""
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.dashboard_config.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .stat-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .status-online {{ background-color: #4CAF50; }}
        .status-offline {{ background-color: #f44336; }}
        .status-warning {{ background-color: #ff9800; }}
        .refresh-info {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.dashboard_config.title}</h1>
            <p>Real-time monitoring av web scraping-aktiviteter</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">Scraping Status</div>
                <div class="stat-value" id="scraping-status">
                    <span class="status-indicator status-offline"></span>
                    Offline
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Requests/Minut</div>
                <div class="stat-value" id="requests-per-minute">0</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Success Rate</div>
                <div class="stat-value" id="success-rate">0%</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Active Proxies</div>
                <div class="stat-value" id="active-proxies">0</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Queue Size</div>
                <div class="stat-value" id="queue-size">0</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Active Webhooks</div>
                <div class="stat-value" id="active-webhooks">0</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>Request Activity (Senaste 30 minuter)</h3>
            <canvas id="requestChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>Success Rate Over Time</h3>
            <canvas id="successChart" width="400" height="200"></canvas>
        </div>
        
        <div class="refresh-info">
            Uppdateras automatiskt var {self.dashboard_config.refresh_interval/1000} sekund
        </div>
    </div>
    
    <script>
        // Chart.js konfiguration
        const requestChart = new Chart(document.getElementById('requestChart'), {{
            type: 'line',
            data: {{
                labels: [],
                datasets: [{{
                    label: 'Requests/min',
                    data: [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
        
        const successChart = new Chart(document.getElementById('successChart'), {{
            type: 'line',
            data: {{
                labels: [],
                datasets: [{{
                    label: 'Success Rate %',
                    data: [],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100
                    }}
                }}
            }}
        }});
        
        // WebSocket-anslutning för real-time updates
        const ws = new WebSocket(`ws://${{window.location.host}}/ws`);
        
        ws.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            updateDashboard(data);
        }};
        
        function updateDashboard(data) {{
            // Uppdatera statistik
            document.getElementById('requests-per-minute').textContent = 
                data.scraping?.requests_per_minute || 0;
            
            document.getElementById('success-rate').textContent = 
                Math.round(data.scraping?.success_rate || 0) + '%';
            
            document.getElementById('active-proxies').textContent = 
                data.proxy?.active_proxies || 0;
            
            document.getElementById('queue-size').textContent = 
                data.distributed?.pending_tasks || 0;
            
            document.getElementById('active-webhooks').textContent = 
                data.webhook?.active_webhooks || 0;
            
            // Uppdatera status
            const statusElement = document.getElementById('scraping-status');
            const statusIndicator = statusElement.querySelector('.status-indicator');
            
            if (data.scraping?.is_running) {{
                statusElement.innerHTML = '<span class="status-indicator status-online"></span>Online';
            }} else {{
                statusElement.innerHTML = '<span class="status-indicator status-offline"></span>Offline';
            }}
            
            // Uppdatera charts
            updateCharts(data);
        }}
        
        function updateCharts(data) {{
            const now = new Date();
            const timeLabel = now.toLocaleTimeString();
            
            // Request chart
            requestChart.data.labels.push(timeLabel);
            requestChart.data.datasets[0].data.push(data.scraping?.requests_per_minute || 0);
            
            if (requestChart.data.labels.length > 30) {{
                requestChart.data.labels.shift();
                requestChart.data.datasets[0].data.shift();
            }}
            
            requestChart.update();
            
            // Success chart
            successChart.data.labels.push(timeLabel);
            successChart.data.datasets[0].data.push(
                Math.round(data.scraping?.success_rate || 0)
            );
            
            if (successChart.data.labels.length > 30) {{
                successChart.data.labels.shift();
                successChart.data.datasets[0].data.shift();
            }}
            
            successChart.update();
        }}
        
        // Initial load
        async function loadInitialData() {{
            try {{
                const response = await axios.get('/api/stats');
                updateDashboard(response.data);
            }} catch (error) {{
                console.error('Error loading initial data:', error);
            }}
        }}
        
        loadInitialData();
    </script>
</body>
</html>
        """

    async def _get_current_stats(self) -> Dict[str, Any]:
        """Hämtar aktuell statistik från alla komponenter"""
        stats = {"timestamp": time.time(), "scraping": {}, "distributed": {}, "proxy": {}, "webhook": {}}

        # Scraping-statistik
        if self.scraper:
            stats["scraping"] = self.scraper.get_metrics()

        # Distribuerad scraping-statistik
        if self.distributed_scraper:
            stats["distributed"] = await self.distributed_scraper.get_queue_stats()

        # Proxy-statistik
        if self.proxy_manager:
            stats["proxy"] = self.proxy_manager.get_stats()

        # Webhook-statistik
        if self.webhook_manager:
            stats["webhook"] = self.webhook_manager.get_stats()

        return stats

    def set_components(
        self,
        scraper: Optional[WebScraper] = None,
        distributed_scraper: Optional[DistributedScraper] = None,
        proxy_manager: Optional[ProxyManager] = None,
        webhook_manager: Optional[WebhookManager] = None,
    ):
        """Sätter komponenter för dashboard"""
        self.scraper = scraper
        self.distributed_scraper = distributed_scraper
        self.proxy_manager = proxy_manager
        self.webhook_manager = webhook_manager

        self.logger.info("Dashboard components configured")

    async def broadcast_update(self, data: Dict[str, Any]):
        """Skickar uppdatering till alla WebSocket-anslutningar"""
        if not self.active_connections:
            return

        message = json.dumps(data)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.error(f"Error sending to WebSocket: {str(e)}")
                disconnected.append(connection)

        # Ta bort frånkopplade anslutningar
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)

    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """Startar dashboard-servern"""
        host = host or self.dashboard_config.host
        port = port or self.dashboard_config.port

        self.logger.info(f"Starting dashboard on {host}:{port}")

        uvicorn.run(self.app, host=host, port=port, log_level="info" if self.dashboard_config.debug else "warning")

    async def start_background(self):
        """Startar dashboard i bakgrunden"""
        config = uvicorn.Config(
            self.app,
            host=self.dashboard_config.host,
            port=self.dashboard_config.port,
            log_level="info" if self.dashboard_config.debug else "warning",
        )

        server = uvicorn.Server(config)
        await server.serve()


# Convenience function för snabb start
def create_dashboard(config: Optional[Config] = None) -> DashboardApp:
    """Skapar och konfigurerar dashboard"""
    return DashboardApp(config)


if __name__ == "__main__":
    # Exempel på användning
    dashboard = create_dashboard()
    dashboard.run()
