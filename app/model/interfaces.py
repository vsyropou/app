from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.model.schemas import PredictionItem, PredictRequest


class IModel(ABC):
    """Stack-agnostic model interface. Implement for any framework (sklearn, xgboost, tensorflow, ...)."""

    @abstractmethod
    def train(self, data: Any, params: dict[str, Any] | None = None) -> None:
        """Train the model in place on the given data."""

    @abstractmethod
    def tune(self, data: Any, search_space: dict[str, Any] | None = None) -> dict[str, Any]:
        """Search hyperparameters on the given data. Returns the best params found."""

    @abstractmethod
    def predict(self, request: "PredictRequest") -> list["PredictionItem"]:
        """Predict for a single request."""

    @abstractmethod
    def evaluate(self, data: Any) -> dict[str, float]:
        """Evaluate the trained model on held-out data. Returns metric name -> value."""

    @abstractmethod
    def score(self, data: Any) -> list[float]:
        """Score each record in the given dataset (e.g. relevance/likelihood, model-specific scale)."""
