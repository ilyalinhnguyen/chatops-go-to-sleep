from aiogram import Router

from . import rollback, start, status

router = Router()
router.include_routers(rollback.router, start.router, status.router)
