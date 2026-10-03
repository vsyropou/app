import asyncio
import datetime
import json
import re
import time
from logging import getLogger
from typing import Any

from aiokafka import AIOKafkaProducer
from asgi_correlation_id import correlation_id
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from tenacity import AsyncRetrying, RetryError, stop_after_attempt, wait_random_exponential
from uuid_extensions import uuid7str

logger = getLogger(__name__)


def serialize(value: dict[str, Any]) -> bytes:
    """
    Serialize a dictionary as JSON.
    :param value: The value to serialize
    :return: the serialized version of the dictionary
    """
    return json.dumps(value).encode()


def _decode_value(value: bytes) -> dict[str, Any] | str:
    """
    Attempts to convert value to JSON object. If it's not a valid JSON object, return the value as string.
    :param value: the value to decode.
    :return: A dictionary with parsed JSON if value contains a valid JSON string, else the value as string.
    """
    try:
        parsed_json: dict[str, Any] = json.loads(value)
        return parsed_json
    except:  # noqa: E722
        # Fall back to string if not JSON
        return value.decode()


class LazyProducer:
    """
    A lazy-initialized wrapper for AIOKafkaProducer.

    This class delays the initialization of the Kafka producer until explicitly
    requested, which is useful for applications that need to establish connections
    only when necessary, reducing resource usage during startup and allowing delegation of
    initialization during lifespan.
    """

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self._producer: AIOKafkaProducer = None
        self.args = args
        self.kwargs = kwargs

    def get(self) -> AIOKafkaProducer:
        if not self._producer:
            raise ValueError("Producer hasn't been initialized")

        return self._producer

    async def init_producer(self) -> None:
        if self.kwargs.get("bootstrap_servers"):
            self._producer = AIOKafkaProducer(*self.args, **self.kwargs)
            await self._producer.start()
        else:
            logger.info("No bootstrap servers configured, skipping Kafka producer initialization")

    async def stop(self) -> None:
        if not self._producer:
            return

        await self._producer.stop()


class KafkaMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses to Kafka topics.

    This middleware captures details of incoming HTTP requests and their corresponding
    responses, then sends this data to specified Kafka topics for various logging purposes.
    It supports filtering by path patterns, exclusion of sensitive headers, and
    configurable inclusion of request/response bodies.

    The middleware uses a retry mechanism with exponential backoff to handle temporary
    Kafka connectivity issues, ensuring reliable delivery of various logs.
    """

    def __init__(
        self,
        app: ASGIApp,
        producer: LazyProducer | None = None,
        request_topic: str = "api-requests",
        response_topic: str = "api-responses",
        include_request_body: bool = True,
        include_response_body: bool = True,
        include_paths: list[str] | None = None,
        exclude_headers: list[str] | None = None,
        retry_delay: float = 0.1,
        max_retry_time: float = 1.0,
        max_retries: int = 3,
    ):
        """
         Initialize the Kafka logging middleware.

        :param app: The FastAPI application instance
        :param producer: Configured Kafka producer for sending messages
        :param request_topic: Kafka topic name for request topic
        :param response_topic: Kafka topic name for response topic
        :param include_request_body: Whether to include request body in logs
        :param include_response_body: Whether to include response body in logs
        :param include_paths: List of regex patterns for paths to include in logging. If empty, no paths will be logged.
        :param exclude_headers: List of header names to exclude from logs for privacy
        :param retry_delay: Base delay in seconds between retry attempts. Actual delay uses exponential backoff
                            with jitter.
        :param max_retry_time: Maximum time between retries.
        :param max_retries: Maximum number of retries.
        """
        if exclude_headers is None:
            exclude_headers = ["authorization", "cookie"]
        super().__init__(app)
        self._app = app
        self.producer = producer
        self.request_topic = request_topic
        self.response_topic = response_topic
        self.include_request_body = include_request_body
        self.include_response_body = include_response_body
        self.include_paths = include_paths or []
        self.compiled_include_path_regexes = [re.compile(path) for path in self.include_paths]
        self.exclude_headers = frozenset(exclude_headers or [])
        self.max_retry_time = max_retry_time
        self.base_retry_delay = retry_delay
        self.max_retries = max_retries

    async def send_with_retry(self, topic: str, value: dict[str, Any]) -> None:
        if not self.producer or not self.producer.get():
            logger.warning("No Kafka producer has been initialized")
            return

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_random_exponential(multiplier=self.base_retry_delay, max=self.max_retry_time),
            ):
                with attempt:
                    await self.producer.get().send_and_wait(topic, serialize(value))
        except RetryError as e:
            logger.error(f'Failed to send message to Kafka topic "{topic}": {e}')

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip middleware if no included paths
        if not any(path.fullmatch(request.url.path) for path in self.compiled_include_path_regexes):
            return await call_next(request)

        # Use request ID to correlate request and response. Generate a random one if not found.
        request_id = correlation_id.get() or str(uuid7str())
        logger.info(f"Logging request {request_id}")

        # Capture request details
        start_time = time.perf_counter()

        # Prepare request data for Kafka
        request_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": {k: v for k, v in request.headers.items() if k.lower() not in self.exclude_headers},
            "client_host": request.client.host if request.client else None,
            "timestamp": datetime.datetime.now(datetime.UTC).timestamp(),
        }

        body_bytes = await request.body()

        # Handle request body if needed
        if self.include_request_body:
            request_data["body"] = _decode_value(body_bytes)

        # Send request data to Kafka asynchronously - don't await to avoid delaying the request
        await asyncio.create_task(self.send_with_retry(self.request_topic, request_data))

        # Process the request through the application
        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = request_id

        # Calculate processing time
        process_time = time.perf_counter() - start_time

        # Prepare response data for Kafka
        response_data = {
            "request_id": request_id,
            "status_code": response.status_code,
            "headers": {k: v for k, v in response.headers.items() if k.lower() not in self.exclude_headers},
            "process_time": process_time,
            "timestamp": datetime.datetime.now(datetime.UTC).timestamp(),
        }

        res_body = [section async for section in response.body_iterator]  # type: ignore[attr-defined]
        response.body_iterator = iterate_in_threadpool(iter(res_body))  # type: ignore[attr-defined]

        # Handle response body if needed
        if self.include_response_body:
            content = b"".join(section for section in res_body)
            response_data["body"] = _decode_value(content)

        # Send response data to Kafka asynchronously - don't await to avoid delaying the response
        await asyncio.create_task(self.send_with_retry(self.response_topic, response_data))

        return response
