"""OutPROX - universal egress router."""
from .providers import (
    BRIGHTDATA_COUNTRIES,
    BRIGHTDATA_PROXY_TYPES,
    PROVIDERS,
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

__all__ = [
    "BRIGHTDATA_COUNTRIES",
    "BRIGHTDATA_PROXY_TYPES",
    "PROVIDERS",
    "WEBSHARE_MODES",
    "build_proxy_url",
    "build_opener",
    "fetch",
    "get_requests_proxies",
    "options",
    "patch_env",
]
