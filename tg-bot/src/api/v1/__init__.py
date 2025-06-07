from .. import private


def metrics() -> None:
    _response = private.get("metrics")
    raise NotImplementedError


def scale() -> None:
    _response = private.post("scale")
    raise NotImplementedError


def restart() -> None:
    _response = private.post("restart")
    raise NotImplementedError


def rollback() -> None:
    _response = private.post("rollback")
    raise NotImplementedError


def ping() -> bool:
    response = private.get("ping")
    return response.ok
