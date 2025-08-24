#!/usr/bin/env python3
"""
🎛️ DASHBOARD MANAGER - Enkel hantering av alla dashboards
"""

import subprocess
import time
import sys
import os
from typing import Dict, Optional
import threading
import signal


class DashboardManager:
    def __init__(self):
        self.dashboards = {
            "1": {
                "name": "🔒 Security Dashboard",
                "file": "security_dashboard.py",
                "port": 8000,
                "description": "GDPR compliance, security auditing, threat detection",
            },
            "2": {
                "name": "🤖 AI Dashboard",
                "file": "ai_dashboard.py",
                "port": 8084,
                "description": "AI-powered features, sentiment analysis, content classification",
            },
            "3": {
                "name": "📱 Mobile Dashboard",
                "file": "mobile_dashboard.py",
                "port": 8081,
                "description": "Mobile-first design, touch support, responsive UI",
            },
            "4": {
                "name": "🎛️ Control Dashboard",
                "file": "control_dashboard.py",
                "port": 8082,
                "description": "Advanced controls, monitoring, configuration",
            },
            "5": {
                "name": "🚀 Advanced Dashboard",
                "file": "enhanced_dashboard.py",
                "port": 8083,
                "description": "Enhanced features, performance optimization",
            },
        }
        self.running_processes = {}

    def show_menu(self):
        """Visar huvudmenyn"""
        print("\n" + "=" * 60)
        print("🎛️  DASHBOARD MANAGER - Enkel hantering av alla dashboards")
        print("=" * 60)

        print("\n📋 Tillgängliga dashboards:")
        for key, dashboard in self.dashboards.items():
            status = "🟢 Körs" if key in self.running_processes else "⚪ Stoppad"
            print(f"   {key}. {dashboard['name']} - {status}")
            print(f"      {dashboard['description']}")
            print(f"      Port: {dashboard['port']}")
            print()

        print("🔧 Kommandon:")
        print("   start <nummer>  - Starta dashboard")
        print("   stop <nummer>   - Stoppa dashboard")
        print("   restart <nummer> - Starta om dashboard")
        print("   status          - Visa status för alla")
        print("   stop all        - Stoppa alla dashboards")
        print("   open <nummer>   - Öppna dashboard i webbläsare")
        print("   q/quit          - Avsluta")
        print("=" * 60)

    def start_dashboard(self, dashboard_num: str):
        """Startar en dashboard"""
        if dashboard_num not in self.dashboards:
            print(f"❌ Dashboard {dashboard_num} finns inte!")
            return

        if dashboard_num in self.running_processes:
            print(f"⚠️  Dashboard {dashboard_num} körs redan!")
            return

        dashboard = self.dashboards[dashboard_num]
        print(f"🚀 Startar {dashboard['name']}...")

        try:
            # Starta process i bakgrunden
            process = subprocess.Popen(
                [sys.executable, dashboard["file"]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.running_processes[dashboard_num] = process
            print(f"✅ {dashboard['name']} startad på port {dashboard['port']}")
            print(f"🌐 Öppna: http://127.0.0.1:{dashboard['port']}")

        except Exception as e:
            print(f"❌ Fel vid start av {dashboard['name']}: {e}")

    def stop_dashboard(self, dashboard_num: str):
        """Stoppar en dashboard"""
        if dashboard_num not in self.running_processes:
            print(f"⚠️  Dashboard {dashboard_num} körs inte!")
            return

        dashboard = self.dashboards[dashboard_num]
        process = self.running_processes[dashboard_num]

        print(f"🛑 Stoppar {dashboard['name']}...")

        try:
            process.terminate()
            process.wait(timeout=5)
            del self.running_processes[dashboard_num]
            print(f"✅ {dashboard['name']} stoppad")
        except subprocess.TimeoutExpired:
            process.kill()
            del self.running_processes[dashboard_num]
            print(f"✅ {dashboard['name']} tvingad att stoppa")
        except Exception as e:
            print(f"❌ Fel vid stopp av {dashboard['name']}: {e}")

    def restart_dashboard(self, dashboard_num: str):
        """Startar om en dashboard"""
        self.stop_dashboard(dashboard_num)
        time.sleep(1)
        self.start_dashboard(dashboard_num)

    def stop_all_dashboards(self):
        """Stoppar alla dashboards"""
        print("🛑 Stoppar alla dashboards...")
        for dashboard_num in list(self.running_processes.keys()):
            self.stop_dashboard(dashboard_num)
        print("✅ Alla dashboards stoppade")

    def show_status(self):
        """Visar status för alla dashboards"""
        print("\n📊 STATUS ÖVERSIKT:")
        print("-" * 40)

        for key, dashboard in self.dashboards.items():
            status = "🟢 Körs" if key in self.running_processes else "⚪ Stoppad"
            print(f"{dashboard['name']}: {status}")

        if self.running_processes:
            print(f"\n🟢 Körs: {len(self.running_processes)} dashboard(s)")
        else:
            print("\n⚪ Inga dashboards körs")

    def open_dashboard(self, dashboard_num: str):
        """Öppnar dashboard i webbläsare"""
        if dashboard_num not in self.dashboards:
            print(f"❌ Dashboard {dashboard_num} finns inte!")
            return

        dashboard = self.dashboards[dashboard_num]
        url = f"http://127.0.0.1:{dashboard['port']}"

        print(f"🌐 Öppnar {dashboard['name']} i webbläsare...")
        print(f"URL: {url}")

        try:
            import webbrowser

            webbrowser.open(url)
        except Exception as e:
            print(f"❌ Kunde inte öppna webbläsare: {e}")
            print(f"📋 Kopiera denna URL: {url}")

    def run(self):
        """Huvudloop för dashboard manager"""
        print("🎛️  Dashboard Manager startad!")

        while True:
            try:
                self.show_menu()
                command = input("\n🎯 Kommando: ").strip().lower()

                if command in ["q", "quit", "exit"]:
                    print("👋 Avslutar Dashboard Manager...")
                    self.stop_all_dashboards()
                    break

                elif command == "status":
                    self.show_status()

                elif command == "stop all":
                    self.stop_all_dashboards()

                elif command.startswith("start "):
                    dashboard_num = command.split()[1]
                    self.start_dashboard(dashboard_num)

                elif command.startswith("stop "):
                    dashboard_num = command.split()[1]
                    self.stop_dashboard(dashboard_num)

                elif command.startswith("restart "):
                    dashboard_num = command.split()[1]
                    self.restart_dashboard(dashboard_num)

                elif command.startswith("open "):
                    dashboard_num = command.split()[1]
                    self.open_dashboard(dashboard_num)

                else:
                    print("❌ Okänt kommando. Använd 'start', 'stop', 'restart', 'open', 'status' eller 'quit'")

                input("\n⏸️  Tryck Enter för att fortsätta...")

            except KeyboardInterrupt:
                print("\n\n👋 Avslutar Dashboard Manager...")
                self.stop_all_dashboards()
                break
            except Exception as e:
                print(f"❌ Fel: {e}")
                input("\n⏸️  Tryck Enter för att fortsätta...")


if __name__ == "__main__":
    manager = DashboardManager()
    manager.run()
