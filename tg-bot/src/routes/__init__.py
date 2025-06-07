from aiogram import Router

from . import rollback, scale, start, status

router = Router()
router.include_routers(rollback.router, scale.router, start.router, status.router)
