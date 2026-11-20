"""TEMPLATE: add a new scraper backend. Copy to outprox/my_scraper.py and fill in.

Steps:
  1. cp templates/new_scraper.py outprox/acme_scraper.py
  2. Rename run + edit the POST below (auth, body, base URL)
  3. register_scraper("acme", ["scrape", "crawl"], run)
  4. Import it once at startup: `import outprox.acme_scraper  # noqa` in outprox/__init__.py
  5. Done: POST /scrapers/acme/scrape, harness backend dropdown, run_scraper("acme", ...).
"""
import json
import os
import urllib.request
from typing import Optional

from .registry import register_scraper


def run(url: str, endpoint: str = "scrape", remote_proxy: Optional[str] = None,
         params: Optional[dict] = None, timeout: int = 120, **kw):
    """Run url through this backend. remote_proxy = our exit URL (or None)."""
    key = kw.get("api_key") or os.environ.get("ACME_API_KEY", "")
    if not key:
        raise RuntimeError("Set ACME_API_KEY env var")
    base = os.environ.get("ACME_BASE", "https://api.acme.example")
    body = {"url": url, **(params or {})}
    if remote_proxy:
        body["remote_proxy"] = remote_proxy  # drop if backend has no BYO proxy
    req = urllib.request.Request(
        f"{base}/{endpoint}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.build_opener().open(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


register_scraper("acme", ["scrape", "crawl"], run)
