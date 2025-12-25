from http.server import HTTPServer
import ssl
from api import TitanHandler

def run_https(port=8443):
    httpd = HTTPServer(("", port), TitanHandler)
    httpd.socket = ssl.wrap_socket(
        httpd.socket,
        certfile="cert.pem",
        keyfile="key.pem",
        server_side=True
    )
    httpd.serve_forever()

if __name__ == "__main__":
    run_https()
