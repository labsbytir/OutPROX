# outprox spec

## ADDED Requirements

### Requirement: Decodo exit
Router SHALL build Decodo backconnect URLs from username + geo vars.

#### Scenario: City session
- WHEN build_proxy_url(provider=decodo, country=us, city=New York, session=a1)
- THEN http://user-alice-country-us-city-new_york-session-a1:...@gate.decodo.com:7000
