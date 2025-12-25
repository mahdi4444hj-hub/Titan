import logging.config
import yaml
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# -------------------- Logging --------------------
with open("logging.yaml", "r") as f:
    logging.config.dictConfig(yaml.safe_load(f))

logger = logging.getLogger("titan")

# -------------------- Simple Rate Limit (basic) --------------------
REQUESTS = {}
RATE_LIMIT = 60  # requests per minute per IP

def is_rate_limited(ip):
    now = int(time.time() / 60)
    key = f"{ip}:{now}"
    REQUESTS[key] = REQUESTS.get(key, 0) + 1
    return REQUESTS[key] > RATE_LIMIT

# -------------------- Handler --------------------
class TitanHandler(BaseHTTPRequestHandler):

    def _json_response(self, code, payload):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_GET(self):
        client_ip = self.client_address[0]
        logger.info("GET request", extra={"ip": client_ip, "path": self.path})

        if is_rate_limited(client_ip):
            logger.warning("Rate limit exceeded", extra={"ip": client_ip})
            self._json_response(429, {"error": "rate limit"})
            return

        if self.path == "/health":
            self._json_response(200, {
                "status": "ok",
                "service": "Titan",
                "version": "0.1.0"
            })
            return

        if self.path == "/":
            self._json_response(200, {
                "message": "Titan API running"
            })
            return

        self._json_response(404, {"error": "not found"})

# -------------------- Server --------------------
def run(host="0.0.0.0", port=8080):
    server = HTTPServer((host, port), TitanHandler)
    logger.info("Titan API started", extra={"host": host, "port": port})
    server.serve_forever()

if __name__ == "__main__":
    run()
