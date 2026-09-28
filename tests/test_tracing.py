from collections.abc import Generator
from unittest.mock import patch

import opentelemetry.trace as otel_trace
import opentelemetry.util._once
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ALWAYS_ON, ParentBased, TraceIdRatioBased

from app.tracing import _sampler, initialize_tracing

from .conftest import make_otel_config


@pytest.fixture(autouse=True)
def reset_tracer_provider() -> Generator[None]:
    ## OTel's set_tracer_provider is once-only; reset the internals so each test starts clean.
    yield
    otel_trace._TRACER_PROVIDER = None
    otel_trace._TRACER_PROVIDER_SET_ONCE = opentelemetry.util._once.Once()


class TestSampler:
    def test_full_sample_rate_returns_parent_based_always_on(self) -> None:
        ## GIVEN: otel is enabled with sample_rate >= 1.0
        cfg = make_otel_config(sample_rate=1.0)

        ## WHEN: _sampler is called
        sampler = _sampler(cfg)

        ## THEN: ParentBased(ALWAYS_ON) is chosen so parent-based decisions honor the parent's sampling bit
        assert isinstance(sampler, ParentBased)
        assert sampler._root is ALWAYS_ON

    def test_partial_sample_rate_uses_ratio(self) -> None:
        ## GIVEN: otel is enabled with a partial sample_rate (e.g. 0.25)
        cfg = make_otel_config(sample_rate=0.25)

        ## WHEN: _sampler is called
        sampler = _sampler(cfg)

        ## THEN: ParentBased(TraceIdRatioBased) is chosen with the configured rate
        assert isinstance(sampler, ParentBased)
        assert isinstance(sampler._root, TraceIdRatioBased)
        assert sampler._root.rate == 0.25


class TestInitializeTracing:
    def test_returns_none_when_disabled(self) -> None:
        ## GIVEN: otel is disabled
        cfg = make_otel_config(enabled=False)

        ## WHEN: initialize_tracing is called
        provider = initialize_tracing(cfg, version="1.0.0")

        ## THEN: no provider is created
        assert provider is None

    def test_creates_provider_with_resource_and_exporter(self) -> None:
        ## GIVEN: otel enabled and endpoint configured
        cfg = make_otel_config(endpoint="http://localhost:4318", sample_rate=1.0)
        cfg.app_name = "my-service"
        cfg.environment = "test"

        ## WHEN: initialize_tracing is called (with OTLP exporter mocked so no network)
        with (
            patch("app.tracing.OTLPSpanExporter") as exporter_cls,
            patch("app.tracing.AIOKafkaInstrumentor") as aiokafka_inst,
            patch("app.tracing.LoggingInstrumentor") as logging_inst,
        ):
            provider = initialize_tracing(cfg, version="1.2.3")

        ## THEN: a real TracerProvider is returned and registered globally
        assert isinstance(provider, TracerProvider)
        assert trace.get_tracer_provider() is provider

        ## THEN: resource attributes pick up app name, version, environment
        resource = provider.resource
        assert resource.attributes["service.name"] == "my-service"
        assert resource.attributes["service.version"] == "1.2.3"
        assert resource.attributes["deployment.environment"] == "test"

        ## THEN: an OTLP exporter was registered through a BatchSpanProcessor
        exporter_cls.assert_called_once_with(endpoint="http://localhost:4318")

        ## THEN: aiokafka + logging auto-instrumentation was enabled against the provider
        aiokafka_inst.return_value.instrument.assert_called_once()
        logging_inst.return_value.instrument.assert_called_once_with(set_logging_format=False, tracer_provider=provider)
