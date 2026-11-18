"""api-gateway: the toy system's entrypoint, proxying to orders-service."""

import os

import httpx
from fastapi import FastAPI, HTTPException

from sre_agent.observability import add_request_logging, configure_logging

SERVICE_NAME = "api-gateway"

configure_logging()
app = FastAPI(title=SERVICE_NAME)
add_request_logging(app, SERVICE_NAME)

_client = httpx.AsyncClient(timeout=10.0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/orders")
async def get_orders() -> dict[str, object]:
    orders_url = os.environ.get("ORDERS_SERVICE_URL", "http://localhost:8000")
    try:
        resp = await _client.get(f"{orders_url}/orders")
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="orders-service unavailable") from exc
    return resp.json()
