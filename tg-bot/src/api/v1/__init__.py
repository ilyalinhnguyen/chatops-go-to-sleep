from src.api import private

from . import kubernetes, prometheus

_ = kubernetes
_ = prometheus

PREFIX: str = "v1"


def ping() -> bool:
    return private.get(f"{PREFIX}/ping").ok


def scale() -> bool:
    return private.post(f"{PREFIX}/scale").ok


def restart() -> bool:
    return private.post(f"{PREFIX}/restart").ok


def rollback() -> bool:
    return private.post(f"{PREFIX}/rollback").ok
