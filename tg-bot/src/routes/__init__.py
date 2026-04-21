from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from . import (
    actions_password,
    deployments,
    namespaces,
    nodes,
    pods,
    restart,
    rollback,
    scale,
    start,
    status,
)

router = Router()


@router.callback_query(F.data == start.HOME_CALLBACK_DATA)
async def callback_go_home(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await start.on_go_home(query.message, state)


router.include_routers(
    start.router,
    actions_password.router,
    deployments.router,
    namespaces.router,
    nodes.router,
    pods.router,
    restart.router,
    rollback.router,
    scale.router,
    status.router,
)
