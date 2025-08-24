#!/usr/bin/env python3
"""
🚀 Enkel Web Server - Bara fungerar!
"""

import http.server
import socketserver
import threading
import time
import json
from datetime import datetime

# Simulerad data
class DashboardData:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.scraped_urls = [
            {"url": "https://httpbin.org/html", "title": "HTML Test Page", "timestamp": "2024-01-15 13:30:00"},
            {"url": "https://httpbin.org/json", "title": "JSON API", "timestamp": "2024-01-15 13:29:45"},
            {"url": "https://httpbin.org/xml", "title": "XML Data", "timestamp": "2024-01-15 13:29:30"},
        ]

    def get_stats(self):
        uptime = int(time.time() - self.start_time)
        success_rate = 95.5  # Simulerad data
        return {
            "uptime": uptime,
            "requests": self.request_count + 150,
            "success": self.success_count + 143,
            "errors": self.error_count + 7,
            "success_rate": success_rate,
            "scraped_urls": len(self.scraped_urls),
        }

dashboard_data = DashboardData()

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
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
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            backdrop-filter: blur(10px);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .success {{ color: #4CAF50; }}
        .error {{ color: #f44336; }}
        .info {{ color: #2196F3; }}
        .urls-section {{
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }}
        .url-item {{
            background: rgba(255, 255, 255, 0.05);
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
        }}
        .status {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="status">🟢 ONLINE</div>
    <div class="container">
        <div class="header">
            <h1>🚀 Enkel Dashboard</h1>
            <p>Live statistik för web scraping</p>
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
            {''.join([f'<div class="url-item"><strong>{item["url"]}</strong><br><small>{item["title"]} - {item["timestamp"]}</small></div>' for item in dashboard_data.scraped_urls])}
        </div>
    </div>
    
    <script>
        // Auto-refresh var 10:e sekund
        setInterval(() => {{
            location.reload();
        }}, 10000);
    </script>
</body>
</html>
            """
            
            self.wfile.write(html.encode())
        elif self.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(dashboard_data.get_stats()).encode())
        else:
            super().do_GET()

def start_server():
    PORT = 8080
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"🚀 Server startad på port {PORT}")
        print(f"🌐 Öppna: http://localhost:{PORT}")
        print(f"🌐 Extern: http://34.233.103.205:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    print("🚀 Startar Enkel Web Server...")
    start_server()