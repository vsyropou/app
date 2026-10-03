from collections.abc import Callable
from functools import partial
from pathlib import Path

from app.models.functions import predict
from app.pipeline.config import create_pipeline_from_config
from app.schemas import ModelRequest, ModelResponse

PWD = Path(__file__).parent


def get_predict_zero() -> Callable[[ModelRequest], list[ModelResponse]]:
    """Compose the full predict function dependency"""

    path = PWD / "zero-shot-pipeline.yaml"

    _, pipeline, _, _, _ = create_pipeline_from_config(path)

    return partial(predict, pipeline=pipeline)


def get_predict_tuned() -> Callable[[ModelRequest], list[ModelResponse]]:
    """Compose the full predict function dependency"""

    path = PWD / "tuned-pipeline.yaml"

    _, pipeline, _, _, _ = create_pipeline_from_config(path)

    return partial(predict, pipeline=pipeline)
