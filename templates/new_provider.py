"""TEMPLATE: add a new proxy provider. Copy to outprox/my_provider.py and fill in.

Steps:
  1. cp templates/new_provider.py outprox/acme.py
  2. Rename _acme_url + edit host/auth/params below
  3. from outprox.registry import register_provider; register_provider("acme", _acme_url)
  4. Import it once at startup: `import outprox.acme  # noqa` in outprox/__init__.py
  5. Done: provider="acme" works in fetch(), /fetch, harness, and as remote_proxy.
"""
import os
import urllib.parse
from typing import Optional

from .registry import register_provider


def _acme_url(password: Optional[str] = None, **kw) -> str:
    user = kw.get("username") or os.environ.get("ACME_USERNAME", "")
    pwd = password or os.environ.get("ACME_PASSWORD", "")
    if not user or not pwd:
        raise RuntimeError("Set ACME_USERNAME + ACME_PASSWORD env vars")
    host = os.environ.get("ACME_HOST", "proxy.acme.example")
    port = kw.get("port") or os.environ.get("ACME_PORT", "8080")
    country = (kw.get("country") or "").lower()
    if country:
        user = f"{user}-country-{country}"  # adapt to your provider's format
    return f"http://{user}:{urllib.parse.quote(pwd, safe='')}@{host}:{port}"


register_provider("acme", _acme_url)
