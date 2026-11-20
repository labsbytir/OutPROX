"""OutPROX test suite. Stdlib unittest, no deps: python3 -m unittest discover -s tests."""
import json
import os
import threading
import unittest
import urllib.request
from http.server import HTTPServer

os.environ["BRIGHTDATA_PASSWORD"] = "dummy"
os.environ["WEBSHARE_USERNAME"] = "u"
os.environ["WEBSHARE_PASSWORD"] = "p"
os.environ["SPIDER_API_KEY"] = "dummykey"

from outprox import (  # noqa: E402
    build_proxy_url,
    fetch_chain,
    options,
    register_provider,
    register_scraper,
    run_scraper,
    scraper_backends,
    scraper_run,
)
from outprox.server import Handler  # noqa: E402
from outprox.forward import ForwardHandler, split_userinfo  # noqa: E402
from outprox.providers import parse_proxy_url  # noqa: E402


class TestBuilders(unittest.TestCase):
    def test_brightdata(self):
        u = build_proxy_url(provider="brightdata", country="us")
        self.assertIn("brd-customer-hl_e5e462d9-zone-isp_proxy1-country-us", u)
        self.assertTrue(u.endswith("@brd.superproxy.io:44445"))

    def test_webshare(self):
        self.assertEqual(build_proxy_url(provider="webshare", mode="backbone"),
                         "http://u:p@p.webshare.io:80")

    def test_spider(self):
        self.assertEqual(build_proxy_url(provider="spider", country="de"),
                         "http://dummykey:country_code=de@proxy.spider.cloud:8888")

    def test_unknown_provider(self):
        with self.assertRaises(ValueError):
            build_proxy_url(provider="nope")

    def test_decodo(self):
        os.environ["DECODO_USERNAME"] = "alice"
        os.environ["DECODO_PASSWORD"] = "s3cret"
        try:
            self.assertEqual(build_proxy_url(provider="decodo"),
                             "http://user-alice:s3cret@gate.decodo.com:7000")
            self.assertEqual(build_proxy_url(provider="decodo", country="it"),
                             "http://user-alice-country-it:s3cret@gate.decodo.com:7000")
            self.assertIn("session-x1", build_proxy_url(
                provider="decodo", country="us", session="x1", sessionduration="90"))
        finally:
            os.environ.pop("DECODO_USERNAME", None)
            os.environ.pop("DECODO_PASSWORD", None)

    def test_decodo_missing_secret(self):
        os.environ.pop("DECODO_USERNAME", None)
        os.environ.pop("DECODO_PASSWORD", None)
        with self.assertRaises(RuntimeError):
            build_proxy_url(provider="decodo")

    def test_missing_secret(self):
        os.environ.pop("BRIGHTDATA_PASSWORD", None)
        try:
            with self.assertRaises(RuntimeError):
                build_proxy_url(provider="brightdata")
        finally:
            os.environ["BRIGHTDATA_PASSWORD"] = "dummy"


