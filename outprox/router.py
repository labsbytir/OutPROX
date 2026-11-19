"""Universal GET/POST pass-through. Caller chooses vars, we inject proxy."""
import os
import urllib.request
from typing import Optional

from .providers import build_proxy_url


def get_proxy_url(**kw) -> str:
    return build_proxy_url(**kw)


def build_opener(**kw):
    proxy = build_proxy_url(**kw)
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    )


def fetch(
    url: str,
    method: str = "GET",
    data: Optional[bytes] = None,
    headers: Optional[dict] = None,
    timeout: int = 30,
    **proxy_kw,
) -> bytes:
    """GET/POST (or any method) through the selected exit. Returns raw body."""
    req = urllib.request.Request(
        url, data=data, headers=headers or {}, method=method.upper()
    )
    return build_opener(**proxy_kw).open(req, timeout=timeout).read()


def get_requests_proxies(**kw) -> dict:
    proxy = build_proxy_url(**kw)
    return {"http": proxy, "https": proxy}


def patch_env(**kw) -> str:
    proxy = build_proxy_url(**kw)
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy
    return proxy
