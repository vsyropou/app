import asyncio

import sentry_sdk
from aiokafka.helpers import create_ssl_context
from hypercorn.asyncio import serve
from hypercorn.config import Config as HypercornConfig
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from starlette.middleware.cors import CORSMiddleware

from app import __version__
from app.api.dependencies import get_config
from app.api.factories import app_factory
from app.api.middlewares.events import LazyProducer
from app.log import initialize_logging
from app.tracing import initialize_tracing

config = get_config()

# Setup Sentry if DSN has been configured.
if config.sentry.dsn:
    sentry_sdk.init(
        dsn=config.sentry.dsn,
        traces_sample_rate=1.0,
        release=f"ep-recommender@{__version__}",
        environment=config.environment,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        profile_session_sample_rate=config.sentry.profile_session_sample_rate,
        profile_lifecycle=config.sentry.profile_lifecycle,
    )

# Initialize lazy object holders

# Create SASL config if settings are set
sasl_config = (
    {
        "security_protocol": "SASL_SSL",
        "sasl_mechanism": "SCRAM-SHA-256",
        "sasl_plain_username": config.core_mq_kafka_sasl_username,
        "sasl_plain_password": config.core_mq_kafka_sasl_password,
        "ssl_context": create_ssl_context(cadata=config.core_mq_kafka_ca_cert),
    }
    if config.core_mq_kafka_sasl_enabled
    else {}
)

producer = LazyProducer(bootstrap_servers=config.core_mq_kafka_brokers, api_version="2.8", **sasl_config)

tracer_provider = initialize_tracing(config, __version__)

app = app_factory(config, producer, tracer_provider)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

log_config = initialize_logging(config.log_config)


if __name__ == "__main__":
    # Run using main - useful for attaching debuggers
    cnf = HypercornConfig()
    cnf.bind = ["0.0.0.0:3000"]
    cnf.accesslog = "-"
    cnf.logconfig_dict = log_config
    asyncio.run(serve(app, cnf))  # type: ignore[arg-type]
