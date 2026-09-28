from qdrant_client import AsyncQdrantClient, models

from app.config import QdrantConfig

DISTANCE_MAP = {
    "Cosine": models.Distance.COSINE,
    "Dot": models.Distance.DOT,
    "Euclid": models.Distance.EUCLID,
}


class LazyQdrantClient:
    """
    A lazy-initialized wrapper for AsyncQdrantClient.

    Delays initialization until explicitly requested, mirroring the
    LazyProducer pattern in app/api/middlewares/events.py.
    """

    def __init__(self, config: QdrantConfig) -> None:
        self.config = config
        self._client: AsyncQdrantClient | None = None

    def get(self) -> AsyncQdrantClient:
        if not self._client:
            raise ValueError("Qdrant client hasn't been initialized")
        return self._client

    async def init_client(self) -> None:
        if self.config.enabled:
            self._client = AsyncQdrantClient(
                host=self.config.host,
                port=self.config.port,
                grpc_port=self.config.grpc_port,
                api_key=self.config.api_key,
                prefer_grpc=self.config.prefer_grpc,
            )

    async def ensure_collection(self) -> None:
        await self.get().create_collection(
            collection_name=self.config.collection_name,
            vectors_config=models.VectorParams(
                size=self.config.vector_size,
                distance=DISTANCE_MAP[self.config.distance],
            ),
        )

    async def stop(self) -> None:
        if not self._client:
            return
        await self._client.close()
