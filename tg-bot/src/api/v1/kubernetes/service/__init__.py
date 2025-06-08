from typing import Literal, TypedDict

from src.api import private

PREFIX: str = "v1/kubernetes/service"


class ScaleResponseData(TypedDict):
    name: str
    namespace: str
    replicas: int


class ScaleResponse(TypedDict):
    status: Literal["success", "error"]
    message: str
    data: ScaleResponseData


def scale(namespace: str, name: str, replicas: int) -> ScaleResponse | None:
    response = private.post(
        f"{PREFIX}/scale",
        json={"namespace": namespace, "name": name, "replicas": replicas},
    )
    if response.ok:
        return response.json()
    else:
        return None


class RestartResponseData(TypedDict):
    name: str
    namespace: str


class RestartResponse(TypedDict):
    status: Literal["success", "error"]
    message: str
    data: RestartResponseData


def restart(namespace: str, name: str) -> RestartResponse | None:
    response = private.post(
        f"{PREFIX}/restart",
        json={"namespace": namespace, "name": name},
    )
    if response.ok:
        return response.json()
    else:
        return None


class RollbackResponseData(TypedDict):
    name: str
    namespace: str
    revisionId: str
    revisionImage: str
    version: str


class RollbackResponse(TypedDict):
    status: Literal["success", "error"]
    message: str
    data: RollbackResponseData


def rollback(namespace: str, name: str) -> RollbackResponse | str:
    response = private.post(
        f"{PREFIX}/rollback",
        json={"namespace": namespace, "name": name},
    )
    if response.ok:
        return response.json()
    else:
        return response.reason


def rollback_rev_id(
    namespace: str,
    name: str,
    revision_id: str,
) -> RollbackResponse | None:
    response = private.post(
        f"{PREFIX}/rollback",
        json={"namespace": namespace, "name": name, "revisionId": revision_id},
    )
    if response.ok:
        return response.json()
    else:
        return None


def rollback_rev_image(
    namespace: str,
    name: str,
    revision_image: str,
) -> RollbackResponse | None:
    response = private.post(
        f"{PREFIX}/rollback",
        json={"namespace": namespace, "name": name, "revisionImage": revision_image},
    )
    if response.ok:
        return response.json()
    else:
        return None


def rollback_version(
    namespace: str,
    name: str,
    version: str,
) -> RollbackResponse | None:
    response = private.post(
        f"{PREFIX}/rollback",
        json={"namespace": namespace, "name": name, "version": version},
    )
    if response.ok:
        return response.json()
    else:
        return None


class UpdateResponseData(TypedDict):
    name: str
    namespace: str
    image: str
    version: str


class UpdateResponse(TypedDict):
    status: Literal["success", "error"]
    message: str
    data: UpdateResponseData


def update_image(namespace: str, name: str, image: str) -> UpdateResponse | None:
    response = private.post(
        f"{PREFIX}/update",
        json={"namespace": namespace, "name": name, "image": image},
    )
    if response.ok:
        return response.json()
    else:
        return None


def update_version(namespace: str, name: str, version: str) -> UpdateResponse | None:
    response = private.post(
        f"{PREFIX}/update",
        json={"namespace": namespace, "name": name, "version": version},
    )
    if response.ok:
        return response.json()
    else:
        return None


class StatusResponseData(TypedDict):
    name: str
    namespace: str
    replicas: int
    available: int
    ready: int
    updated: int
    unavailable: int


class StatusResponse(TypedDict):
    status: Literal["success", "error"]
    message: str
    data: StatusResponseData


def status(namespace: str, name: str) -> StatusResponse | None:
    response = private.post(
        f"{PREFIX}/status",
        json={"namespace": namespace, "name": name},
    )
    if response.ok:
        return response.json()
    else:
        return None
