from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery

from src.fsm import UserState

router = Router()


@router.callback_query(UserState.default, F.data == "update")
async def query_update(query: CallbackQuery) -> None:
    assert query.message is not None
    await query.message.answer("received an /update")


@router.message(UserState.default, Command("update"))
async def command_update(message: Message) -> None:
    await message.answer("received an /update")
