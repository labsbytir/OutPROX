# OutPROX hardening: auth, metering, fallback, tests, CI

## Why
Open proxy spend needs protection (auth), visibility (metering), resilience
(fallback chains), and proof (tests + CI) before more traffic flows through.

## What
- OUTPROX_TOKEN bearer auth on all routes except / and /healthz
- GET /stats counters + OUTPROX_LOG JSON-lines metering
- outprox/chain.py: fetch_chain/scrape_chain over caller-ordered exits;
  POST /fetch|/scrape|/crawl accept "chain"
- tests/test_outprox.py (unittest, stdlib only) + GitHub CI on 3.9-3.12
- Harness token field; README/.env.example updates

## Out of scope
- Per-caller quotas/billing; sticky sessions; served-at-/ harness hosting
