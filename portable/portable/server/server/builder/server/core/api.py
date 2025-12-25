from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import time
import threading
import logging
import secrets
from urllib.parse import parse_qs, urlparse
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

# Configuration
PORT = 8000
RATE_LIMIT = 60  # requests per minute
SESSION_TIMEOUT = 3600  # 1 hour
MAX_BODY_SIZE = 1_048_576  # 1MB
DASHBOARD_HTML = None  # Cache

# Thread-safe storage
lock = threading.Lock()
requests_log: Dict[str, List[float]] = defaultdict(list)
SESSIONS: Dict[str, Dict] = {}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_dashboard_html() -> bytes:
    """Load and cache dashboard HTML"""
    global DASHBOARD_HTML
    if DASHBOARD_HTML is None:
        try:
            html_path = Path("core/dashboard/index.html")
            if not html_path.exists():
                logger.error(f"Dashboard HTML not found: {html_path}")
                return b"<h1>Dashboard not found</h1>"
            
            DASHBOARD_HTML = html_path.read_bytes()
            logger.info("Dashboard HTML loaded and cached")
        except Exception as e:
            logger.error(f"Failed to load dashboard: {e}")
            return b"<h1>Error loading dashboard</h1>"
    
    return DASHBOARD_HTML


def is_rate_limited(ip: str) -> bool:
    """Check if IP has exceeded rate limit"""
    now = time.time()
    
    with lock:
        # Clean old requests
        requests_log[ip] = [
            t for t in requests_log[ip] 
            if now - t < 60
        ]
        
        # Check limit
        if len(requests_log[ip]) >= RATE_LIMIT:
            return True
        
        # Add new request
        requests_log[ip].append(now)
        return False


def cleanup_sessions():
    """Remove expired sessions (runs in background)"""
    while True:
        time.sleep(300)  # Check every 5 minutes
        
        now = time.time()
        with lock:
            expired = [
                token for token, data in SESSIONS.items()
                if data.get("expires", 0) < now
            ]
            
            for token in expired:
                del SESSIONS[token]
            
            if expired:
                logger.info(f"Cleaned {len(expired)} expired sessions")


def validate_session(token: Optional[str]) -> Optional[str]:
    """Validate session token and return email"""
    if not token:
        return None
    
    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    
    with lock:
        session = SESSIONS.get(token)
        
        if not session:
            return None
        
        # Check expiration
        if session.get("expires", 0) < time.time():
            del SESSIONS[token]
            return None
        
        return session.get("email")


