import logging.config
import yaml
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------- Logging ----------
with open("logging.yaml", "r", encoding="utf-8") as f:
    logging.config.dictConfig(yaml.safe_load(f))

logger = logging.getLogger("titan")

# ---------- Simple Rate Limit ----------
REQUESTS = {}
RATE_LIMIT = 60  # requests per minute per IP

def is_rate_limited(ip):
    now_min = int(time.time() / 60)
    key = f"{ip}:{now_min}"
    REQUESTS[key] = REQUESTS.get(key, 0) + 1
    return REQUESTS[key] > RATE_LIMIT

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

# ---------- Server ----------
def run(host="0.0.0.0", port=8080):
    server = HTTPServer((host, port), TitanHandler)
    logger.info("Titan API started", extra={"host": host, "port": port})
    server.serve_forever()

if __name__ == "__main__":
    run()
