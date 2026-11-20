# OutPROX Spider as proxy provider

## Why
Spider runs a residential proxy pool (proxy.spider.cloud, 199+ countries) alongside
its scrape API. Adding it as a third exit provider keeps one universal builder.

## What
- `provider=spider`: key as user, `country_code` (+ trackers_disabled) as password,
  host proxy.spider.cloud, ports 8888/8889/8887
- Document provider=spider (exit) vs via=spider (scrape API) distinction

## Out of scope
- Live traffic through Spider pool (metered $2/GB); Webshare direct-pool parity
