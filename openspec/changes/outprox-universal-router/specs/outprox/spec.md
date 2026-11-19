# outprox spec

## ADDED Requirements

### Requirement: Universal exit
Router SHALL route all egress via selected provider with secrets from env only.

#### Scenario: Bright Data fetch
- WHEN caller calls fetch(url, provider=brightdata, country=us) with BRIGHTDATA_PASSWORD set
- THEN request egresses via brd.superproxy.io:44445

#### Scenario: Webshare fetch
- WHEN caller calls fetch(url, provider=webshare, mode=backbone) with WEBSHARE creds set
- THEN request egresses via p.webshare.io

### Requirement: Pass-through vars
Server SHALL inject caller-chosen vars into the proxy URL per request.

#### Scenario: Per-request country
- WHEN GET /fetch?url=X&provider=brightdata&country=gb
- THEN response body is fetched via GB exit

### Requirement: Harness UI
Harness SHALL offer dropdowns sourced from GET /options plus GET/POST send.

#### Scenario: Dropdowns load
- WHEN harness.html loads /options
- THEN provider, Bright Data types/countries, Webshare modes populate
