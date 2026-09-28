from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_config
from app.api.factories import app_factory
from app.api.middlewares.events import LazyProducer
from app.config import AppConfig, get_environment_config


@pytest.fixture
def test_config() -> AppConfig:
    config = get_environment_config("test")
    config.api_token = None
    config.audit_log_enabled = False
    return config


@pytest.fixture
def mock_producer() -> LazyProducer:
    """LazyProducer with no Kafka underneath; init_producer is a no-op."""
    return LazyProducer()


@pytest_asyncio.fixture
async def test_app(test_config: AppConfig, mock_producer: LazyProducer) -> AsyncGenerator[FastAPI, None]:
    app = app_factory(test_config, mock_producer)
    app.dependency_overrides[get_config] = lambda: test_config
    try:
        async with app.router.lifespan_context(app):
            yield app
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        yield client
