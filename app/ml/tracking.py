from typing import Any, cast

import mlflow
from mlflow.models.model import ModelInfo

from app.config import MlflowConfig


def init_tracking(cfg: MlflowConfig) -> None:
    if cfg.enabled and cfg.tracking_uri:
        mlflow.set_tracking_uri(cfg.tracking_uri)
        mlflow.set_experiment(cfg.experiment_name)


def log_params(params: dict[str, Any]) -> None:
    mlflow.log_params(params)


def log_metrics(metrics: dict[str, float], step: int | None = None) -> None:
    mlflow.log_metrics(metrics, step=step)


def log_model(model: Any, artifact_path: str, registered_model_name: str | None = None) -> ModelInfo | None:
    result = mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path=artifact_path,
        registered_model_name=registered_model_name,
    )
    return cast(ModelInfo | None, result)
