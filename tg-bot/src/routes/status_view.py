from typing import Any


def format_deployment_status(
    namespace: str, name: str, data: dict[str, Any], language: str = "en"
) -> str:
    replicas = data.get("replicas", 0)
    ready = data.get("ready", 0)
    available = data.get("available", 0)
    updated = data.get("updated", 0)
    unavailable = data.get("unavailable", 0)

    is_russian = language == "ru"

    if ready == replicas and unavailable == 0:
        health = "🟢 Здорово" if is_russian else "🟢 Healthy"
    elif ready > 0:
        health = "🟡 Деградировано" if is_russian else "🟡 Degraded"
    else:
        health = "🔴 Нездорово" if is_russian else "🔴 Unhealthy"

    if is_russian:
        replicas_line = f"Реплики: {ready}/{replicas} готовы"
        available_line = f"Доступно: {available}"
        updated_line = f"Обновлено: {updated}"
        unavailable_line = f"Недоступно: {unavailable}"
    else:
        replicas_line = f"Replicas: {ready}/{replicas} ready"
        available_line = f"Available: {available}"
        updated_line = f"Updated: {updated}"
        unavailable_line = f"Unavailable: {unavailable}"

    return (
        f"📦 {namespace}/{name}\n"
        f"📊 {health}\n"
        f"{replicas_line}\n"
        f"{available_line}\n"
        f"{updated_line}\n"
        f"{unavailable_line}"
    )
