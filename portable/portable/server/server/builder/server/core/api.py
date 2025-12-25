from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import hashlib
import time

# ================= CONFIG =================
API_KEY = "CHANGE_ME"
RATE_LIMIT = 60  # requests per minute per IP

USERS = {
    "admin@local": hashlib.sha256("admin123".encode()).hexdigest()
}

SUSPICIOUS_PATHS = {"/admin", "/wp-login", "/phpmyadmin"}

# ================= MEMORY =================
requests_log = {}
blocked_ips = set()

# ================= SECURITY =================
def check_auth(email, password):
    if not email or not password:
        return False
    h = hashlib.sha256(password.encode()).hexdigest()
    return USERS.get(email) == h


def rate_limited(ip):
    now = time.time()
    window = 60
    log = requests_log.get(ip, [])
    log = [t for t in log if now - t < window]
    if len(log) >= RATE_LIMIT:
        return True
    log.append(now)
    requests_log[ip] = log
    return False


def ai_detect(path, ip):
    if path in SUSPICIOUS_PATHS:
        blocked_ips.add(ip)
        return True
    return False


# ================= DASHBOARD =================
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
 }).catch(e=>{
   document.getElementById("out").innerText = "ACCESS DENIED";
 })
}
</script>
</body>
</html>
"""

# ================= HANDLER =================
class TitanHandler(BaseHTTPRequestHandler):

    def deny(self, code):
        self.send_response(code)
        self.end_headers()

    def do_GET(self):
        ip = self.client_address[0]

        # Permanent Block
        if ip in blocked_ips:
            return self.deny(403)

        # Rate Limit
        if rate_limited(ip):
            return self.deny(429)

        # AI / WAF
        if ai_detect(self.path, ip):
            return self.deny(403)

        # API Key
        if self.headers.get("X-API-Key") != API_KEY:
            return self.deny(403)

        # Login
        email = self.headers.get("X-Email")
        password = self.headers.get("X-Password")
        if not check_auth(email, password):
            return self.deny(401)

        # Routes
        if self.path in ("/", "/dashboard"):
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
                "security": "active",
                "blocked_ips": len(blocked_ips)
            }).encode())
        else:
            self.deny(404)


# ================= RUN =================
def run(port=8443):
    server = HTTPServer(("", port), TitanHandler)
    print(f"TitanFusion running on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
