"""Stdlib pass-through server (no deps). GET/POST /fetch, GET /options."""
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from .providers import options
from .router import fetch


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/options":
            return self._json(options())
        if parsed.path in ("/", "/healthz"):
            return self._json({"ok": True, "service": "outprox"})
        if parsed.path == "/fetch":
            q = urllib.parse.parse_qs(parsed.query)
            url = (q.get("url") or [None])[0]
            if not url:
                return self._json({"error": "missing ?url="}, 400)
            proxy_kw = {k: v[0] for k, v in q.items() if k != "url" and v}
            try:
                body = fetch(url, method="GET", **proxy_kw)
            except Exception as e:  # noqa: BLE001 - surface as JSON
                return self._json({"error": str(e)}, 502)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return self._json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/fetch":
            return self._json({"error": "not found"}, 404)
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:  # noqa: BLE001
            return self._json({"error": f"bad json: {e}"}, 400)
        url = payload.pop("url", None)
        method = payload.pop("method", "POST")
        data = payload.pop("body", None)
        headers = payload.pop("headers", None)
        proxy_kw = payload  # rest = pass-through vars (provider/country/zone/...)
        if not url:
            return self._json({"error": "missing url"}, 400)
        try:
            body = fetch(
                url,
                method=method,
                data=data.encode() if isinstance(data, str) else data,
                headers=headers,
                **proxy_kw,
            )
        except Exception as e:  # noqa: BLE001
            return self._json({"error": str(e)}, 502)
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # quieter logs
        pass


def main(port: int = 8080):
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    import os

    main(int(os.environ.get("PORT", "8080")))
