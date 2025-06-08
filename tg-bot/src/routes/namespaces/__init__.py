import json

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from src import api
from src.fsm import UserState

router = Router()


@router.message(UserState.default, Command("namespaces"))
async def command_namespaces(message: Message, state: FSMContext) -> None:
    response = api.v1.kubernetes.metrics.namespaces()
    if response is None:
        await message.answer("Internal error")
        return

    await message.answer(
        f"```json\n{json.dumps(response, indent=2)}```",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
