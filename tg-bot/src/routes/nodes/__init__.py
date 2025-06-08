import json

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from src import api
from src.fsm import UserState

router = Router()


@router.message(UserState.default, Command("nodes"))
async def command_nodes(message: Message) -> None:
    assert message.text is not None

    response = api.v1.kubernetes.metrics.nodes()
    if response is None:
        await message.answer("Internal error.")
        return

    await message.answer(
        f"```json\n{json.dumps(response, indent=2)[:4000]}```",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
