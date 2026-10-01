from typing import Any, cast

import mlflow
from mlflow.models.model import ModelInfo


def log_pandas_df(obj: Any, **kwargs) -> Any:
    """Load the artifact from the given path."""

    mlflow_data = mlflow.data.from_pandas(obj)
    mlflow.log_input(mlflow_data, context=kwargs.get("context", None), tags=kwargs.get("tags", None))


def log_params(params: dict[str, Any]) -> None:
    mlflow.log_params(params)


def log_metrics(metrics: dict[str, float], step: int | None = None) -> None:
    mlflow.log_metrics(metrics, step=step)


def log_model(model: Any, artifact_path: str, registered_model_name: str | None = None) -> ModelInfo | None:
    result = mlflow.pyfunc.log_model(
        python_model=model,
        artifact_path=artifact_path,
        registered_model_name=registered_model_name,
    )
    return cast(ModelInfo | None, result)
