import pytest
from fastapi.testclient import TestClient

from sre_agent.services.payments_service import main as payments_service


@pytest.fixture(autouse=True)
def _reset_chaos_mode() -> None:
    payments_service._chaos_mode = "normal"


@pytest.fixture
def client() -> TestClient:
    return TestClient(payments_service.app)


def _patch_fast_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(payments_service.asyncio, "sleep", fake_sleep)


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_chaos_rejects_unknown_mode(client: TestClient) -> None:
    response = client.post("/chaos", json={"mode": "not-a-real-mode"})
    assert response.status_code == 400


def test_charge_succeeds_in_normal_mode(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_fast_sleep(monkeypatch)

    response = client.post("/charge")

    assert response.status_code == 200
    assert response.json() == {"status": "charged"}


def test_charge_fails_in_outage_mode_above_the_error_rate(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    client.post("/chaos", json={"mode": "outage"})
    _patch_fast_sleep(monkeypatch)
    monkeypatch.setattr(payments_service.random, "random", lambda: 0.0)

    response = client.post("/charge")

    assert response.status_code == 503


def test_charge_can_still_succeed_in_outage_mode_below_the_error_rate(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    client.post("/chaos", json={"mode": "outage"})
    _patch_fast_sleep(monkeypatch)
    monkeypatch.setattr(payments_service.random, "random", lambda: 0.99)

    response = client.post("/charge")

    assert response.status_code == 200
