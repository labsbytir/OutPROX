"""OutPROX - universal egress router."""
from .providers import (
    BRIGHTDATA_COUNTRIES,
    BRIGHTDATA_PROXY_TYPES,
    PROVIDERS,
    SPIDER_ENDPOINTS,
    VIAS,
    WEBSHARE_MODES,
    build_proxy_url,
    options,
)
from .router import (
    build_opener,
    fetch,
    get_requests_proxies,
    patch_env,
)
from .spider import scrape as spider_scrape
from .scrapers import crawl as scraper_crawl
from .scrapers import run as scraper_run
from .scrapers import scrape as scraper_scrape
from .chain import fetch_chain, scrape_chain
from .registry import (
    provider_names,
    register_provider,
    register_scraper,
    run_scraper,
    scraper_backends,
)

__all__ = [
    "BRIGHTDATA_COUNTRIES",
    "BRIGHTDATA_PROXY_TYPES",
    "PROVIDERS",
    "SPIDER_ENDPOINTS",
    "VIAS",
    "WEBSHARE_MODES",
    "build_proxy_url",
    "build_opener",
    "fetch",
    "get_requests_proxies",
    "options",
    "patch_env",
    "spider_scrape",
    "scraper_crawl",
    "scraper_scrape",
    "scraper_run",
    "fetch_chain",
    "scrape_chain",
    "provider_names",
    "register_provider",
    "register_scraper",
    "run_scraper",
    "scraper_backends",
]
