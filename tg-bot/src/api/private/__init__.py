import os

import requests
from requests import Response


def init_api_url() -> str:
    api = os.getenv("SERVER")
    assert api is not None
    return api


def init_headers() -> dict[str, str]:
    auth_key = os.getenv("AUTH_KEY")
    assert auth_key is not None

    return {"Authentication": auth_key}


API: str = init_api_url()
HEADERS: dict[str, str] = init_headers()


def get(route: str) -> Response:
    return requests.get(f"{API}/{route}", headers=HEADERS)


def post(route: str) -> Response:
    return requests.post(f"{API}/{route}", headers=HEADERS)
