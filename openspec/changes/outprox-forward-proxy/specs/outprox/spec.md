# outprox spec

## ADDED Requirements

### Requirement: Forward proxy door
Server SHALL accept standard proxy clients and exit via selected provider.

#### Scenario: No token
- WHEN CONNECT without Proxy-Authorization and OUTPROX_TOKEN set
- THEN 407 with Proxy-Authenticate header

#### Scenario: Upstream truth
- WHEN upstream exit refuses CONNECT with 402
- THEN client receives 402, not a masked 502
