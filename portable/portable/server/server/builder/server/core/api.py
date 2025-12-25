from http.server import BaseHTTPRequestHandler, HTTPServer
import json

API_KEY = "CHANGE_ME"

class TitanHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get("X-API-Key") != API_KEY:
            self.send_response(403)
            self.end_headers()
            return

        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "running",
                "service": "TitanFusion"
            }).encode())

def run(port=8443):
    server = HTTPServer(("", port), TitanHandler)
    server.serve_forever()

if __name__ == "__main__":
    run()
