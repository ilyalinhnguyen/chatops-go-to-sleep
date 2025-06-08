from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from src import api
from src.fsm import UserState
import json
from aiogram.enums import ParseMode
from src.routes import start
router = Router()


@router.message(UserState.default, Command("metrics"))
async def command_restart(message: Message, state:FSMContext) -> None:
    assert message.text is not None

    response = api.v1.prometheus.metrics.basic()
    if response is None:
        await message.answer("Internal error.")
        return

    await message.answer(
        f"```json\n{json.dumps(response, indent=2)[:4000]}```",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    await start.command_start(message, state)
