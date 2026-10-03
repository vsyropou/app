from fastapi import APIRouter, Response

from app import __version__
from app.api.middlewares.events import LazyProducer
from app.checks import checks
from app.checks.checks import AggregateResponse, HealthResponse

# ponytail: hardcoded serving-model config; move to AppConfig if this stops being a demo app
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen2.5:0.5b"


def build_router(producer: LazyProducer) -> APIRouter:
    """
    Build the liveness/readiness router, closing over the given producer.

    :param producer: the LazyProducer used by the readiness checks.
    :return: a configured APIRouter exposing /healthz and /readyz.
    """
    router = APIRouter(tags=["checks"])

    @router.get("/healthz", status_code=200, response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        return HealthResponse(api_version=__version__)

    @router.get("/readyz", response_model=AggregateResponse)
    async def readiness_check(response: Response) -> AggregateResponse:
        result = checks.aggregate(
            await checks.kafka_ready(producer),
            await checks.ollama_ready(OLLAMA_BASE_URL, OLLAMA_MODEL),
        )
        response.status_code = 200 if result.ok else 503
        return result

    return router
