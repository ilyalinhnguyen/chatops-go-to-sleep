from src.api import private

from . import kubernetes, prometheus

_ = kubernetes
_ = prometheus

PREFIX: str = "v1"


def ping() -> bool:
    return private.get(f"{PREFIX}/ping").ok
