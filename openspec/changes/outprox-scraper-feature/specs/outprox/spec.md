# outprox spec

## ADDED Requirements

### Requirement: Separate scraper routes
Server SHALL expose POST /scrape and POST /crawl as scraper-only routes.

#### Scenario: Scrape route validates input
- WHEN POST /crawl with {}
- THEN 400 {"error": "missing url"}

#### Scenario: Unknown routes 404
- WHEN POST /nope
- THEN 404 {"error": "not found"}
