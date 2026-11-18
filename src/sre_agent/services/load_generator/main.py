"""Drives continuous traffic against api-gateway so logs/metrics aren't empty.

Swallows transport errors on purpose: during an injected incident the
target is genuinely failing or slow, and the load generator must keep
going so there's still traffic to observe while that's happening.
"""

import os
import random
import time
from typing import Protocol

import httpx


class _HttpClient(Protocol):
    def get(self, url: str) -> httpx.Response: ...


def make_request(client: _HttpClient, target_url: str) -> None:
    try:
        client.get(f"{target_url}/orders")
    except httpx.HTTPError:
        pass


def main() -> None:
    target_url = os.environ.get("TARGET_URL", "http://localhost:8000")
    min_interval_s = float(os.environ.get("LOAD_MIN_INTERVAL_S", "0.2"))
    max_interval_s = float(os.environ.get("LOAD_MAX_INTERVAL_S", "1.0"))

    client = httpx.Client(timeout=10.0)
    while True:
        make_request(client, target_url)
        time.sleep(random.uniform(min_interval_s, max_interval_s))


if __name__ == "__main__":
    main()
