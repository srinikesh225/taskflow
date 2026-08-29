"""A minimal in-memory fixed-window rate limiter.

Sufficient for a single-process lab deployment. For multi-worker / multi-host
production, back this with Redis instead.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max = max_attempts
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str, now: float) -> deque[float]:
        dq = self._hits[key]
        while dq and now - dq[0] > self.window:
            dq.popleft()
        return dq

    def is_allowed(self, key: str) -> bool:
        """True if `key` is under the limit right now (does not record a hit)."""
        return len(self._prune(key, time.monotonic())) < self.max

    def record(self, key: str) -> None:
        now = time.monotonic()
        self._prune(key, now).append(now)

    def reset(self) -> None:
        self._hits.clear()


# Limits *failed* login attempts per client IP.
login_rate_limiter = RateLimiter(max_attempts=10, window_seconds=60)
