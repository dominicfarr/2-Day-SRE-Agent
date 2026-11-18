import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sre_agent.observability import add_request_logging


def _build_app() -> FastAPI:
    app = FastAPI()
    add_request_logging(app, "test-service")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/widgets")
    def widgets() -> dict[str, str]:
        return {"widgets": "none"}

    return app


def test_health_check_is_not_logged(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    client = TestClient(_build_app())

    client.get("/health")

    assert not (tmp_path / "test-service.jsonl").exists()


def test_request_is_logged_as_one_json_line(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    client = TestClient(_build_app())

    response = client.get("/widgets")

    assert response.status_code == 200
    lines = (tmp_path / "test-service.jsonl").read_text().splitlines()
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["service"] == "test-service"
    assert entry["path"] == "/widgets"
    assert entry["status_code"] == 200
    assert entry["level"] == "info"
    assert "duration_ms" in entry
    assert "timestamp" in entry

    stdout_lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(stdout_lines) == 1
    assert json.loads(stdout_lines[0]) == entry
