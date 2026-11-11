"""
Generate three realistic sample log files so you can see the merger
work immediately. Each file is sorted chronologically. The merged
output interleaves them by timestamp.

Writes nginx.log, app.log, auth.log in the current folder.

Usage:
    python generate_sample_logs.py
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta


RNG = random.Random(42)
START = datetime(2026, 11, 11, 9, 0, 0)


def _lines_for(service: str, count: int, spread_seconds: int) -> list[str]:
    """Generate `count` sorted log lines over the given time spread."""
    offsets = sorted(RNG.sample(range(spread_seconds), count))
    templates = {
        "nginx": [
            "GET /api/users 200",
            "GET /api/products 200",
            "POST /api/orders 201",
            "GET /health 200",
            "GET /static/app.css 304",
            "POST /api/orders 500",
            "GET /dashboard 200",
        ],
        "app": [
            "handling request to /api/users",
            "database connection established",
            "cache miss for key=session:abc",
            "queued background job #12",
            "slow query detected (1.2s)",
            "exception in request handler",
            "shutdown signal received",
        ],
        "auth": [
            "user halemaa logged in",
            "user alice logged in",
            "failed login attempt from 203.0.113.5",
            "session expired for user alice",
            "password reset requested by halemaa",
            "SSH key rotated for root",
        ],
    }
    picks = templates[service]
    lines: list[str] = []
    for off in offsets:
        when = START + timedelta(seconds=off)
        msg = RNG.choice(picks)
        lines.append(f"{when:%Y-%m-%d %H:%M:%S}  {service}  {msg}")
    return lines


def main() -> None:
    for service, count in (("nginx", 15), ("app", 10), ("auth", 8)):
        lines = _lines_for(service, count, spread_seconds=60)
        path = f"{service}.log"
        with open(path, "w", encoding="utf-8") as fh:
            for ln in lines:
                fh.write(ln + "\n")
        print(f"Wrote {path} ({count} entries)")


if __name__ == "__main__":
    main()
