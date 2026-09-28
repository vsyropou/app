from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import __version__
from app.api.middlewares.events import LazyProducer
from app.checks.router import build_router


def _client_for(producer: LazyProducer) -> TestClient:
    ## Build a minimal FastAPI app mounting just the checks router.
    app = FastAPI()
    app.include_router(build_router(producer))
    return TestClient(app)


class TestHealthzEndpoint:
    def test_returns_api_version(self) -> None:
        ## GIVEN: a router built with any LazyProducer
        producer = LazyProducer()
        client = _client_for(producer)

        ## WHEN: GET /healthz
        response = client.get("/healthz")

        ## THEN: 200 and body contains the api_version
        assert response.status_code == 200
        assert response.json() == {"api_version": __version__}


class TestReadyzEndpoint:
    def test_kafka_not_initialized_returns_503(self) -> None:
        ## GIVEN: LazyProducer with no underlying producer
        producer = LazyProducer()
        producer._producer = None
        client = _client_for(producer)

        ## WHEN: GET /readyz
        response = client.get("/readyz")

        ## THEN: 503 and kafka check reports not initialized
        assert response.status_code == 503
        body = response.json()
        assert body["ok"] is False
        assert body["checks"] == [{"name": "kafka", "ok": False, "detail": "kafka not initialized"}]

    def test_kafka_fetch_succeeds_returns_200(self) -> None:
        ## GIVEN: a stubbed producer whose fetch_all_metadata succeeds
        fake_inner = MagicMock()
        fake_inner.client.fetch_all_metadata = AsyncMock(return_value=None)
        producer = LazyProducer()
        producer._producer = fake_inner
        client = _client_for(producer)

        ## WHEN: GET /readyz
        response = client.get("/readyz")

        ## THEN: 200 and kafka ok=True with no detail
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["checks"] == [{"name": "kafka", "ok": True, "detail": None}]

    def test_kafka_fetch_raises_returns_503(self) -> None:
        ## GIVEN: a stubbed producer whose fetch_all_metadata raises
        fake_inner = MagicMock()
        fake_inner.client.fetch_all_metadata = AsyncMock(side_effect=RuntimeError("broker unreachable"))
        producer = LazyProducer()
        producer._producer = fake_inner
        client = _client_for(producer)

        ## WHEN: GET /readyz
        response = client.get("/readyz")

        ## THEN: 503, ok=False, detail contains the exception message
        assert response.status_code == 503
        body = response.json()
        assert body["ok"] is False
        assert body["checks"][0]["name"] == "kafka"
        assert body["checks"][0]["ok"] is False
        assert "broker unreachable" in body["checks"][0]["detail"]