class TitanHandler(BaseHTTPRequestHandler):
    """Enhanced HTTP handler with security features"""
    
    def send_json(self, code: int, data: dict, headers: dict = None):
        """Send JSON response with proper headers"""
        try:
            body = json.dumps(data).encode('utf-8')
            
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            
            if headers:
                for key, value in headers.items():
                    self.send_header(key, value)
            
            self.end_headers()
            self.wfile.write(body)
            
        except Exception as e:
            logger.error(f"Error sending JSON: {e}")
    
    def send_html(self, code: int, html: bytes):
        """Send HTML response"""
        try:
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "SAMEORIGIN")
            self.end_headers()
            self.wfile.write(html)
            
        except Exception as e:
            logger.error(f"Error sending HTML: {e}")
    
    def do_POST(self):
        """Handle POST requests"""
        ip = self.client_address[0]
        
        # Rate limiting
        if is_rate_limited(ip):
            logger.warning(f"Rate limit exceeded for {ip}")
            self.send_json(429, {"error": "Too many requests"})
            return
        
        try:
            # Check content length
            length = int(self.headers.get("Content-Length", 0))
            
            if length > MAX_BODY_SIZE:
                self.send_json(413, {"error": "Request body too large"})
                return
            
            if length == 0:
                self.send_json(400, {"error": "Empty request body"})
                return
            
            # Read and parse body
            body = self.rfile.read(length).decode('utf-8')
            data = parse_qs(body)
            
            # Route handling
            if self.path == "/login":
                self.handle_login(data)
            elif self.path == "/logout":
                self.handle_logout()
            else:
                self.send_json(404, {"error": "Endpoint not found"})
        
        except UnicodeDecodeError:
            self.send_json(400, {"error": "Invalid UTF-8 encoding"})
        except Exception as e:
            logger.error(f"POST error: {e}", exc_info=True)
            self.send_json(500, {"error": "Internal server error"})
    
    def handle_login(self, data: dict):
        """Handle login request"""
        try:
            email = data.get("email", [""])[0].strip()
            password = data.get("password", [""])[0]
            
            if not email or not password:
                self.send_json(400, {"error": "Email and password required"})
                return
            
            # Import here to avoid circular dependency
            from auth import verify_user
            
            if verify_user(email, password):
                # Create secure session
                token = secrets.token_urlsafe(32)
                
                with lock:
                    SESSIONS[token] = {
                        "email": email,
                        "created": time.time(),
                        "expires": time.time() + SESSION_TIMEOUT,
                        "ip": self.client_address[0]
                    }
                
                logger.info(f"Successful login: {email}")
                self.send_json(200, {
                    "token": token,
                    "expires_in": SESSION_TIMEOUT
                })
            else:
                logger.warning(f"Failed login attempt: {email}")
                self.send_json(401, {"error": "Invalid credentials"})
        
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            self.send_json(500, {"error": "Login failed"})
    
    def handle_logout(self):
        """Handle logout request"""
        try:
            token = self.headers.get("Authorization")
            
            if token and token.startswith("Bearer "):
                token = token[7:]
                
                with lock:
                    if token in SESSIONS:
                        email = SESSIONS[token].get("email")
                        del SESSIONS[token]
                        logger.info(f"User logged out: {email}")
                        self.send_json(200, {"message": "Logged out successfully"})
                        return
            
            self.send_json(400, {"error": "Invalid session"})
        
        except Exception as e:
            logger.error(f"Logout error: {e}")
            self.send_json(500, {"error": "Logout failed"})
    
    def do_GET(self):
        """Handle GET requests"""
        ip = self.client_address[0]
        
        # Rate limiting
        if is_rate_limited(ip):
            logger.warning(f"Rate limit exceeded for {ip}")
            self.send_json(429, {"error": "Too many requests"})
            return
        
        try:
            # Parse URL
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # Health check (no auth required)
            if path == "/health":
                self.send_json(200, {
                    "status": "ok",
                    "timestamp": time.time(),
                    "sessions": len(SESSIONS)
                })
                return
            
            # Dashboard (auth required)
            if path.startswith("/dashboard"):
                token = self.headers.get("Authorization")
                email = validate_session(token)
                
                if not email:
                    self.send_json(403, {"error": "Unauthorized"})
                    return
                
                html = load_dashboard_html()
                self.send_html(200, html)
                return
            
            # Session info
            if path == "/session":
                token = self.headers.get("Authorization")
                email = validate_session(token)
                
                if not email:
                    self.send_json(403, {"error": "Unauthorized"})
                    return
                
                with lock:
                    session = SESSIONS.get(token[7:] if token.startswith("Bearer ") else token)
                
                self.send_json(200, {
                    "email": email,
                    "created": session.get("created"),
                    "expires": session.get("expires"),
                    "time_remaining": int(session.get("expires", 0) - time.time())
                })
                return
            
            # Not found
            self.send_json(404, {"error": "Endpoint not found"})
        
        except Exception as e:
            logger.error(f"GET error: {e}", exc_info=True)
            self.send_json(500, {"error": "Internal server error"})
    
    def log_message(self, format, *args):
        """Override to use custom logging"""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server():
    """Start HTTP server"""
    try:
        # Start session cleanup thread
        cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
        cleanup_thread.start()
        logger.info("Session cleanup thread started")
        
        # Create and start server
        server = ThreadingHTTPServer(("0.0.0.0", PORT), TitanHandler)
        logger.info(f"🚀 Titan HTTP Server running on port {PORT}")
        logger.info(f"📊 Rate limit: {RATE_LIMIT} requests/minute")
        logger.info(f"⏱️  Session timeout: {SESSION_TIMEOUT} seconds")
        
        server.serve_forever()
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        logger.info("Server shutdown")


if __name__ == "__main__":
    run_server()
