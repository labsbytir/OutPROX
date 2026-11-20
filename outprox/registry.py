"""Plugin registry: add a proxy provider or scraper backend without touching core.

Copy templates/new_provider.py or templates/new_scraper.py into outprox/
(or any importable module), fill the blanks, and it self-registers on import.
"""
from typing import Callable, Dict, List

PROVIDER_BUILDERS: Dict[str, Callable[..., str]] = {}
SCRAPER_BACKENDS: Dict[str, dict] = {}


def register_provider(name: str, fn: Callable[..., str]) -> None:
    PROVIDER_BUILDERS[name] = fn


def register_scraper(name: str, endpoints: List[str], fn: Callable) -> None:
    SCRAPER_BACKENDS[name] = {"endpoints": list(endpoints), "run": fn}


def provider_names() -> List[str]:
    return list(PROVIDER_BUILDERS)


def scraper_backends() -> Dict[str, List[str]]:
    return {n: b["endpoints"] for n, b in SCRAPER_BACKENDS.items()}


def run_scraper(backend: str, endpoint: str, url: str, **kw):
    """Dispatch to any registered scraper backend. Raises ValueError if unknown."""
    try:
        b = SCRAPER_BACKENDS[backend]
    except KeyError:
        raise ValueError(
            f"unknown scraper backend {backend!r}; pick {list(SCRAPER_BACKENDS)}"
        )
    if endpoint not in b["endpoints"]:
        raise ValueError(f"unknown endpoint {endpoint!r}; pick {b['endpoints']}")
    return b["run"](url, endpoint=endpoint, **kw)
