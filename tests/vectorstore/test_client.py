import pytest

from app.config import QdrantConfig
from app.vectorstore.client import LazyQdrantClient


def test_get_raises_when_uninitialized() -> None:
    config = QdrantConfig()
    client = LazyQdrantClient(config)

    with pytest.raises(ValueError, match="hasn't been initialized"):
        client.get()


async def test_init_client_noop_when_disabled() -> None:
    config = QdrantConfig(enabled=False)
    client = LazyQdrantClient(config)

    await client.init_client()

    assert client._client is None


async def test_init_client_creates_client_when_enabled() -> None:
    config = QdrantConfig(enabled=True)
    client = LazyQdrantClient(config)

    await client.init_client()

    assert client._client is not None
    assert client.get() is not None
    await client.stop()


async def test_stop_noop_when_uninitialized() -> None:
    config = QdrantConfig()
    client = LazyQdrantClient(config)

    await client.stop()
