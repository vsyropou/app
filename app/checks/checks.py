import asyncio

import httpx
from pydantic import BaseModel

from app.api.middlewares.events import LazyProducer


class HealthResponse(BaseModel):
    api_version: str


class CheckResult(BaseModel):
    name: str
    ok: bool
    detail: str | None = None


class AggregateResponse(BaseModel):
    ok: bool
    checks: list[CheckResult]


async def kafka_ready(producer: LazyProducer) -> CheckResult:
    """
    Check whether the Kafka producer is initialized and able to reach the cluster.

    Note: this intentionally reads the private `_producer` member of `LazyProducer`
    to avoid leaking Kafka specifics into a public accessor. This is a known,
    documented trade-off.

    :param producer: the LazyProducer wrapping the AIOKafkaProducer.
    :return: CheckResult indicating whether Kafka is reachable.
    """
    if producer._producer is None:
        return CheckResult(name="kafka", ok=False, detail="kafka not initialized")

    try:
        await asyncio.wait_for(producer._producer.client.fetch_all_metadata(), timeout=2.0)
        return CheckResult(name="kafka", ok=True)
    except Exception as e:
        return CheckResult(name="kafka", ok=False, detail=str(e))


async def ollama_ready(base_url: str, model: str, timeout: float = 2.0) -> CheckResult:
    """
    Check whether the Ollama server is reachable and the requested model is available.

    Uses the OpenAI-compatible GET {base_url}/models listing (the same server the
    serving pipeline's LLM client talks to) rather than a completion — generating
    would load the model into memory on every probe.

    :param base_url: OpenAI-compatible base URL, e.g. "http://localhost:11434/v1".
    :param model: model name to look for, e.g. "qwen2.5:0.5b".
    :return: CheckResult indicating whether Ollama serves the model.
    """
    url = f"{base_url.rstrip('/')}/models"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            available = {m.get("id") for m in response.json().get("data", [])}
    except Exception as e:
        return CheckResult(name="ollama", ok=False, detail=str(e))

    if model not in available:
        return CheckResult(name="ollama", ok=False, detail=f"model '{model}' not available")
    return CheckResult(name="ollama", ok=True)


def aggregate(*results: CheckResult) -> AggregateResponse:
    """
    Aggregate multiple CheckResults into a single readiness payload.
    :param results: the individual dependency check results.
    :return: AggregateResponse with `ok` (all checks passed) and per-check entries.
    """
    return AggregateResponse(ok=all(r.ok for r in results), checks=list(results))
