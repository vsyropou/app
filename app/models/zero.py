import pathlib
from collections.abc import Callable

from app.pipeline.config import create_pipeline_from_config
from app.schemas import Document, EvaluationMetrics, ModelResponse

PIPELINE_PATH = pathlib.Path(__file__).parent / "serving-model.yaml"

PredictFn = Callable[[list[Document], list[int] | None], tuple[ModelResponse, EvaluationMetrics | None]]


def predict(points: list[Document], labels: list[int] | None = None) -> tuple[ModelResponse, EvaluationMetrics | None]:
    pipeline = create_pipeline_from_config(PIPELINE_PATH)
    rsp = pipeline.process(points)
    metrics: EvaluationMetrics | None = None
    if labels is not None:
        raise NotImplementedError("Scoring is not implemented yet")
    return rsp, metrics


def get_predict() -> PredictFn:
    """Return the predict callable. Bound via FastAPI Depends in the router."""
    return predict
