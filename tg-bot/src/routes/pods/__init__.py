import json
from dataclasses import dataclass

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from src import api
from src.fsm import UserState
from src.routes import start

router = Router()


@router.callback_query(UserState.default, F.data == "pods")
async def callback_pods(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None:
        return

    response = api.v1.kubernetes.metrics.pods(None)
    if response is None:
        await query.message.answer("Internal error.")
        await start.command_start(query.message, state)
        return

    await query.message.answer(
        f"```json\n{json.dumps(response, indent=2)[:4000]}```",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    await start.command_start(query.message, state)


@dataclass(kw_only=True)
class PodsData:
    namespace: str | None

    @staticmethod
    def parse_command(text: str) -> "PodsData | None":
        tokens = text.split()

        if len(tokens) not in [1, 2]:
            return None

        if tokens[0] != "/pods":
            return None

        if len(tokens) == 2:
            return PodsData(namespace=tokens[1])
        else:
            return PodsData(namespace=None)


@router.message(UserState.default, Command("pods"))
async def command_pods(message: Message) -> None:
    assert message.text is not None

    pods_data = PodsData.parse_command(message.text)
    if pods_data is None:
        await message.answer("`/pods [NAMESPACE]`", parse_mode=ParseMode.MARKDOWN_V2)
        return

    response = api.v1.kubernetes.metrics.pods(pods_data.namespace)
    if response is None:
        await message.answer("Internal error.")
        return

    await message.answer(
        f"```json\n{json.dumps(response, indent=2)[:4000]}```",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
