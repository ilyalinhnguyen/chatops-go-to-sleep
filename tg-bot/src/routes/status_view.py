from typing import Any


def format_deployment_status(namespace: str, name: str, data: dict[str, Any]) -> str:
    replicas = data.get("replicas", 0)
    ready = data.get("ready", 0)
    available = data.get("available", 0)
    updated = data.get("updated", 0)
    unavailable = data.get("unavailable", 0)

    if ready == replicas and unavailable == 0:
        health = "🟢 Healthy"
    elif ready > 0:
        health = "🟡 Degraded"
    else:
        health = "🔴 Unhealthy"

    return (
        f"📦 {namespace}/{name}\n"
        f"📊 {health}\n"
        f"Replicas: {ready}/{replicas} ready\n"
        f"Available: {available}\n"
        f"Updated: {updated}\n"
        f"Unavailable: {unavailable}"
    )
