"""Separate scraper feature: Spider /scrape and /crawl with our exit as remote_proxy.

Unlike generic /fetch (raw GET/POST through the exit), these routes run the
full Spider pipeline (browser/render/markdown) for scraper workloads.
"""
from typing import Optional

from .spider import scrape as _spider


def scrape(url: str, spider_params: Optional[dict] = None, **proxy_kw):
    """One page through Spider /scrape with our exit injected as remote_proxy."""
    return _spider(url, endpoint="scrape", spider_params=spider_params, **proxy_kw)


def crawl(url: str, spider_params: Optional[dict] = None, **proxy_kw):
    """Site crawl through Spider /crawl with our exit injected as remote_proxy."""
    return _spider(url, endpoint="crawl", spider_params=spider_params, **proxy_kw)
