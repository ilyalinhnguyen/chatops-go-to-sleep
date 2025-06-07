from typing import Any, TypedDict

from src.api import private

PREFIX: str = "v1/prometheus/metrics"


class BasicMetrics(TypedDict):
    upStatus: bool
    cpuUsage: float
    memoryUsage: int
    timestamp: str


def basic() -> BasicMetrics | None:
    response = private.get(f"{PREFIX}/basic")
    if response.ok:
        return response.json()
    else:
        return None


class MetricList(TypedDict):
    metrics: list[str]


def list() -> MetricList | None:
    response = private.get(f"{PREFIX}/list")
    if response.ok:
        return response.json()
    else:
        return None


def by_name(name: str) -> dict[str, Any] | None:
    response = private.get(f"{PREFIX}/{name}")
    if response.ok:
        return response.json()
    else:
        return None
