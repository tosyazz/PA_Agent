"""Snapshot cache TTL for HTTP data sources.

Continuous polling has been removed; this module only keeps the short-lived
cache used by the HTTP A-share source to avoid duplicate identical requests.
"""
from __future__ import annotations

HTTP_SNAPSHOT_CACHE_TTL_S = 8.0
HTTP_SNAPSHOT_CACHE_TTL_1D_S = 12.0


def snapshot_cache_ttl_s(timeframe: str) -> float:
    if timeframe in ("1d", "1w", "1M"):
        return HTTP_SNAPSHOT_CACHE_TTL_1D_S
    if timeframe == "1m":
        return 4.0
    return HTTP_SNAPSHOT_CACHE_TTL_S
