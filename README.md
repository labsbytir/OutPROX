# OutPROX — universal egress router

One exit for APIs, scrapers, firewalls. Targets see provider IPs, never yours.

Providers: **Bright Data** (all proxy types + all countries) and **Webshare**
(direct/backbone). Callers pick vars (provider/country/type/mode); router injects
them into the request. No credentials in code.

## Quick use (append to a form/script)

```python
from outprox import fetch, patch_env
patch_env(provider="brightdata", country="us")  # uses env creds
print(fetch("https://geo.brdtest.com/welcome.txt?product=isp&method=native").decode())
```

```python
# Webshare instead — same call, different vars
print(fetch("https://example.com", provider="webshare", mode="backbone").decode())
```

```python
# Spider Cloud with YOUR exit as remote_proxy (50% data-transfer saving,
# still runs Spider's browser/render/markdown pipeline)
from outprox import spider_scrape
print(spider_scrape("https://example.com", provider="brightdata", country="us"))
```

## Env

```bash
cp .env.example .env  # then fill secrets
export BRIGHTDATA_PASSWORD='...'      # required for brightdata
export BRIGHTDATA_CUSTOMER=hl_e5e462d9
export BRIGHTDATA_ZONE=isp_proxy1
export WEBSHARE_USERNAME='...' WEBSHARE_PASSWORD='...'  # required for webshare
export SPIDER_API_KEY='...'  # required for via=spider (/scrape, /crawl remote_proxy)
python3 -m outprox.server  # :8080 -> /options, GET/POST /fetch
```

## Pass-through server

- `GET /options` → providers, Bright Data types, countries, Webshare modes (feeds dropdowns)
- `GET /fetch?url=...&provider=brightdata&country=us` → body
- `GET /fetch?url=...&via=spider&endpoint=scrape&provider=brightdata&country=us` → Spider JSON (remote_proxy injected)
- `POST /fetch` JSON `{url, method, body?, headers?, provider?, country?, ...}` → body
- `POST /fetch` JSON `{url, via:"spider", endpoint:"scrape"|"crawl", provider?, country?, spider_params?}` → Spider JSON
- `harness.html` → drop-in dropdowns + GET/POST form

## Container (Podman + Wolfi)

```bash
/opt/podman/bin/podman build -f Containerfile -t outprox .
/opt/podman/bin/podman run --env-file .env -p 8080:8080 outprox
```

## Docs

- Bright Data: `brd.superproxy.io:44445`, user `brd-customer-{id}-zone-{zone}[-country-{cc}...]`
- Webshare: backbone `p.webshare.io:80`, direct via `proxy/list/?mode=direct` address+port
