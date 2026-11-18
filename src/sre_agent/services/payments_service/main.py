"""payments-service: the downstream dependency orders-service calls.

Chaos Toggle: POST /chaos {"mode": "normal" | "outage"} flips in-memory
behaviour without touching the Deploy Ledger, per ADR 0001 -- so an
outage here must never look like a deploy to anything reading the
ledger.
"""

import asyncio
import random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sre_agent.observability import add_request_logging, configure_logging

SERVICE_NAME = "payments-service"
_OUTAGE_LATENCY_S = 1.5
_OUTAGE_ERROR_RATE = 0.6

configure_logging()
app = FastAPI(title=SERVICE_NAME)
add_request_logging(app, SERVICE_NAME)

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
    if body.mode not in {"normal", "outage"}:
        raise HTTPException(status_code=400, detail=f"unknown chaos mode: {body.mode}")
    _chaos_mode = body.mode
    return {"mode": _chaos_mode}


@app.post("/charge")
async def charge() -> dict[str, str]:
    if _chaos_mode == "outage":
        await asyncio.sleep(_OUTAGE_LATENCY_S)
        if random.random() < _OUTAGE_ERROR_RATE:
            raise HTTPException(status_code=503, detail="payments provider unavailable")
    else:
        await asyncio.sleep(0.02)
    return {"status": "charged"}
