from src.api import private

from . import kubernetes

_ = kubernetes

PREFIX: str = "v1"


def ping() -> bool:
    return private.get(f"{PREFIX}/ping").ok
