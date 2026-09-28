from app.interfaces import IVectorStore
from app.vectorstore.client import LazyQdrantClient
from app.vectorstore.schemas import Document, SearchResult


class QdrantVectorStore(IVectorStore):
    def __init__(self, client: LazyQdrantClient) -> None:
        self.client = client

    async def ensure_collection(self) -> None:
        await self.client.ensure_collection()

    async def upsert(self, documents: list[Document]) -> None:
        from qdrant_client import models

        points = [
            models.PointStruct(
                id=doc.id,
                vector=doc.embedding,
                payload={"text": doc.text, "metadata": doc.metadata},
            )
            for doc in documents
        ]
        await self.client.get().upsert(
            collection_name=self.client.config.collection_name,
            points=points,
        )

    async def search(self, query_vector: list[float], limit: int = 10) -> list[SearchResult]:
        result = await self.client.get().query_points(
            collection_name=self.client.config.collection_name,
            query=query_vector,
            limit=limit,
        )
        return [
            SearchResult(
                id=str(p.id),
                text=p.payload.get("text", "") if p.payload else "",
                metadata=p.payload.get("metadata", {}) if p.payload else {},
                score=p.score,
            )
            for p in result.points
        ]


def get_vector_store(client: LazyQdrantClient) -> IVectorStore:
    return QdrantVectorStore(client)
