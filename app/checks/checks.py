import asyncio

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


def aggregate(*results: CheckResult) -> AggregateResponse:
    """
    Aggregate multiple CheckResults into a single readiness payload.
    :param results: the individual dependency check results.
    :return: AggregateResponse with `ok` (all checks passed) and per-check entries.
    """
    return AggregateResponse(ok=all(r.ok for r in results), checks=list(results))
