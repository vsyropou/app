from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.vectorstore.schemas import Document, SearchResult


class IDependency(ABC):
    @abstractmethod
    async def method(self) -> bool:
        pass


class IVectorStore(ABC):
    @abstractmethod
    async def ensure_collection(self) -> None: ...

    @abstractmethod
    async def upsert(self, documents: list["Document"]) -> None: ...

    @abstractmethod
    async def search(self, query_vector: list[float], limit: int = 10) -> list["SearchResult"]: ...
