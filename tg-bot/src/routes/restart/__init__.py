from dataclasses import dataclass

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery
from src import api
from src.fsm import UserState

router = Router()


@dataclass(kw_only=True)
class RestartData:
    namespace: str
    name: str

    @staticmethod
    def parse_command(text: str) -> "RestartData | None":
        tokens = text.split()

        if len(tokens) != 2:
            return None

        if tokens[0] != "/restart":
            return None

        args = tokens[1].split(":")

        if len(args) != 2:
            return None

        return RestartData(namespace=args[0], name=args[1])


@router.callback_query(UserState.default, F.data == "restart")
async def query_restart(query: CallbackQuery) -> None:
    assert query.message is not None
    await query.message.answer("received a /restart")


@router.message(UserState.default, Command("restart"))
async def command_restart(message: Message) -> None:
    assert message.text is not None

    restart_data = RestartData.parse_command(message.text)
    if restart_data is None:
        await message.answer(
            "`/restart <NAMESPACE>:<NAME>`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    response = api.v1.kubernetes.service.restart(restart_data.namespace, restart_data.name)
    if response is None:
        await message.answer("Internal error.")
        return

    await message.answer(str(response["data"]))