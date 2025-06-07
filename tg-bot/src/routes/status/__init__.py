from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.fsm import UserState

router = Router()


@router.message(UserState.default, Command("status"))
async def command_status(message: Message) -> None:
    await message.answer("received /status")
