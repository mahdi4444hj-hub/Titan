from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from auth import check

API_KEY = "CHANGE_ME"

class TitanHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # API Key check
        if self.headers.get("X-API-Key") != API_KEY:
            self.send_response(403)
            self.end_headers()
            return

        # Email / Password check
        email = self.headers.get("X-Email")
        password = self.headers.get("X-Password")
        if not check(email, password):
            self.send_response(401)
            self.end_headers()
            return

        # Routes
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "running",
                "service": "TitanFusion"
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()


def run(port=8443):
    server = HTTPServer(("", port), TitanHandler)
    server.serve_forever()


if __name__ == "__main__":
    run()
