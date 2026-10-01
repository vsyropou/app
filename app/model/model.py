from typing import Any

from app.interfaces import IModel
from app.tracking.tracking import log_metrics, log_model, log_params


class PlaceholderModel(IModel):
    """Placeholder implementation proving the layering. Replace with a real model (sklearn, xgboost, ...)."""

    def train(self, data: Any, params: dict[str, Any] | None = None) -> None:
        # no-op until a concrete model lands
        log_model(self, artifact_path="model", registered_model_name="placeholder-model")

    def tune(self, data: Any, params: dict[str, Any] | None = None) -> dict[str, Any]:
        tuned_params = {"param1": 0.5, "param2": 10}
        log_params(tuned_params)
        return tuned_params

    def predict(self, data: Any, params: dict[Any, Any]) -> list[Any]:
        return []

    def evaluate(self, data: Any, params: dict[Any, Any]) -> dict[str, float]:
        metrics = {"accuracy": 0.9, "f1_score": 0.8}
        log_metrics(metrics)
        return metrics

    def score(self, data: Any, params: dict[Any, Any]) -> list[float]:
        return []
