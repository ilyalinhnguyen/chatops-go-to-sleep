from typing import TypedDict

from pydantic.types import Strict

from src.api import private

PREFIX: str = "v1/kubernetes/metrics"


class Cluster(TypedDict):
    cpuUsage: float
    memoryUsage: float
    nodeCount: int
    podCount: int
    timestamp: str


def cluster() -> Cluster | None:
    response = private.get(f"{PREFIX}/cluster")
    if response.ok:
        return response.json()
    else:
        return None


class Node(TypedDict):
    name: str
    cpuUsage: float
    memoryUsage: float
    diskUsage: float
    podCount: int


def nodes() -> list[Node] | None:
    response = private.get(f"{PREFIX}/nodes")
    if response.ok:
        return response.json()
    else:
        return None


class Pod(TypedDict):
    name: str
    namespace: str
    cpuUsage: float
    memoryUsage: int
    restartCount: int
    containerCount: int


def pods(namespace: str | None) -> list[Pod] | None:
    if namespace is not None:
        response = private.get(f"{PREFIX}/pods?namespace={namespace}")
    else:
        response = private.get(f"{PREFIX}/pods")

    if response.ok:
        return response.json()
    else:
        return None


class Deployment(TypedDict):
    name: str
    namespace: str
    replicas: int
    available: int
    ready: int


def deployments() -> list[Deployment] | None:
    response = private.get(f"{PREFIX}/deployments")
    if response.ok:
        return response.json()
    else:
        return None


class DeploymentConditions(TypedDict):
    lastTransitionTime: str
    lastUpdatedTime: str
    message: str
    reason: str
    status: str
    type: str


class SpecificDeployment(TypedDict):
    available: int
    conditions: list[DeploymentConditions]
    creationTimestamp: str
    name: str
    namespace: str
    observedGeneration: int
    ready: int
    replicas: int
    unavailable: int
    updated: int


def deployments_by_name(name: str) -> SpecificDeployment | None:
    response = private.get(f"{PREFIX}/deployments/{name}")
    if response.ok:
        return response.json()
    else:
        return None


class Namespace(TypedDict):
    name: str
    cpuUsage: float
    memoryUsage: int
    podCount: int


def namespaces() -> list[Namespace] | None:
    response = private.get(f"{PREFIX}/namespaces")
    if response.ok:
        return response.json()
    else:
        return None
