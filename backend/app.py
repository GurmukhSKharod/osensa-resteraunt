# backend/web_service.py
# expose a minimal HTTP /health endpoint 
# so Render can host this as a Web Service,
# and start your existing MQTT worker in the background.

import os
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Import your existing blocking worker entrypoint
from kitchen.main import main as kitchen_main


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"ok": True}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    # keep logs quiet
    def log_message(self, fmt, *args):
        return


def start_worker_once():
    # Start your MQTT worker in a background daemon thread.
    # kitchen_main() should block forever.
    t = threading.Thread(target=kitchen_main, daemon=True)
    t.start()
    return t


def main():
    # Render injects $PORT. Default locally if missing.
    port = int(os.environ.get("PORT", "8000"))

    # Start the MQTT worker
    start_worker_once()

    # Start the HTTP health server
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"[backend] Health server on :{port} (GET /health)")
    server.serve_forever()


if __name__ == "__main__":
    main()
