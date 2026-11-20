"""Fallback chains: ordered exits, first success wins. Caller orders the chain
(cheapest first, fastest first, home-country first — your call per request)."""
from typing import Optional

from .router import fetch
from .scrapers import run as scraper_run


def fetch_chain(url: str, chain: list, method: str = "GET", data: Optional[bytes] = None,
               headers: Optional[dict] = None, timeout: int = 30):
    """Try each link {provider, country, ...} in order. Returns (body, used_index)."""
    last: Exception = RuntimeError("empty chain")
    for i, link in enumerate(chain):
        try:
            return fetch(url, method=method, data=data, headers=headers,
                         timeout=timeout, **link), i
        except Exception as e:  # noqa: BLE001 - try next exit
            last = e
    raise last


def scrape_chain(url: str, chain: list, backend: str = "spider",
                 endpoint: str = "scrape", **kw):
    """Same idea for scraper backends. kw holds backend params (spider_params)."""
    last: Exception = RuntimeError("empty chain")
    for i, link in enumerate(chain):
        try:
            return scraper_run(backend, endpoint, url, **{**link, **kw}), i
        except Exception as e:  # noqa: BLE001 - try next exit
            last = e
    raise last
