# OutPROX Spider BYO proxy

## Why
Spider Cloud accepts `remote_proxy: protocol://user:pass@host:port` on /scrape and /crawl.
Routing Spider through our Bright Data / Webshare exit keeps one origin-hidden
exit, keeps Spider's browser/render/markdown pipeline, and saves ~50% data-transfer.

## What
- `outprox/spider.py`: `scrape(url, remote_proxy?, endpoint=scrape|crawl, spider_params?)`;
  builds remote_proxy via existing universal builder when not passed directly
- Server: `via=spider` on GET /fetch and POST /fetch returns Spider JSON
- Harness: via + Spider-endpoint dropdowns sourced from /options
- README + `.env.example` (SPIDER_API_KEY)

## Out of scope
- Live Spider calls (needs credits; key present but API returned 402)
- Per-proxy rotation pools, Spider AI/unlimited routes
