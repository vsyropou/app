from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from logging import getLogger

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import Depends, FastAPI, status
from opentelemetry.sdk.trace import TracerProvider
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from app import __version__
from app.api.dependencies import require_bearer
from app.api.middlewares.events import KafkaMiddleware, LazyProducer
from app.api.middlewares.metrics import PrometheusMiddleware, metrics
from app.checks import router as checks_router
from app.config import AppConfig
from app.models import router as models_router
from app.tracing import instrument_fastapi

logger = getLogger(__name__)


def app_factory(config: AppConfig, producer: LazyProducer, tracer_provider: TracerProvider | None = None) -> FastAPI:
    logger.info("Starting FastAPI setup")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # noqa: ARG001
        # kafka audit log producer
        await producer.init_producer()

        yield

        await producer.stop()
        if tracer_provider is not None:
            tracer_provider.shutdown()

    myapp = FastAPI(
        title=config.app_name,
        description="App endpoints",
        version=__version__,
        contact={
            "name": "Hack The Box",
            "url": "https://hackthebox.com",
        },
        debug=config.debug,
        lifespan=lifespan,
    )

    # Composable endpoints
    myapp.include_router(
        models_router.router,
        prefix="/api/v1",
        dependencies=[Depends(require_bearer)],
    )

    # Liveness/readiness probes (root-mounted so k8s probes can hit them directly)
    myapp.include_router(checks_router.build_router(producer))

    # ======================= #
    # Extra Endpoints
    # ======================= #
    # Metrics endpoint
    myapp.add_route("/metrics", metrics)

    # Default endpoints required for system
    if config.docs_enabled:

        @myapp.get("/", status_code=200)
        async def docs_redirect() -> RedirectResponse:
            return RedirectResponse(url="/redoc")

    # Middlewares
    # OTel instrumentation must be installed before any other middleware so the
    # current request span is active while inner middleware (Prometheus exemplars,
    # Kafka audit) runs.
    if tracer_provider is not None:
        instrument_fastapi(myapp)

    if config.audit_log_enabled:
        logger.info("Enabling Kafka Audit logging")
        myapp.add_middleware(
            KafkaMiddleware,
            producer=producer,
            request_topic=config.topic_requests,
            response_topic=config.topic_responses,
            include_request_body=config.include_request_body,
            include_response_body=config.include_response_body,
            include_paths=[r"/api/.*"],
            max_retries=config.kafka_max_retries,
            retry_delay=config.kafka_retry_delay,
        )
    else:
        logger.warning("Kafka Audit logging is disabled")

    myapp.add_middleware(PrometheusMiddleware, app_name=config.app_name)

    # Correlation ID Middleware must always be last
    myapp.add_middleware(CorrelationIdMiddleware, header_name="x-htb-request-id", validator=None)

    # Custom exception handlers
    @myapp.exception_handler(Exception)
    async def generic_exception_handler(request: Request, err: Exception) -> JSONResponse:
        base_error_message = f"Error processing the {request.method} to {request.url}: {err}"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": base_error_message, "api_version": __version__},
        )

    return myapp
