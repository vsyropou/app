from typing import Any

from app.model.interfaces import IModel
from app.model.schemas import PredictionItem, PredictRequest


class PlaceholderModel(IModel):
    """Placeholder implementation proving the layering. Replace with a real model (sklearn, xgboost, ...)."""

    def train(self, data: Any, params: dict[str, Any] | None = None) -> None:
        # no-op until a concrete model lands
        ...

    def tune(self, data: Any, search_space: dict[str, Any] | None = None) -> dict[str, Any]:
        return {}

    def predict(self, request: PredictRequest) -> list[PredictionItem]:
        return [PredictionItem(output=inp) for inp in request.inputs[: request.top_n]]

    def evaluate(self, data: Any) -> dict[str, float]:
        return {}

    def score(self, data: Any) -> list[float]:
        return []


def get_method() -> IModel:
    return PlaceholderModel()
