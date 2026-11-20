# OutPROX plugin template for scrapers and proxies

## Why
New scraper backends and proxy providers should be 10-line additions, not core edits.

## What
- `outprox/registry.py`: register_provider/register_scraper, run_scraper dispatch
- `templates/new_provider.py`, `templates/new_scraper.py` copy-paste starters
- `POST /scrapers/{backend}/{endpoint}` generic route; /options lists backends
- Harness Scrapers form gets backend dropdown; README documents the flow

## Out of scope
- Migrating existing providers off their modules (they register in place)
