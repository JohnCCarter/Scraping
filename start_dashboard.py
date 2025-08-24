#!/usr/bin/env python3
"""
🚀 Start Dashboard - Försöker olika portar
"""

import http.server
import socketserver
import threading
import time
import os

def create_handler():
    class DashboardHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                # Läs HTML-filen
                try:
                    with open('dashboard.html', 'r', encoding='utf-8') as f:
                        html = f.read()
                    self.wfile.write(html.encode('utf-8'))
                except FileNotFoundError:
                    self.wfile.write(b"Dashboard HTML file not found!")
            else:
                super().do_GET()
    
    return DashboardHandler

def start_server_on_port(port):
    try:
        handler = create_handler()
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"✅ Server startad på port {port}")
            print(f"🌐 Lokal: http://localhost:{port}")
            print(f"🌐 Extern: http://34.233.103.205:{port}")
            httpd.serve_forever()
    except OSError as e:
        print(f"❌ Kunde inte starta på port {port}: {e}")
        return False
    return True

def main():
    print("🚀 Startar Dashboard på olika portar...")
    
    # Testa olika portar
    ports = [8080, 3000, 5000, 8000, 9000, 4000, 6000, 7000]
    
    for port in ports:
        print(f"\n🔄 Försöker port {port}...")
        if start_server_on_port(port):
            break
        time.sleep(1)
    else:
        print("❌ Kunde inte starta på någon port!")
        print("💡 Ladda ner dashboard.html och öppna den lokalt istället!")

if __name__ == "__main__":
    main()