from . import private, v1

_ = v1


def ping() -> bool:
    return private.requests.get(f"{private.API}/ping").ok


def metrics() -> ...:
    _response = private.requests.get(f"{private.API}/metrics")
    raise NotImplementedError
