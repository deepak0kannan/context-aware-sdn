#!/usr/bin/env python3
"""
Lightweight Localhost Dashboard API & Web Server
Serves the Netflix-Themed Context-Aware SDN Dashboard on http://127.0.0.1:5000
"""

import os
import sys
import json
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
STATUS_FILE = os.path.join(DATA_DIR, "live_remediation_status.json")
BENCHMARK_FILE = os.path.join(DATA_DIR, "benchmark_results.json")
INDEX_HTML = os.path.join(PROJECT_DIR, "index.html")


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in ["/", "/index.html"]:
            try:
                with open(INDEX_HTML, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                self.send_error(500, f"Error reading index.html: {e}")
                return

        elif parsed.path == "/api/status":
            data = {
                "timestamp": time.time(),
                "detected_class": "normal",
                "confidence": 0.985,
                "remediation_state": "NORMAL",
                "last_action": "BASELINE_PATH_A",
                "action_description": "Primary Path A (s1-s2-s4) active with deterministic flow rules.",
                "telemetry": {
                    "packet_rate": 54.2,
                    "byte_rate": 76.2,
                    "unique_ips": 1,
                    "entropy": 0.0,
                    "avg_packet_size": 1406,
                    "std_packet_size": 18.4,
                    "port_status": 1,
                    "rx_dropped": 0,
                    "tx_dropped": 2
                }
            }
            if os.path.exists(STATUS_FILE):
                try:
                    with open(STATUS_FILE, "r") as f:
                        data = json.load(f)
                except Exception:
                    pass

            resp = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
            return

        elif parsed.path == "/api/benchmark":
            data = {}
            if os.path.exists(BENCHMARK_FILE):
                try:
                    with open(BENCHMARK_FILE, "r") as f:
                        data = json.load(f)
                except Exception:
                    pass

            resp = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
            return

        # Fallback to standard file serving from project root
        self.directory = PROJECT_DIR
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/inject":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            scenario = "normal"
            try:
                body = json.loads(post_data)
                scenario = body.get("scenario", "normal")
            except Exception:
                pass

            status_map = {
                "normal": ("normal", 0.984, "NORMAL", "BASELINE_PATH_A", "Primary Path A active with deterministic flow rules."),
                "flash_crowd": ("flash_crowd", 0.942, "LOAD_BALANCED", "OFPGT_SELECT_MULTIPATH", "Installed OpenFlow 1.3 SELECT group table (Group 50) across Path A and Path B."),
                "ddos": ("ddos", 0.998, "INGRESS_DROP", "SURGICAL_INGRESS_DROP", "High-priority surgical drop rule installed against attacker source IP."),
                "slow_congestion": ("slow_congestion", 0.925, "PREEMPTIVE_REROUTE", "PREEMPTIVE_REROUTE", "Secondary bulk flows diverted to Path B before queue drop occurs on Path A."),
                "link_failure": ("link_failure", 1.000, "LINK_FAILOVER", "FAILOVER_PATH_B", "Port s1-eth6 down signal captured. OpenFlow fast failover engaged to backup Path B.")
            }
            c_name, conf, rem_state, act, desc = status_map.get(scenario, status_map["normal"])
            
            telemetry_map = {
                "normal": (54.2, 76.2, 1, 0.0, 1406, 18.4, 1, 0, 2),
                "flash_crowd": (480.5, 680.0, 5, 2.32, 1415, 42.1, 1, 0, 2),
                "ddos": (980.0, 62.7, 1, 0.0, 64, 2.1, 1, 0, 2),
                "slow_congestion": (620.0, 890.0, 2, 0.95, 1435, 22.0, 1, 0, 14),
                "link_failure": (48.0, 58.0, 1, 0.0, 1370, 24.5, 0, 0, 2)
            }
            tel = telemetry_map.get(scenario, telemetry_map["normal"])

            mock_state = {
                "timestamp": time.time(),
                "formatted_time": time.strftime("%H:%M:%S"),
                "detected_class": c_name,
                "confidence": conf,
                "remediation_state": rem_state,
                "last_action": act,
                "action_description": desc,
                "telemetry": {
                    "packet_rate": tel[0],
                    "byte_rate": tel[1],
                    "unique_ips": tel[2],
                    "entropy": tel[3],
                    "avg_packet_size": tel[4],
                    "std_packet_size": tel[5],
                    "port_status": tel[6],
                    "rx_dropped": tel[7],
                    "tx_dropped": tel[8]
                }
            }
            try:
                os.makedirs(DATA_DIR, exist_ok=True)
                with open(STATUS_FILE, "w") as f:
                    json.dump(mock_state, f, indent=2)
            except Exception:
                pass

            resp = json.dumps({"success": True, "scenario": scenario, "state": mock_state}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
            return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run_server(port=5000):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, DashboardHandler)
    print("=" * 65)
    print(f"[*] Netflix-Themed SDN Dashboard running at:")
    print(f"    -> http://127.0.0.1:{port}/")
    print(f"    -> http://localhost:{port}/")
    print("=" * 65)
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")


if __name__ == "__main__":
    p = 5000
    if len(sys.argv) > 1:
        p = int(sys.argv[1])
    run_server(p)
