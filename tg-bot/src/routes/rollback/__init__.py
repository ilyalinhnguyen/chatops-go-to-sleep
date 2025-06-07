from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.fsm import UserState

router = Router()


@router.message(UserState.default, Command("rollback"))
async def command_rollback(message: Message) -> None:
    assert message.text is not None

    tokens = message.text.split()

    assert len(tokens) == 2
    assert tokens[0] == "/rollback"

    version = tokens[1]

    await message.reply(f"received /rollback {version}")
