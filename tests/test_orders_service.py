import httpx
import pytest
from fastapi.testclient import TestClient

from sre_agent.services.orders_service import main as orders_service


@pytest.fixture(autouse=True)
def _reset_chaos_mode() -> None:
    orders_service._chaos_mode = "normal"


@pytest.fixture
def client() -> TestClient:
    return TestClient(orders_service.app)


def _patch_fast_sleep(monkeypatch: pytest.MonkeyPatch, calls: list[float]) -> None:
    async def fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    monkeypatch.setattr(orders_service.asyncio, "sleep", fake_sleep)


def _patch_successful_payment(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_post(url: str, *args: object, **kwargs: object) -> httpx.Response:
        return httpx.Response(200, json={"status": "charged"}, request=httpx.Request("POST", url))

    monkeypatch.setattr(orders_service._client, "post", fake_post)


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_chaos_mode_round_trips(client: TestClient) -> None:
    assert client.get("/chaos").json() == {"mode": "normal"}

    response = client.post("/chaos", json={"mode": "config_drift"})

    assert response.json() == {"mode": "config_drift"}
    assert client.get("/chaos").json() == {"mode": "config_drift"}


def test_chaos_rejects_unknown_mode(client: TestClient) -> None:
    response = client.post("/chaos", json={"mode": "not-a-real-mode"})
    assert response.status_code == 400


def test_v1_does_not_sleep_for_the_regression(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SERVICE_VERSION", "v1")
    sleep_calls: list[float] = []
    _patch_fast_sleep(monkeypatch, sleep_calls)
    _patch_successful_payment(monkeypatch)

    client.get("/orders")

    assert sleep_calls == []


def test_v2_sleeps_for_the_regression(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_VERSION", "v2")
    sleep_calls: list[float] = []
    _patch_fast_sleep(monkeypatch, sleep_calls)
    _patch_successful_payment(monkeypatch)

    client.get("/orders")

    assert sleep_calls == [orders_service._V2_REGRESSION_LATENCY_S]


def test_config_drift_sleeps_independent_of_version(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SERVICE_VERSION", "v1")
    client.post("/chaos", json={"mode": "config_drift"})
    sleep_calls: list[float] = []
    _patch_fast_sleep(monkeypatch, sleep_calls)
    _patch_successful_payment(monkeypatch)

    client.get("/orders")

    assert sleep_calls == [orders_service._CONFIG_DRIFT_LATENCY_S]


def test_returns_502_when_payments_service_unavailable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SERVICE_VERSION", "v1")

    async def fake_post(url: str, *args: object, **kwargs: object) -> httpx.Response:
        raise httpx.ConnectError("refused", request=httpx.Request("POST", url))

    monkeypatch.setattr(orders_service._client, "post", fake_post)

    response = client.get("/orders")

    assert response.status_code == 502
