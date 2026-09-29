import enum
import os
import pathlib
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PWD = pathlib.Path(__file__).parent


class SentryConfig(BaseSettings):
    dsn: str | None = None
    profile_session_sample_rate: float | None = None
    profile_lifecycle: Literal["manual", "trace"] = "manual"


class OtelConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    enabled: bool = False
    endpoint: str | None = None
    sample_rate: float = 1.0


class QdrantConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    enabled: bool = True
    host: str = "localhost"
    port: int = 6333
    grpc_port: int = 6334
    api_key: str | None = None
    prefer_grpc: bool = False
    collection_name: str = "rag_documents"
    vector_size: int = 1536
    distance: Literal["Cosine", "Dot", "Euclid"] = "Cosine"


class MlflowConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    enabled: bool = True
    tracking_uri: str = "http://localhost:5500"
    experiment_name: str = "app"


class ModelConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    name: str = "model"
    # MLflow model URI (e.g. models:/name@alias, models:/name/version) or local path
    uri: str | None = None


class SSLMode(enum.StrEnum):
    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"


class DatabaseConfig(BaseSettings):
    username: str = "app"
    password: str = "password"
    host: str = "localhost"
    port: int = 5432
    database: str = "app"
    schema_name: str = Field(alias="schema", default="public")
    ssl_mode: SSLMode = Field(alias="sslmode", default=SSLMode.PREFER)
    pool_pre_ping: bool = True
    pool_size: int = 5
    pool_recycle: int = -1
    scheme: str = "postgresql+psycopg"

    def connection_url(self) -> str:
        return f"{self.scheme}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PWD / ".." / ".env",
        env_ignore_empty=True,
        extra="ignore",
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )

    environment: Literal["local", "test", "development", "staging", "production"] = "local"

    app_name: str = "app"
    debug: bool = False

    # Logging
    log_config: Literal["logging.json", "logging.prod.json"] = "logging.json"

    # Documentation
    docs_enabled: bool = False

    # Audit log
    audit_log_enabled: bool = True

    # Security
    api_token: str | None = None

    # Kafka config
    # Topics follow conventions in https://hackthebox.atlassian.net/wiki/spaces/ACH/pages/436535297/Kafka+Topics+Naming+Conventions
    topic_requests: str = "domain.subdomain.app.requests"
    topic_responses: str = "domain.subdomain.app.responses"

    # Connection settings
    core_mq_kafka_sasl_enabled: bool = False
    core_mq_kafka_sasl_username: str | None = None
    core_mq_kafka_sasl_password: str | None = None
    core_mq_kafka_brokers: str = ""
    core_mq_kafka_ca_cert: str | None = None

    # Producer settings
    client_id: str = "ai.ep.producer"
    request_timeout: int = 5000
    include_request_body: bool = True
    include_response_body: bool = True
    kafka_max_retries: int = 2
    kafka_retry_delay: float = 0.1

    # Sentry
    sentry: SentryConfig = SentryConfig()

    # OpenTelemetry
    otel: OtelConfig = OtelConfig()

    # Qdrant
    qdrant: QdrantConfig = QdrantConfig()

    # Database
    database: DatabaseConfig = DatabaseConfig()

    # MLflow
    mlflow: MlflowConfig = MlflowConfig()

    # Model
    model: ModelConfig = ModelConfig()

    # Slow response threshold (in seconds)
    slow_response_threshold: int = 3

    # storage
    data_path: pathlib.Path = PWD.parent / "data"

    # cold items
    cold_items_file: pathlib.Path = PWD.parent / "data" / "cold" / "prod.json"


class LocalConfig(AppConfig):
    debug: bool = True
    docs_enabled: bool = True


class DevConfig(AppConfig):
    debug: bool = True
    docs_enabled: bool = True
    log_config: Literal["logging.json", "logging.prod.json"] = "logging.prod.json"
    core_mq_kafka_sasl_enabled: bool = True


class ProdConfig(AppConfig):
    debug: bool = False
    log_config: Literal["logging.json", "logging.prod.json"] = "logging.prod.json"
    docs_enabled: bool = False
    core_mq_kafka_sasl_enabled: bool = True


CONFIGS = {
    "local": LocalConfig(),
    "test": LocalConfig(),
    "development": DevConfig(),
    "production": ProdConfig(),
}


def get_environment_config(environment: str | None = None) -> AppConfig:
    _env = environment if environment else os.environ.get("ENVIRONMENT", "local")
    return CONFIGS[_env]
