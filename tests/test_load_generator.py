import httpx

from sre_agent.services.load_generator import main as load_generator


class _FakeClient:
    def __init__(self) -> None:
        self.requested_urls: list[str] = []

    def get(self, url: str) -> httpx.Response:
        self.requested_urls.append(url)
        return httpx.Response(200, request=httpx.Request("GET", url))


class _FailingClient:
    def get(self, url: str) -> httpx.Response:
        raise httpx.ConnectError("refused", request=httpx.Request("GET", url))


def test_make_request_hits_the_orders_endpoint() -> None:
    client = _FakeClient()

    load_generator.make_request(client, "http://api-gateway:8000")

    assert client.requested_urls == ["http://api-gateway:8000/orders"]


def test_make_request_swallows_http_errors() -> None:
    load_generator.make_request(_FailingClient(), "http://api-gateway:8000")
