# outprox spec

## ADDED Requirements

### Requirement: Plugin registry
New providers/scrapers SHALL register without core edits.

#### Scenario: Dummy plugin round-trip
- WHEN register_provider/register_scraper called for "acme"
- THEN build_proxy_url(provider=acme) and run_scraper(acme, ...) dispatch to it

#### Scenario: Generic scraper route
- WHEN POST /scrapers/nope/scrape with valid exit creds
- THEN 502 naming the unknown backend
