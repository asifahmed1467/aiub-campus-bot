"""AIUB Campus Companion - run with:  python app.py   then open http://localhost:8000

Zero dependencies (Python 3.9+ standard library only).
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from core.assistant import Assistant

ROOT = Path(__file__).resolve().parent
BOT = Assistant()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._send(200, (ROOT / "static" / "index.html").read_bytes(), "text/html")
        if path == "/api/faculty":
            return self._send(200, BOT.faculty.all())
        if path == "/api/dashboard":
            return self._send(200, BOT.dashboard())
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/chat":
            return self._send(404, {"error": "not found"})
        try:
            n = min(int(self.headers.get("Content-Length", 0)), 10_000)
            msg = json.loads(self.rfile.read(n) or b"{}").get("message", "")
        except (ValueError, json.JSONDecodeError):
            return self._send(400, {"error": "bad request"})
        self._send(200, BOT.handle(msg))

    def log_message(self, *args):  # keep console quiet; no raw text is logged
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"AIUB Campus Companion running at http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
