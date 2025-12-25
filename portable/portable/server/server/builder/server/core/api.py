import json
import time
import socketserver
from http.server import BaseHTTPRequestHandler
from collections import defaultdict

# ======================
# Security Config
# ======================
RATE_LIMIT = 60  # requests per minute
BLOCKED_COUNTRIES = {"CN", "RU", "KP"}  # نمونه
REQUEST_LOG = defaultdict(list)
BLOCKED_IPS = set()

# ======================
# Simple Geo-IP (Mock)
# ======================
def get_country_from_ip(ip):
    if ip.startswith("127.") or ip.startswith("192."):
        return "LOCAL"
    return "UNKNOWN"

# ======================
# Rate Limiter
# ======================
def is_rate_limited(ip):
    now = time.time()
    REQUEST_LOG[ip] = [t for t in REQUEST_LOG[ip] if now - t < 60]
    REQUEST_LOG[ip].append(now)
    return len(REQUEST_LOG[ip]) > RATE_LIMIT

# ======================
# Basic WAF / AI-like Detection
# ======================
def is_malicious(path, headers):
    suspicious_keywords = ["../", "<script", "select *", "union", "%00"]
    for key in suspicious_keywords:
        if key.lower() in path.lower():
            return True
    user_agent = headers.get("User-Agent", "")
    if user_agent == "":
        return True
    return False

# ======================
# HTTP Handler
# ======================
class TitanHandler(BaseHTTPRequestHandler):

    def _block(self, code=403, msg="Blocked"):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "blocked", "reason": msg}).encode())

    def do_GET(self):
        client_ip = self.client_address[0]

        # ---- Global IP Block ----
        if client_ip in BLOCKED_IPS:
            return self._block(403, "IP blacklisted")

        # ---- Rate Limit ----
        if is_rate_limited(client_ip):
            BLOCKED_IPS.add(client_ip)
            return self._block(429, "Rate limit exceeded")

        # ---- Geo-IP Block ----
        country = get_country_from_ip(client_ip)
        if country in BLOCKED_COUNTRIES:
            BLOCKED_IPS.add(client_ip)
            return self._block(403, "Geo blocked")

        # ---- WAF / AI Detection ----
        if is_malicious(self.path, self.headers):
            BLOCKED_IPS.add(client_ip)
            return self._block(403, "Malicious request detected")

        # ======================
        # Routes
        # ======================
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "service": "TitanFusion API",
                "status": "running",
                "ip": client_ip
            }).encode())

        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        else:
            self.send_response(404)
            self.end_headers()

# ======================
# Server Bootstrap
# ======================
def run_server(port=8080):
    with socketserver.ThreadingTCPServer(("", port), TitanHandler) as httpd:
        print(f"[TitanFusion] Secure API running on port {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
