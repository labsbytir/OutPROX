"""Decodo exit provider (residential default; other pools via host/port override).

Format per docs: user-USERNAME[-country-CC][-city-NAME][-state-US_X]...
@ gate.decodo.com:7000. Secrets from env only.
"""
import os
import urllib.parse
from typing import Optional

from .registry import register_provider

# Pools from Decodo quick-start index; residential is fully mapped here,
# others reuse the same auth scheme with their own endpoint via kw/env.
DECODO_TYPES = [
    "residential",
    "mobile",
    "datacenter-pay-gb",
    "datacenter-pay-ip",
    "isp-pay-gb",
    "isp-pay-ip",
    "dedicated-isp",
    "dedicated-dc",
]


def _decodo_url(password: Optional[str] = None, **kw) -> str:
    user = kw.get("username") or os.environ.get("DECODO_USERNAME", "")
    pwd = password or os.environ.get("DECODO_PASSWORD", "")
    if not user or not pwd:
        raise RuntimeError("Set DECODO_USERNAME + DECODO_PASSWORD env vars")
    parts = [f"user-{user}"]
    country = (kw.get("country") or os.environ.get("DECODO_COUNTRY", "")).lower()
    if country:
        parts.append(f"country-{country}")
    city = (kw.get("city") or "").strip().replace(" ", "_").lower()
    if city:
        parts.append(f"city-{city}")
    for key in ("state", "zip", "asn", "continent", "session", "sessionduration"):
        v = kw.get(key) or os.environ.get(f"DECODO_{key.upper()}", "")
        if v:
            parts.append(f"{key}-{v}")
    host = kw.get("host") or os.environ.get("DECODO_HOST", "gate.decodo.com")
    port = kw.get("port") or os.environ.get("DECODO_PORT", "7000")
    return f"http://{'-'.join(parts)}:{urllib.parse.quote(pwd, safe='')}@{host}:{port}"


register_provider("decodo", _decodo_url)
