import pathlib
from collections.abc import Callable

from app.pipeline.config import create_pipeline_from_config
from app.schemas import Document, ModelRequest, ModelResponse

PIPELINE_PATH = pathlib.Path(__file__).parent / "serving-model.yaml"


def predict(requests: list[Document]) -> list[ModelResponse]:
    _, pipeline, _, _ = create_pipeline_from_config(PIPELINE_PATH)
    # NOTE: This should be a parallel operation given a fat gpu array cluster in production.

    results = []
    for req in requests:
        rsp: Document = pipeline.process(req)
        meta = rsp.metadata

        if req.labels is not None:
            raise NotImplementedError("Scoring is not implemented yet")

        results += [ModelResponse(verdict=meta.is_true, confidence=meta.confidence, hint=meta.hint)]

    results = [pipeline.process(req.documents) for req in requests]

    return list[results]


def get_predict() -> Callable[[ModelRequest], ModelResponse]:
    """Return the predict callable. Bound via FastAPI Depends in the router."""
    return predict
