"""orders-service: calls payments-service to fulfil an order.

Two independent causes can produce the same symptom (elevated latency):
v2's regression (a genuine slow query, baked into the image) and the
Config Drift Chaos Toggle (a behaviour change with no deploy behind
it). Per PLAN.md's Rollback and escalation policy, only the first of
those should ever lead to a rollback -- see ADR 0001.
"""

import asyncio
import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sre_agent.observability import add_request_logging, configure_logging

SERVICE_NAME = "orders-service"
_V2_REGRESSION_LATENCY_S = 0.6
_CONFIG_DRIFT_LATENCY_S = 0.4

configure_logging()
app = FastAPI(title=SERVICE_NAME)
add_request_logging(app, SERVICE_NAME)

_client = httpx.AsyncClient(timeout=10.0)
_chaos_mode = "normal"


class ChaosRequest(BaseModel):
    mode: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/chaos")
def get_chaos() -> dict[str, str]:
    return {"mode": _chaos_mode}


@app.post("/chaos")
def set_chaos(body: ChaosRequest) -> dict[str, str]:
    global _chaos_mode
    if body.mode not in {"normal", "config_drift"}:
        raise HTTPException(status_code=400, detail=f"unknown chaos mode: {body.mode}")
    _chaos_mode = body.mode
    return {"mode": _chaos_mode}


@app.get("/orders")
async def list_orders() -> dict[str, object]:
    if os.environ.get("SERVICE_VERSION", "v1") == "v2":
        await asyncio.sleep(_V2_REGRESSION_LATENCY_S)

    if _chaos_mode == "config_drift":
        await asyncio.sleep(_CONFIG_DRIFT_LATENCY_S)

    payments_url = os.environ.get("PAYMENTS_SERVICE_URL", "http://localhost:8000")
    try:
        payment = await _client.post(f"{payments_url}/charge")
        payment.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="payments-service unavailable") from exc

    return {"orders": [{"id": 1, "status": "paid"}]}
