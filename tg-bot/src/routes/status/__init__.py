from dataclasses import dataclass

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from src import api
from src.fsm import UserState
from aiogram.fsm.context import FSMContext
from src.routes import start

router = Router()


@dataclass(kw_only=True)
class StatusData:
    namespace: str
    name: str

    @staticmethod
    def parse_command(text: str) -> "StatusData | None":
        tokens = text.split()

        if len(tokens) != 2:
            return None

        if tokens[0] != "/status":
            return None

        args = tokens[1].split(":")

        if len(args) != 2:
            return None

        return StatusData(namespace=args[0], name=args[1])


@router.callback_query(UserState.default, F.data == "status")
async def query_status(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await query.message.answer("received a /status")
    await state.set_state(UserState.status_prompted)


@router.message(UserState.default, Command("status"))
async def command_status(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    status_data = StatusData.parse_command(message.text)
    if status_data is None:
        await message.answer(
            "`/status <NAMESPACE>:<NAME>`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    response = api.v1.kubernetes.service.status(status_data.namespace, status_data.name)
    if response is None:
        await message.answer("Internal error.")
        return

    await message.answer(str(response["data"]))
    await start.command_start(message, state)
