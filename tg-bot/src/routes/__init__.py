from aiogram import Router

from . import (
    deployments,
    metrics,
    namespaces,
    nodes,
    pods,
    restart,
    rollback,
    scale,
    start,
    status,
    update,
)

router = Router()
router.include_routers(
    start.router,
    deployments.router,
    metrics.router,
    namespaces.router,
    nodes.router,
    pods.router,
    restart.router,
    rollback.router,
    scale.router,
    status.router,
)
