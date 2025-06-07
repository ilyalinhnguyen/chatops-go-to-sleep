from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery

from src.fsm import UserState

router = Router()


@router.callback_query(UserState.default, F.data == "status")
async def query_status(query: CallbackQuery) -> None:
    assert query.message is not None
    await query.message.answer("received a /status")


@router.message(UserState.default, Command("status"))
async def command_status(message: Message) -> None:
    await message.answer("received a /status")