class TestRegistry(unittest.TestCase):
    def test_plugin_round_trip(self):
        register_provider("tprov", lambda password=None, **kw: "http://tprov-exit")
        register_scraper("tscrape", ["go"],
                         lambda url, endpoint="go", **kw: {"url": url, "via": kw.get("remote_proxy")})
        self.assertEqual(build_proxy_url(provider="tprov"), "http://tprov-exit")
        res = scraper_run("tscrape", "go", "https://example.com",
                          provider="brightdata", country="us")
        self.assertIn("brd.superproxy.io", res["via"])
        with self.assertRaises(ValueError):
            run_scraper("nope", "go", "https://example.com")
        with self.assertRaises(ValueError):
            run_scraper("tscrape", "nope", "https://example.com")

    def test_chain_empty(self):
        with self.assertRaises(RuntimeError):
            fetch_chain("https://example.com", [])


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["OUTPROX_TOKEN"] = "test-token"
        cls.srv = HTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.srv.server_address[1]
        cls.t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.t.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        os.environ.pop("OUTPROX_TOKEN", None)

    def _get(self, path, token=True):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}")
        if token:
            req.add_header("Authorization", "Bearer test-token")
        try:
            with urllib.request.build_opener().open(req, timeout=5) as r:
                return r.status, r.read()
        except Exception as e:
            return getattr(e, "code", 0), e.read() if hasattr(e, "read") else b""

    def _post(self, path, payload):
        data = json.dumps(payload).encode()
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data,
                                     headers={"Authorization": "Bearer test-token",
                                              "Content-Type": "application/json"})
        try:
            with urllib.request.build_opener().open(req, timeout=5) as r:
                return r.status, r.read()
        except Exception as e:
            return getattr(e, "code", 0), e.read() if hasattr(e, "read") else b""

    def test_healthz_open(self):
        code, _ = self._get("/healthz", token=False)
        self.assertEqual(code, 200)

    def test_options_needs_auth(self):
        code, _ = self._get("/options", token=False)
        self.assertEqual(code, 401)

    def test_options_ok(self):
        code, body = self._get("/options")
        self.assertEqual(code, 200)
        o = json.loads(body)
        self.assertIn("spider", o["providers"])
        self.assertIn("spider", o["scraper_backends"])

    def test_stats_shape(self):
        code, body = self._get("/stats")
        self.assertEqual(code, 200)
        self.assertIn("requests", json.loads(body))

    def test_scrape_missing_url(self):
        code, body = self._post("/scrape", {"provider": "brightdata"})
        self.assertEqual(code, 400)
        self.assertIn("missing url", body.decode())

    def test_unknown_route(self):
        code, _ = self._post("/nope", {})
        self.assertEqual(code, 404)

    def test_unknown_backend(self):
        code, body = self._post("/scrapers/nope/scrape",
                                {"url": "https://example.com", "provider": "brightdata"})
        self.assertEqual(code, 502)
        self.assertIn("unknown scraper backend", body.decode())


class TestForwardParsing(unittest.TestCase):
    def test_split_userinfo(self):
        from outprox.forward import split_userinfo
        self.assertEqual(split_userinfo(""), {})
        self.assertEqual(split_userinfo("spider"), {"provider": "spider"})
        self.assertEqual(split_userinfo("brightdata-us"),
                         {"provider": "brightdata", "country": "us"})
        self.assertEqual(split_userinfo("decodo-gb-sess1"),
                         {"provider": "decodo", "country": "gb", "session": "sess1"})

    def test_parse_proxy_url(self):
        scheme, host, port, user, pwd = parse_proxy_url(
            "http://u-abc-country-us:p%40ss@brd.superproxy.io:44445")
        self.assertEqual((scheme, host, port, user, pwd),
                         ("http", "brd.superproxy.io", 44445, "u-abc-country-us", "p@ss"))


class TestForwardProxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from http.server import ThreadingHTTPServer
        os.environ["OUTPROX_TOKEN"] = "fwd-token"
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ForwardHandler)
        cls.port = cls.srv.server_address[1]
        cls.t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.t.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        os.environ.pop("OUTPROX_TOKEN", None)

    def _raw(self, req):
        import socket
        s = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        s.sendall(req)
        out = b""
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                out += chunk
                if len(out) > 65536:
                    break
        except (OSError, socket.timeout):
            pass
        s.close()
        return out.split(b"\r\n", 1)[0]

    def test_connect_no_token_denied(self):
        line = self._raw(b"CONNECT example.com:443 HTTP/1.1\r\nHost: example.com\r\n\r\n")
        self.assertIn(b"407", line)

    def test_connect_bad_provider_502(self):
        import base64
        cred = base64.b64encode(b"nope-us:fwd-token").decode()
        line = self._raw(f"CONNECT example.com:443 HTTP/1.1\r\nHost: example.com\r\nProxy-Authorization: Basic {cred}\r\n\r\n".encode())
        self.assertTrue(line.startswith(b"HTTP/1.1 502") or b"502" in line)

    def test_absolute_form_no_token_denied(self):
        line = self._raw(b"GET http://example.com/ HTTP/1.1\r\nHost: example.com\r\n\r\n")
        self.assertIn(b"407", line)


if __name__ == "__main__":
    unittest.main()
