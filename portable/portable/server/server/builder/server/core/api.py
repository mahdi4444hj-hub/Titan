from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import time
import threading
import logging

# ================= CONFIG =================
PORT = 8000
RATE_LIMIT = 60        # requests per minute per IP
BLOCKED_IPS = set()    # امکان گسترش آینده

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ================= RATE LIMIT =================
lock = threading.Lock()
request_log = {}

def rate_limited(ip: str) -> bool:
    now = time.time()
    with lock:
        timestamps = request_log.get(ip, [])
        timestamps = [t for t in timestamps if now - t < 60]
        timestamps.append(now)
        request_log[ip] = timestamps
        return len(timestamps) > RATE_LIMIT

# ================= HANDLER =================
class TitanAPI(BaseHTTPRequestHandler):

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        client_ip = self.client_address[0]

        # ---- IP BLOCK ----
        if client_ip in BLOCKED_IPS:
            logging.warning(f"Blocked IP tried access: {client_ip}")
            self._send_json(403, {"error": "Forbidden"})
            return

        # ---- RATE LIMIT ----
        if rate_limited(client_ip):
            logging.warning(f"Rate limit exceeded: {client_ip}")
            self._send_json(429, {"error": "Too many requests"})
            return

        # ---- ROUTES ----
        if self.path == "/":
            self._send_json(200, {"status": "Titan API running"})
        elif self.path == "/health":
            self._send_json(200, {"ok": True})
        else:
            self._send_json(404, {"error": "Not found"})

    def log_message(self, format, *args):
        # جلوگیری از لاگ اضافی BaseHTTPRequestHandler
        return

# ================= RUN =================
def run():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), TitanAPI)
    logging.info(f"Titan Server started on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        logging.info("Titan Server stopped")

if __name__ == "__main__":
    run()
