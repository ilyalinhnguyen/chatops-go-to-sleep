from typing import Any

from src.api import private

PREFIX: str = "v1/prometheus"


def query(promql_query: str) -> dict[str, Any] | None:
    response = private.post(f"{PREFIX}/query", json={"query": promql_query})
    if response.ok:
        return response.json()
    else:
        return None
