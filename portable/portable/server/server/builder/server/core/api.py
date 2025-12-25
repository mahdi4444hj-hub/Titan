import time

RATE_LIMIT = 60  # req/min per IP
BLOCKED_COUNTRIES = {"CN", "RU"}  # مثال
requests = {}

def rate_limited(ip):
    now = time.time()
    window = 60
    reqs = requests.get(ip, [])
    reqs = [t for t in reqs if now - t < window]
    if len(reqs) >= RATE_LIMIT:
        return True
    reqs.append(now)
    requests[ip] = reqs
    return False
    
def geo_block(ip):
    # ساده‌سازی: فعلاً دستی/Placeholder
    return False

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import hashlib

API_KEY = "CHANGE_ME"

# --- Auth ---
USERS = {
    "admin@local": hashlib.sha256("admin123".encode()).hexdigest()
}

def check_auth(email, password):
    if not email or not password:
        return False
    h = hashlib.sha256(password.encode()).hexdigest()
    return USERS.get(email) == h


# --- HTTP Handler ---
class TitanHandler(BaseHTTPRequestHandler):

    def _unauthorized(self):
        self.send_response(401)
        self.end_headers()

    def _forbidden(self):
        self.send_response(403)
        self.end_headers()

    def do_GET(self):

        # API KEY
        if self.headers.get("X-API-Key") != API_KEY:
            return self._forbidden()

        # LOGIN
        email = self.headers.get("X-Email")
        password = self.headers.get("X-Password")
        if not check_auth(email, password):
            return self._unauthorized()

        # ROUTES
        if self.path == "/" or self.path == "/dashboard":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())

        elif self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "running",
                "service": "TitanFusion",
                "mode": "secured"
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()


# --- Dashboard UI ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>TitanFusion Dashboard</title>
</head>
<body>
<h2>TitanFusion Secure Dashboard</h2>
<button onclick="check()">Check Status</button>
<pre id="out">---</pre>

<script>
function check(){
 fetch("/status", {
  headers:{
   "X-API-Key":"CHANGE_ME",
   "X-Email":"admin@local",
   "X-Password":"admin123"
  }
 }).then(r=>r.json()).then(d=>{
   document.getElementById("out").innerText =
    JSON.stringify(d,null,2)
 })
}
</script>
</body>
</html>
"""


def run(port=8443):
    server = HTTPServer(("", port), TitanHandler)
    server.serve_forever()


if __name__ == "__main__":
    run()
