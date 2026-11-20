# outprox spec

## ADDED Requirements

### Requirement: Spider exit provider
Router SHALL build Spider proxy URLs from key + country vars.

#### Scenario: German exit
- WHEN build_proxy_url(provider=spider, country=de) with SPIDER_API_KEY set
- THEN http://KEY:country_code=de@proxy.spider.cloud:8888

#### Scenario: Missing key
- WHEN provider=spider without SPIDER_API_KEY
- THEN RuntimeError naming the env var
