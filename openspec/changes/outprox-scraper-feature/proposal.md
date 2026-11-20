# OutPROX scrapers as a separate feature

## Why
Scraper workloads (Spider /scrape, /crawl with remote_proxy) deserve their own
routes and harness section, distinct from generic GET/POST /fetch passthrough.

## What
- `outprox/scrapers.py`: `scrape()` and `crawl()` wrappers over spider BYO
- Server: dedicated `POST /scrape`, `POST /crawl` (keep `via=spider` on /fetch)
- Harness: separate Scrapers form posting to /scrape or /crawl
- `/options` advertises `features: [fetch, scrapers]`

## Out of scope
- Live Spider calls (key exists but API returns 402, needs funding)
