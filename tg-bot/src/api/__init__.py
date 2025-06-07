from . import private, v1

_ = v1


def insecure_ping() -> bool:
    response = private.get("ping")
    return response.ok
