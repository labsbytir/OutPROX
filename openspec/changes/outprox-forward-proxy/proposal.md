# OutPROX as a connectable forward proxy

## Why
Tools (curl, browsers, scrapers) should point at one OutPROX server and get
provider exits with zero code changes, instead of speaking the REST API.

## What
- outprox/forward.py on OUTPROX_PROXY_PORT (8888): absolute-form HTTP relay
  + CONNECT chaining upstream; userinfo selects exit, token enforced (407)
- providers.parse_proxy_url; meter.py shared by REST + forward
- python3 -m outprox.server runs both doors; README/.env/tests updated

## Out of scope
- Live exit traffic (Spider pool returns account 402; chain verified to relay it)
