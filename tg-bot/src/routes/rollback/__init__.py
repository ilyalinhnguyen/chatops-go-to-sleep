from dataclasses import dataclass

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.fsm import UserState

router = Router()


@dataclass(kw_only=True)
class RollbackData:
    version: str

    @staticmethod
    def parse_command(text: str) -> "RollbackData | None":
        tokens = text.split()

        if len(tokens) != 2:
            return None

        if tokens[0] != "/rollback":
            return None

        return RollbackData(version=tokens[1])


@router.message(UserState.default, Command("rollback"))
async def command_rollback(message: Message) -> None:
    assert message.text is not None

    rollback_data = RollbackData.parse_command(message.text)
    if rollback_data is None:
        raise NotImplementedError
        return

    await message.reply(f"received /rollback {rollback_data.version}")
    raise NotImplementedError
