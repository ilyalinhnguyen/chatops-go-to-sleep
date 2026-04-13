import os

import requests
from requests import Response


def init_api_url() -> str:
    api = os.getenv("SERVER_URL")
    if api is None:
        raise RuntimeError("SERVER_URL is not set")
    return api


def init_headers() -> dict[str, str]:
    auth_key = os.getenv("AUTH_KEY")
    if auth_key is None:
        raise RuntimeError("AUTH_KEY is not set")

    return {"Authorization": f"Bearer {auth_key}"}


API: str = init_api_url()
HEADERS: dict[str, str] = init_headers()


def get(route: str, **kwargs) -> Response:
    return requests.get(f"{API}/{route}", headers=HEADERS, **kwargs)


def post(route: str, **kwargs) -> Response:
    return requests.post(f"{API}/{route}", headers=HEADERS, **kwargs)
