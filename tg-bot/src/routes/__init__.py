from aiogram import Router

from . import metrics, restart, rollback, scale, start, status

router = Router()
router.include_routers(
    start.router,
    metrics.router,
    restart.router,
    rollback.router,
    scale.router,
    status.router,
    update.router,
)
