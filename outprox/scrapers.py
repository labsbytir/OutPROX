"""Separate scraper feature: Spider /scrape and /crawl with our exit as remote_proxy.

Unlike generic /fetch (raw GET/POST through the exit), these routes run the
full Spider pipeline (browser/render/markdown) for scraper workloads.
"""
from typing import Optional

from .providers import build_proxy_url
from .registry import run_scraper
from .spider import scrape as _spider


def scrape(url: str, spider_params: Optional[dict] = None, **proxy_kw):
    """One page through Spider /scrape with our exit injected as remote_proxy."""
    return _spider(url, endpoint="scrape", spider_params=spider_params, **proxy_kw)


def crawl(url: str, spider_params: Optional[dict] = None, **proxy_kw):
    """Site crawl through Spider /crawl with our exit injected as remote_proxy."""
    return _spider(url, endpoint="crawl", spider_params=spider_params, **proxy_kw)


def run(backend: str, endpoint: str, url: str, remote_proxy: Optional[str] = None,
        use_exit: bool = True, **kw):
    """Run url through ANY registered scraper backend.

    backend: "spider" (more via templates/new_scraper.py). endpoint: backend's
    route, e.g. scrape/crawl. Unless remote_proxy is given (or use_exit=False),
    our universal exit URL is built from kw (provider/country/...) and injected.
    Backend-specific params (e.g. spider_params) pass through untouched.
    """
    if remote_proxy is None and use_exit:
        exit_kw = {k: v for k, v in kw.items()
                   if k not in ("spider_params", "params")}
        remote_proxy = build_proxy_url(**exit_kw)
    return run_scraper(backend, endpoint, url, remote_proxy=remote_proxy, **kw)
