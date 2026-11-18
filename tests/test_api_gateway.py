import httpx
import pytest
from fastapi.testclient import TestClient

from sre_agent.services.api_gateway import main as api_gateway


@pytest.fixture
def client() -> TestClient:
    return TestClient(api_gateway.app)


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_orders_proxies_orders_service(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(url: str, *args: object, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            200,
            json={"orders": [{"id": 1, "status": "paid"}]},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(api_gateway._client, "get", fake_get)

    response = client.get("/orders")

    assert response.status_code == 200
    assert response.json() == {"orders": [{"id": 1, "status": "paid"}]}


def test_orders_returns_502_when_orders_service_unreachable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_get(url: str, *args: object, **kwargs: object) -> httpx.Response:
        raise httpx.ConnectError("refused", request=httpx.Request("GET", url))

    monkeypatch.setattr(api_gateway._client, "get", fake_get)

    response = client.get("/orders")

    assert response.status_code == 502
