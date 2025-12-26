import logging.config
import yaml
import json
import time
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------- Load Logging ----------
with open("logging.yaml", "r", encoding="utf-8") as f:
    logging.config.dictConfig(yaml.safe_load(f))

logger = logging.getLogger("titan")

# ---------- Rate Limit (basic) ----------
REQUESTS = {}
RATE_LIMIT = 60  # per minute per IP

def is_rate_limited(ip):
    minute = int(time.time() / 60)
    key = f"{ip}:{minute}"
    REQUESTS[key] = REQUESTS.get(key, 0) + 1
    return REQUESTS[key] > RATE_LIMIT
# ---------- Geo-IP (placeholder) ----------
GEOIP_ENABLED = False
def check_geoip(ip):
    return True  # later: real country check

# ---------- AI Detection (placeholder) ----------
AI_ENABLED = False
def ai_detect(ip, path):
    return False  # later: real AI logic
# ---------- HTTP Handler ----------
class TitanHandler(BaseHTTPRequestHandler):
    def _json(self, code, payload):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_GET(self):
        client_ip = self.client_address[0]
        logger.info("request received", extra={"ip": client_ip, "path": self.path})

        if is_rate_limited(client_ip):
            logger.warning("rate limit exceeded", extra={"ip": client_ip})
            self._json(429, {"error": "rate limit"})
            return

        if self.path == "/":
            self._json(200, {"message": "Titan API running"})
            return

        if self.path == "/health":
            self._json(200, {
                "status": "ok",
                "service": "Titan",
                "version": "0.1.0"
            })
            return

        logger.warning("route not found", extra={"path": self.path})
        self._json(404, {"error": "not found"})

# ---------- HTTPS Server ----------
def run(host="0.0.0.0", port=8443):
    server = HTTPServer((host, port), TitanHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile="certs/server.crt",
        keyfile="certs/server.key"
    )
    server.socket = context.wrap_socket(server.socket, server_side=True)
    logger.info("Titan HTTPS started", extra={"host": host, "port": port})
    server.serve_forever()

if __name__ == "__main__":
    run()
