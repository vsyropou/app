from abc import ABC, abstractmethod
from typing import Any

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


class IModel(ABC):
    """Stack-agnostic model interface. Implement for any framework (sklearn, xgboost, tensorflow, ...)."""

    @abstractmethod
    def train(self, data: Any, params: dict[str, Any] | None = None) -> None:
        """Train the model in place on the given data."""

    @abstractmethod
    def tune(self, data: Any, search_space: dict[str, Any] | None = None) -> dict[str, Any]:
        """Search hyperparameters on the given data. Returns the best params found."""

    @abstractmethod
    def predict(self, data: Any) -> Any:
        """Predict for a single request."""

    @abstractmethod
    def evaluate(self, data: Any) -> dict[str, float]:
        """Evaluate the trained model on held-out data. Returns metric name -> value."""

    @abstractmethod
    def score(self, data: Any) -> list[float]:
        """Score each record in the given dataset (e.g. relevance/likelihood, model-specific scale)."""
