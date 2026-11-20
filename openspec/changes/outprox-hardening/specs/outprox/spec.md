# outprox spec

## ADDED Requirements

### Requirement: Router auth
Server SHALL reject unauthenticated non-health routes when OUTPROX_TOKEN is set.

#### Scenario: Missing token
- WHEN GET /options without Authorization with OUTPROX_TOKEN set
- THEN 401 {"error": "unauthorized"}

#### Scenario: Open health
- WHEN GET /healthz without Authorization
- THEN 200 regardless of token

### Requirement: Metering
Server SHALL count requests/bytes/errors per route.

#### Scenario: Stats shape
- WHEN GET /stats with valid token
- THEN JSON with requests, errors, bytes_in, bytes_out, by_route

### Requirement: Fallback chains
Library and server SHALL try ordered exits until one succeeds.

#### Scenario: Empty chain
- WHEN fetch_chain(url, [])
- THEN RuntimeError
