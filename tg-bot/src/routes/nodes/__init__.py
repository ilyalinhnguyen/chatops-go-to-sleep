import json

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from src import api
from src.formatting import json_pre_html
from src.fsm import UserState
from src.i18n import tr
from src.routes import start

router = Router()


@router.message(UserState.default, Command("nodes"))
async def command_nodes(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    response = api.v1.kubernetes.metrics.nodes()
    if response is None:
        await start.return_to_main_menu(
            message,
            state,
            notice=await tr(state, "nodes_loading_failed"),
            history_command="/nodes",
        )
        return

    plain = json.dumps(response, indent=2)[:3500]
    await start.return_to_main_menu(
        message,
        state,
        notice=json_pre_html(plain),
        history_line=await start.build_history_entry(state, "/nodes", plain),
        notice_parse_mode=ParseMode.HTML,
    )
