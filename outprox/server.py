"""Stdlib pass-through server (no deps).

Routes: GET /fetch, POST /fetch|/scrape|/crawl|/scrapers/*, GET /options|/stats|/healthz
Auth: set OUTPROX_TOKEN; every route except / and /healthz needs
`Authorization: Bearer <token>`. Unset = open dev mode.
Metering: in-memory counters at GET /stats + JSON lines at $OUTPROX_LOG.
"""
import hmac
import json
import os
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from .chain import fetch_chain, scrape_chain
from .providers import options
from .router import fetch
from .scrapers import crawl as scraper_crawl
from .scrapers import run as scraper_run
from .scrapers import scrape as scraper_scrape
from .spider import scrape as spider_scrape

STATS = {"requests": 0, "errors": 0, "bytes_in": 0, "bytes_out": 0, "by_route": {}}


def _meter(route, label, status, bytes_in, bytes_out, ms):
    STATS["requests"] += 1
    STATS["bytes_in"] += bytes_in
    STATS["bytes_out"] += bytes_out
    key = f"{route}:{label}"
    bucket = STATS["by_route"].setdefault(key, {"n": 0, "err": 0, "out": 0})
    bucket["n"] += 1
    bucket["out"] += bytes_out
    if status >= 400:
        STATS["errors"] += 1
        bucket["err"] += 1
    path = os.environ.get("OUTPROX_LOG", "")
    if path:
        try:
            with open(path, "a") as f:
                f.write(json.dumps({
                    "ts": time.time(), "route": route, "label": label,
                    "status": status, "in": bytes_in, "out": bytes_out, "ms": ms,
                }) + "\n")
        except OSError:
            pass


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self):
        want = os.environ.get("OUTPROX_TOKEN", "")
        if not want:
            return True
        got = self.headers.get("Authorization", "")
        return hmac.compare_digest(got, f"Bearer {want}")

    def _guard(self):
        if self._auth():
            return True
        self._json({"error": "unauthorized"}, 401)
        return False

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/", "/healthz"):
            return self._json({"ok": True, "service": "outprox"})
        if not self._guard():
            return
        if parsed.path == "/options":
            return self._json(options())
        if parsed.path == "/stats":
            return self._json(STATS)
        if parsed.path == "/fetch":
            t0 = time.time()
            q = urllib.parse.parse_qs(parsed.query)
            url = (q.get("url") or [None])[0]
            if not url:
                _meter("fetch", "none", 400, 0, 0, 0)
                return self._json({"error": "missing ?url="}, 400)
            proxy_kw = {k: v[0] for k, v in q.items() if k != "url" and v}
            label = proxy_kw.get("provider", "brightdata")
            via = proxy_kw.pop("via", "direct")
            try:
                if via == "spider":
                    endpoint = proxy_kw.pop("endpoint", "scrape")
                    res = self._json(spider_scrape(url, endpoint=endpoint, **proxy_kw))
                    _meter("fetch", f"spider/{label}", 200, 0, 0,
                           int((time.time() - t0) * 1000))
                    return res
                body = fetch(url, method="GET", **proxy_kw)
            except Exception as e:  # noqa: BLE001 - surface as JSON
                _meter("fetch", label, 502, 0, 0, int((time.time() - t0) * 1000))
                return self._json({"error": str(e)}, 502)
            _meter("fetch", label, 200, 0, len(body), int((time.time() - t0) * 1000))
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if not self._guard():
            return
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "scrapers":
            return self._backend(parts[1], parts[2])
        if parsed.path in ("/scrape", "/crawl"):
            return self._scraper(parsed.path.lstrip("/"))
        if parsed.path != "/fetch":
            return self._json({"error": "not found"}, 404)
        t0 = time.time()
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:  # noqa: BLE001
            return self._json({"error": f"bad json: {e}"}, 400)
        url = payload.pop("url", None)
        method = payload.pop("method", "POST")
        data = payload.pop("body", None)
        headers = payload.pop("headers", None)
        via = payload.pop("via", "direct")
        chain = payload.pop("chain", None)
        if via == "spider":
            if not url:
                return self._json({"error": "missing url"}, 400)
            try:
                endpoint = payload.pop("endpoint", "scrape")
                spider_params = payload.pop("spider_params", None)
                res = self._json(spider_scrape(
                    url, endpoint=endpoint, spider_params=spider_params, **payload))
                _meter("fetch", "spider", 200, length, 0,
                       int((time.time() - t0) * 1000))
                return res
            except Exception as e:  # noqa: BLE001
                _meter("fetch", "spider", 502, length, 0,
                       int((time.time() - t0) * 1000))
                return self._json({"error": str(e)}, 502)
        if not url:
            _meter("fetch", "none", 400, length, 0, 0)
            return self._json({"error": "missing url"}, 400)
        raw = data.encode() if isinstance(data, str) else data
        try:
            if chain:
                body, _ = fetch_chain(url, chain, method=method, data=raw,
                                     headers=headers)
                label = "chain"
            else:
                label = payload.get("provider", "brightdata")
                body = fetch(url, method=method, data=raw, headers=headers, **payload)
        except Exception as e:  # noqa: BLE001
            _meter("fetch", "chain" if chain else payload.get("provider", "?"),
                   502, length, 0, int((time.time() - t0) * 1000))
            return self._json({"error": str(e)}, 502)
        _meter("fetch", label, 200, length, len(body), int((time.time() - t0) * 1000))
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"{}"), length, None
        except Exception as e:  # noqa: BLE001
            return None, length, str(e)

    def _scraper(self, endpoint):
        t0 = time.time()
        payload, length, err = self._read_json()
        if err:
            return self._json({"error": f"bad json: {err}"}, 400)
        url = payload.pop("url", None)
        if not url:
            _meter(endpoint, "spider", 400, length, 0, 0)
            return self._json({"error": "missing url"}, 400)
        spider_params = payload.pop("spider_params", None)
        chain = payload.pop("chain", None)
        label = f"spider/{payload.get('provider', 'default')}"
        fn = scraper_scrape if endpoint == "scrape" else scraper_crawl
        try:
            if chain:
                res, _ = scrape_chain(url, chain, backend="spider",
                                     endpoint=endpoint, spider_params=spider_params)
            else:
                res = fn(url, spider_params=spider_params, **payload)
        except Exception as e:  # noqa: BLE001
            _meter(endpoint, label, 502, length, 0, int((time.time() - t0) * 1000))
            return self._json({"error": str(e)}, 502)
        _meter(endpoint, label, 200, length, 0, int((time.time() - t0) * 1000))
        return self._json(res)

    def _backend(self, backend, endpoint):
        t0 = time.time()
        payload, length, err = self._read_json()
        if err:
            return self._json({"error": f"bad json: {err}"}, 400)
        url = payload.pop("url", None)
        if not url:
            _meter("scrapers", backend, 400, length, 0, 0)
            return self._json({"error": "missing url"}, 400)
        try:
            res = scraper_run(backend, endpoint, url, **payload)
        except Exception as e:  # noqa: BLE001
            _meter("scrapers", backend, 502, length, 0,
                   int((time.time() - t0) * 1000))
            return self._json({"error": str(e)}, 502)
        _meter("scrapers", backend, 200, length, 0, int((time.time() - t0) * 1000))
        return self._json(res)

    def log_message(self, *a):  # quieter logs
        pass


def main(port: int = 8080):
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main(int(os.environ.get("PORT", "8080")))
