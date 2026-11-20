"""Provider catalog + universal proxy-URL builder.

Vars are pass-through: caller picks provider/country/type, we inject into URL.
No credentials hardcoded — all secrets come from env or explicit args.
"""
import os
import urllib.parse
from typing import Optional

from .registry import (
    PROVIDER_BUILDERS,
    provider_names,
    register_provider,
    scraper_backends,
)

PROVIDERS = ["brightdata", "webshare", "spider"]
VIAS = ["direct", "spider"]
SPIDER_ENDPOINTS = ["scrape", "crawl"]
# Spider proxy front-end: HTTP :8888, HTTPS :8889, SOCKS5 :8887
SPIDER_PROXY_PORTS = {"http": "8888", "https": "8889", "socks5": "8887"}

# Bright Data proxy families (docs: residential/ipv4, mega ipv4+ipv6, ipv6,
# dedicated, datacenter, isp). Host/port identical (native 44445); type is a
# routing hint recorded on the zone, selection enforced via zone name.
BRIGHTDATA_PROXY_TYPES = [
    "isp",
    "residential-ipv4",
    "residential-mega",
    "residential-ipv6",
    "residential-dedicated",
    "datacenter",
    "datacenter-dedicated",
]

# Full ISO-3166 list published in Bright Data FAQs (not every code has peers,
# most do). Lowercase to match `-country-XX` username params.
BRIGHTDATA_COUNTRIES = (
    "af al dz as ad ao ai aq ag ar am aw au at az bs bh bd bb by be bz bj bm bt "
    "bo bq ba bw bv br io bn bg bf bi cv kh cm ca ky cf td cl cn cx cc co km cg cd "
    "ck cr ci hr cu cw cy cz dk dj dm do ec eg sv gq er ee sz et fk fo fj fi fr gf "
    "pf tf ga gm ge de gh gi gr gl gd gp gu gt gg gn gw gy ht hm va hn hk hu is "
    "in id ir iq ie im il it jm je jo kz ke ki kp kr kw kg la lv lb ls lr ly li "
    "lt lu mo mg mw my mv ml mt mh mq mr mu yt mx fm md mc mn me ms ma mz mm na "
    "nr np nl nc nz ni ne ng nu nf mp no om pk pw ps pa pg py pe ph pn pl pt pr "
    "qa mk ro rw re bl sh kn lc mf pm vc ws sm st sa sn rs sc sl sg sx sk si sb "
    "so za gs ss es lk sd sr sj sz se ch sy tw tj tz th tl tg tk to tt tn tr tm "
    "tc tv ug ua ae gb us um uy uz vu va ve vn vg vi wf eh ye zm zw ax"
).split()

WEBSHARE_MODES = ["direct", "backbone"]
WEBSHARE_POOLS = ["datacenter", "residential", "static-residential"]


def build_proxy_url(
    provider: Optional[str] = None,
    password: Optional[str] = None,
    **kw,
) -> str:
    provider = (provider or os.environ.get("OUTPROX_PROVIDER", "brightdata")).lower()
    try:
        build = PROVIDER_BUILDERS[provider]
    except KeyError:
        raise ValueError(f"unknown provider {provider!r}; pick {provider_names()}")
    return build(password, **kw)


def _brightdata_url(password: Optional[str] = None, **kw) -> str:
    pwd = password or os.environ.get("BRIGHTDATA_PASSWORD", "")
    if not pwd or "replace" in pwd or "[" in pwd:
        raise RuntimeError("Set BRIGHTDATA_PASSWORD env var")
    customer = kw.get("customer") or os.environ.get("BRIGHTDATA_CUSTOMER", "hl_e5e462d9")
    zone = kw.get("zone") or os.environ.get("BRIGHTDATA_ZONE", "isp_proxy1")
    country = (kw.get("country") or os.environ.get("BRIGHTDATA_COUNTRY", "")).lower()
    user = f"brd-customer-{customer}-zone-{zone}"
    if country:
        user += f"-country-{country}"
    for key in ("state", "city", "zip", "asn", "session"):
        v = kw.get(key) or os.environ.get(f"BRIGHTDATA_{key.upper()}", "")
        if v:
            user += f"-{key}-{v}"
    host = os.environ.get("BRIGHTDATA_HOST", "brd.superproxy.io")
    port = os.environ.get("BRIGHTDATA_PORT", "44445")
    return f"http://{user}:{urllib.parse.quote(pwd, safe='')}@{host}:{port}"


def _spider_proxy_url(password: Optional[str] = None, **kw) -> str:
    """Spider residential proxy: key as user, params (country_code, ...) as password."""
    key = kw.get("api_key") or os.environ.get("SPIDER_API_KEY", "")
    if not key:
        raise RuntimeError("Set SPIDER_API_KEY env var")
    params = []
    country = (kw.get("country") or os.environ.get("SPIDER_COUNTRY", "")).lower()
    if country:
        params.append(f"country_code={country}")
    trackers = kw.get("trackers_disabled", os.environ.get("SPIDER_TRACKERS_DISABLED", ""))
    if trackers != "":
        params.append(f"trackers_disabled={str(trackers).lower()}")
    # shortcut: limit of this join is Spider only documents single-param use —
    # multi-param separator unconfirmed, country-only is the safe path
    userinfo = key + (":" + ";".join(params) if params else ":")
    host = os.environ.get("SPIDER_PROXY_HOST", "proxy.spider.cloud")
    port = kw.get("port") or os.environ.get("SPIDER_PROXY_PORT", "8888")
    return f"http://{userinfo}@{host}:{port}"


def _webshare_url(password: Optional[str] = None, **kw) -> str:
    mode = (kw.get("mode") or os.environ.get("WEBSHARE_MODE", "backbone")).lower()
    user = kw.get("username") or os.environ.get("WEBSHARE_USERNAME", "")
    pwd = password or os.environ.get("WEBSHARE_PASSWORD", "")
    if not user or not pwd:
        raise RuntimeError("Set WEBSHARE_USERNAME + WEBSHARE_PASSWORD env vars")
    if mode == "backbone":
        host = os.environ.get("WEBSHARE_HOST", "p.webshare.io")
        port = kw.get("port") or os.environ.get("WEBSHARE_PORT", "80")
        return f"http://{user}:{urllib.parse.quote(pwd, safe='')}@{host}:{port}"
    # direct: per-proxy address from list API (proxy.webshare.io/api/v2/proxy/list/?mode=direct)
    host = kw.get("proxy_address") or os.environ.get("WEBSHARE_PROXY_ADDRESS", "")
    port = kw.get("port") or os.environ.get("WEBSHARE_PORT_DIRECT", "")
    if not host or not port:
        raise RuntimeError("direct mode needs proxy_address + port (see Webshare list API)")
    return f"http://{user}:{urllib.parse.quote(pwd, safe='')}@{host}:{port}"


def options() -> dict:
    return {
        "providers": provider_names() or PROVIDERS,
        "features": ["fetch", "scrapers"],
        "vias": VIAS,
        "spider_endpoints": SPIDER_ENDPOINTS,
        "scraper_backends": scraper_backends(),
        "brightdata_proxy_types": BRIGHTDATA_PROXY_TYPES,
        "brightdata_countries": BRIGHTDATA_COUNTRIES,
        "webshare_modes": WEBSHARE_MODES,
        "webshare_pools": WEBSHARE_POOLS,
        "spider_proxy_ports": SPIDER_PROXY_PORTS,
    }


register_provider("brightdata", _brightdata_url)
register_provider("webshare", _webshare_url)
register_provider("spider", _spider_proxy_url)
