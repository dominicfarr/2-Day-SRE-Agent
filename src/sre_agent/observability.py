"""Structured JSON logging shared by every toy-system service.

One line per request: printed to stdout, and appended to
LOG_DIR/<service>.jsonl. Read fresh from the environment on every
write, not cached at import time, so a test (or a future Chaos Toggle)
can change it without restarting the process.
"""

import json
import logging
import os
import sys
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, Request, Response


def configure_logging() -> None:
    """Silences uvicorn's own access log; this module replaces it."""
    logging.getLogger("uvicorn.access").disabled = True


def log_dir() -> Path:
    return Path(os.environ.get("LOG_DIR", "logs"))


def write_log_line(service: str, fields: dict[str, object]) -> None:
    line = {"timestamp": datetime.now(UTC).isoformat(), "service": service, **fields}
    serialized = json.dumps(line, sort_keys=True)
    print(serialized, file=sys.stdout, flush=True)

    directory = log_dir()
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / f"{service}.jsonl").open("a") as handle:
        handle.write(serialized + "\n")


def add_request_logging(app: FastAPI, service_name: str) -> None:
    """Logs every request except /health, which Docker polls constantly."""

    @app.middleware("http")
    async def _log_requests(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            write_log_line(
                service_name,
                {
                    "version": os.environ.get("SERVICE_VERSION", "v1"),
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                    "level": "error" if status_code >= 500 else "info",
                },
            )
