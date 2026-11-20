"""Forward proxy: one server your own tools connect to.

Point anything at us (`curl -x`, `HTTP_PROXY`, browsers) and we exit through
your providers. Per-request exit via proxy userinfo:

    http://{provider}[-{country}[-{session}]]:{token}@host:8888

No userinfo -> env defaults (OUTPROX_PROVIDER/COUNTRY/...). Password is
OUTPROX_TOKEN when set. Plain-HTTP (absolute-form) is fetched through the
exit and relayed; HTTPS (CONNECT) is chained upstream and relayed as bytes.
"""
import base64
import os
import select
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .meter import _meter
from .providers import build_proxy_url, parse_proxy_url

HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
       "proxy-connection", "te", "trailer", "transfer-encoding", "upgrade"}


def split_userinfo(user):
    """'provider-country-session...' -> exit kw. Empty -> {} (env defaults)."""
    bits = (user or "").split("-")
    if not bits or not bits[0]:
        return {}
    kw = {"provider": bits[0]}
    rest = bits[1:]
    if rest and len(rest[0]) == 2:
        kw["country"] = rest[0]
        rest = rest[1:]
    if rest:
        kw["session"] = "-".join(rest)
    return kw


def _relay(a, b, timeout=300):
    end = time.time() + timeout
    for s in (a, b):
        try:
            s.settimeout(max(1, int(end - time.time())))
        except OSError:
            return
    while time.time() < end:
        try:
            r, _, _ = select.select([a, b], [], [], 30)
        except (OSError, ValueError):
            return
        if not r:
            continue
        for s in r:
            try:
                data = s.recv(65536)
            except OSError:
                return
            if not data:
                return
            try:
                (b if s is a else a).sendall(data)
            except OSError:
                return


class ForwardHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "OutPROX/1"

    def _creds(self):
        auth = self.headers.get("Proxy-Authorization", "")
        if auth.startswith("Basic "):
            try:
                user, _, token = base64.b64decode(auth[6:]).decode().partition(":")
                return user, token
            except Exception:  # noqa: BLE001
                pass
        return "", ""

    def _deny(self):
        self.send_response(407, "Proxy Authentication Required")
        self.send_header("Proxy-Authenticate", 'Basic realm="outprox"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _exit(self, user):
        return build_proxy_url(**split_userinfo(user))

    def do_CONNECT(self):
        t0 = time.time()
        user, token = self._creds()
        want = os.environ.get("OUTPROX_TOKEN", "")
        if want and token != want:
            self._deny()
            return
        host_port = self.path
        if ":" not in host_port:
            host_port += ":443"
        try:
            exit_url = self._exit(user)
            _, up_host, up_port, up_user, up_pass = parse_proxy_url(exit_url)
            up = socket.create_connection((up_host, up_port or 8080), timeout=20)
            req = f"CONNECT {host_port} HTTP/1.1\r\nHost: {host_port}\r\n"
            if up_user:
                cred = base64.b64encode(f"{up_user}:{up_pass}".encode()).decode()
                req += f"Proxy-Authorization: Basic {cred}\r\n"
            req += "\r\n"
            up.sendall(req.encode())
            resp = b""
            while b"\r\n\r\n" not in resp:
                chunk = up.recv(4096)
                if not chunk:
                    break
                resp += chunk
            if not resp.split(b" ", 2)[1].startswith(b"2"):
                try:
                    self.connection.sendall(resp)
                except OSError:
                    pass
                _meter("proxy", "connect", 502, 0, len(resp),
                       int((time.time() - t0) * 1000))
                up.close()
                return
            self.send_response(200, "Connection established")
            self.end_headers()
            ms = int((time.time() - t0) * 1000)
            _meter("proxy", f"connect:{split_userinfo(user).get('provider', 'default')}",
                   200, 0, 0, ms)
            _relay(self.connection, up)
            up.close()
        except Exception as e:  # noqa: BLE001 - surface as 502
            try:
                self.send_error(502, f"exit failed: {e}")
            except OSError:
                pass
            _meter("proxy", "connect", 502, 0, 0, int((time.time() - t0) * 1000))

    def _forward(self):
        t0 = time.time()
        user, token = self._creds()
        want = os.environ.get("OUTPROX_TOKEN", "")
        if want and token != want:
            self._deny()
            return
        if not self.path.startswith(("http://", "https://")):
            self.send_error(404, "proxy-only port; use absolute-form URLs")
            return
        kw = split_userinfo(user)
        label = kw.get("provider", "default")
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length) if length else None
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in HOP and k.lower() != "host"}
        try:
            exit_url = build_proxy_url(**kw)
            opener = urllib.request.build_opener(urllib.request.ProxyHandler(
                {"http": exit_url, "https": exit_url}))
            req = urllib.request.Request(self.path, data=data, headers=headers,
                                         method=self.command)
            try:
                res = opener.open(req, timeout=60)
                status, rheaders, body = res.status, res.headers, res.read()
            except urllib.error.HTTPError as e:
                status, rheaders, body = e.code, e.headers, e.read()
        except Exception as e:  # noqa: BLE001
            _meter("proxy", label, 502, length, 0, int((time.time() - t0) * 1000))
            try:
                self.send_error(502, f"exit failed: {e}")
            except OSError:
                pass
            return
        ms = int((time.time() - t0) * 1000)
        _meter("proxy", label, status, length, len(body), ms)
        try:
            self.send_response(status)
            for k, v in (rheaders or {}).items():
                if k.lower() not in HOP and k.lower() != "content-length":
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except OSError:
            pass

    do_GET = _forward
    do_POST = _forward
    do_PUT = _forward
    do_DELETE = _forward
    do_PATCH = _forward
    do_HEAD = _forward
    do_OPTIONS = _forward

    def log_message(self, *a):
        pass


def serve_forever(port: int = 8888):
    ThreadingHTTPServer(("0.0.0.0", port), ForwardHandler).serve_forever()


if __name__ == "__main__":
    serve_forever(int(os.environ.get("OUTPROX_PROXY_PORT", "8888")))
