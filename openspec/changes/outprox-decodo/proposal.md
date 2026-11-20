# OutPROX Decodo provider

## Why
Decodo (residential + mobile + datacenter + ISP pools) is a fourth exit.
Built as a plugin module to prove the registry path end to end.

## What
- outprox/decodo.py: user-USER-country-CC-... @ gate.decodo.com:7000 builder
- Curated provider order in /options (built-ins first, plugins appended)

## Out of scope
- Live Decodo traffic (needs account creds); non-residential endpoint mapping
