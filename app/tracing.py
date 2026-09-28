import logging
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiokafka import AIOKafkaInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_OFF, ALWAYS_ON, ParentBased, Sampler, TraceIdRatioBased

from app.config import AppConfig

logger = logging.getLogger(__name__)


def _sampler(config: AppConfig) -> Sampler:
    if not config.otel.enabled:
        return ALWAYS_OFF
    if config.otel.sample_rate >= 1.0:
        return ParentBased(root=ALWAYS_ON)
    return ParentBased(root=TraceIdRatioBased(config.otel.sample_rate))


def initialize_tracing(config: AppConfig, version: str) -> TracerProvider | None:
    """Build and register the global TracerProvider. Returns None when disabled."""
    if not config.otel.enabled or not config.otel.endpoint:
        logger.info("OTel tracing disabled")
        return None

    resource = Resource.create(
        attributes={
            "service.name": config.app_name,
            "service.version": version,
            "deployment.environment": config.environment,
        }
    )
    provider = TracerProvider(resource=resource, sampler=_sampler(config))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=config.otel.endpoint)))
    trace.set_tracer_provider(provider)

    # Auto-instrument aiokafka producer and logging so spans/log records carry trace context.
    AIOKafkaInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=False, tracer_provider=provider)

    logger.info("OTel tracing initialized (endpoint=%s)", config.otel.endpoint)
    return provider


def instrument_fastapi(app: Any) -> None:
    """Install the FastAPI ASGI instrumentation (must be called before other add_middleware calls)."""
    FastAPIInstrumentor().instrument_app(app)
