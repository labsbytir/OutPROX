# OutPROX universal egress router

## Why
APIs, scrapers, and firewalls need one exit so targets never see server IPs.
Must support Bright Data (all types + countries) and Webshare via pass-through vars.

## What
- Universal `outprox` package: `build_proxy_url` / `fetch` / `patch_env` for brightdata + webshare
- Stdlib pass-through server: `GET /options`, `GET/POST /fetch`
- `harness.html` dropdowns (provider, Bright Data type, country, Webshare mode) + GET/POST form
- Universal README + `.env.example`, Wolfi Containerfile for Podman

## Out of scope
- Live credential testing (needs user secrets), per-proxy rotation pools, auth proxy UI
