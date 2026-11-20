"""Spider Cloud BYO proxy: inject our exit URL as remote_proxy.

Requests still run Spider's browser/render/markdown pipeline; BYO proxy
saves ~50% data-transfer vs Spider's pool. Secrets from env only.
"""
import json
import os
import urllib.request
from typing import Optional

from .providers import build_proxy_url
from .registry import register_scraper

SPIDER_ENDPOINTS = ["scrape", "crawl"]


def scrape(
    url: str,
    remote_proxy: Optional[str] = None,
    endpoint: str = "scrape",
    api_key: Optional[str] = None,
    spider_params: Optional[dict] = None,
    timeout: int = 120,
    **proxy_kw,
):
    """POST url to Spider /scrape (or /crawl) with remote_proxy injected."""
    if endpoint not in SPIDER_ENDPOINTS:
        raise ValueError(f"unknown endpoint {endpoint!r}; pick {SPIDER_ENDPOINTS}")
    key = api_key or os.environ.get("SPIDER_API_KEY", "")
    if not key:
        raise RuntimeError("Set SPIDER_API_KEY env var")
    proxy = remote_proxy or build_proxy_url(**proxy_kw)
    base = os.environ.get("SPIDER_BASE", "https://api.spider.cloud")
    body = {"url": url, "remote_proxy": proxy, **(spider_params or {})}
    req = urllib.request.Request(
        f"{base}/{endpoint}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.build_opener().open(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


register_scraper("spider", SPIDER_ENDPOINTS, scrape)
