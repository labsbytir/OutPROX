# OutPROX — universal egress router

One exit for APIs, scrapers, firewalls. Targets see provider IPs, never yours.

Providers: **Bright Data** (all proxy types + all countries), **Webshare**
(direct/backbone), **Spider** (`proxy.spider.cloud`, 199+ countries), and
**Decodo** (`gate.decodo.com:7000`, country/city/session targeting). Callers pick vars
(provider/country/type/mode); router injects them into the request.
No credentials in code.

Note: `provider=spider` = exit through Spider's proxy pool.
`via=spider` = run through Spider's scrape/crawl API (any exit as `remote_proxy`).

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
export SPIDER_API_KEY='...'  # required for provider=spider AND via=spider
# optional: SPIDER_COUNTRY=us SPIDER_PROXY_PORT=8888 (http) / 8889 (https)
OUTPROX_TOKEN=''  # set to require `Authorization: Bearer` on all routes but /healthz
OUTPROX_LOG=''    # set to a path for JSON-lines request metering
PORT=8080
```

## Pass-through server

- `GET /options` → providers, features, backends, types, countries, modes (feeds dropdowns)
- `GET /stats` → request/byte/error counters by route (who burns the GBs)
- `GET /fetch?url=...&provider=brightdata&country=us` → body
- `GET /fetch?url=...&via=spider&endpoint=scrape&provider=brightdata&country=us` → Spider JSON (remote_proxy injected)
- `POST /fetch` JSON `{url, method, body?, headers?, provider?, country?, ...}` → body
- `POST /fetch` JSON `{url, via:"spider", endpoint:"scrape"|"crawl", provider?, country?, spider_params?}` → Spider JSON
- `POST /fetch` JSON `{url, chain:[{provider, country, ...}, ...]}` → first exit that succeeds
- Auth: set `OUTPROX_TOKEN`, send `Authorization: Bearer <token>` (harness has a field)

## Scrapers (separate feature)

- `POST /scrape` JSON `{url, provider?, country?, spider_params?}` → Spider /scrape JSON
- `POST /crawl` JSON `{url, provider?, country?, spider_params?}` → Spider /crawl JSON
- `POST /scrapers/{backend}/{endpoint}` → any registered backend (generic)
- Python: `from outprox import scraper_scrape, scraper_crawl, scraper_run`
- Harness has a separate Scrapers form (backend + endpoint dropdowns)

## Adding more scrapers or proxies (template)

Copy a template, fill the blanks, import once — no core changes:

```bash
cp templates/new_provider.py outprox/acme.py   # edit host/auth, keep register_provider("acme", ...)
cp templates/new_scraper.py outprox/acme_scraper.py  # edit POST, keep register_scraper("acme", [...], run)
```

```python
# outprox/__init__.py — one line each so they self-register at startup
import outprox.acme  # noqa
import outprox.acme_scraper  # noqa
```

Then `provider="acme"` works in `fetch()`/`/fetch`/harness, and
`POST /scrapers/acme/scrape` + `scraper_run("acme", "scrape", url, ...)` work.

## Fallback chains (cheapest/fastest — your order)

```python
from outprox import fetch_chain
body, i = fetch_chain("https://example.com", [
    {"provider": "brightdata", "country": "us"},
    {"provider": "spider", "country": "de"},
])  # i = which link succeeded
```

Server: `POST /fetch` with `"chain": [...]` instead of flat vars; same for
`POST /scrape|/crawl` (chain of exits into Spider).

## Tests + CI

```bash
python3 -m unittest discover -s tests -v
```

`.github/workflows/ci.yml` runs compile + unittest on Python 3.9–3.12 for
`sandbox`/`main` pushes and PRs.
- `harness.html` → drop-in dropdowns + GET/POST form

## Container (Podman + Wolfi)

```bash
/opt/podman/bin/podman build -f Containerfile -t outprox .
/opt/podman/bin/podman run --env-file .env -p 8080:8080 outprox
```

## Docs

- Bright Data: `brd.superproxy.io:44445`, user `brd-customer-{id}-zone-{zone}[-country-{cc}...]`
- Webshare: backbone `p.webshare.io:80`, direct via `proxy/list/?mode=direct` address+port
- Spider: `proxy.spider.cloud:8888`, user = API key, password = `country_code=xx`
- Decodo: `gate.decodo.com:7000`, user `user-NAME[-country-CC][-city-..][-session-..]`, plain password
