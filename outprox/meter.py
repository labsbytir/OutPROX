"""Shared request metering for REST + forward proxy."""
import time

STATS = {"requests": 0, "errors": 0, "bytes_in": 0, "bytes_out": 0, "by_route": {}}


def _meter(route, label, status, bytes_in, bytes_out, ms=None):
    if ms is None:
        ms = 0
    STATS["requests"] += 1
    STATS["bytes_in"] += bytes_in
    STATS["bytes_out"] += bytes_out
    key = f"{route}:{label}"
    bucket = STATS["by_route"].setdefault(key, {"n": 0, "err": 0, "out": 0})
    bucket["n"] += 1
    bucket["out"] += bytes_out
    if status >= 400:
        STATS["errors"] += 1
        bucket["err"] += 1
    import json
    import os
    path = os.environ.get("OUTPROX_LOG", "")
    if path:
        try:
            with open(path, "a") as f:
                f.write(json.dumps({
                    "ts": time.time(), "route": route, "label": label,
                    "status": status, "in": bytes_in, "out": bytes_out, "ms": ms,
                }) + "\n")
        except OSError:
            pass
