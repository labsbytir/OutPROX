# outprox spec

## ADDED Requirements

### Requirement: Spider BYO exit
Router SHALL inject the universal exit URL as Spider remote_proxy.

#### Scenario: Scrape via Bright Data exit
- WHEN spider_scrape(url, provider=brightdata, country=us) with SPIDER_API_KEY set
- THEN POST api.spider.cloud/scrape includes remote_proxy with brd.superproxy.io exit

### Requirement: Server via switch
Server SHALL route via=spider requests to Spider and return Spider JSON.

#### Scenario: GET fetch via spider
- WHEN GET /fetch?url=X&via=spider&endpoint=scrape&provider=brightdata
- THEN response is Spider JSON, not raw body
