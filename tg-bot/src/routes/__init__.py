from aiogram import Router

from . import rollback, scale, start, status, restart, update

router = Router()
router.include_routers(rollback.router, scale.router, start.router, status.router, restart.router, update.router)
