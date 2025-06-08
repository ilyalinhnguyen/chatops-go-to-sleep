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
class UpdateData:
    namespace: str
    name: str
    image: str  

    @staticmethod
    def parse_command(text: str) -> "UpdateData | None":
        tokens = text.split()

        if len(tokens) != 3:  
            return None

        if tokens[0] != "/update":
            return None

        args = tokens[1].split(":")
        if len(args) != 2:
            return None

        return UpdateData(namespace=args[0], name=args[1], image=tokens[2])


@router.callback_query(UserState.default, F.data == "update")
async def query_update(query: CallbackQuery) -> None:
    assert query.message is not None
    await query.message.answer("received a /update")


@router.message(UserState.default, Command("update"))
async def command_update(message: Message) -> None:
    assert message.text is not None

    update_data = UpdateData.parse_command(message.text)
    if update_data is None:
        await message.answer(
            "`/update <NAMESPACE>:<NAME> <NEW_IMAGE>`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    response = api.v1.kubernetes.service.update(
        namespace=update_data.namespace,
        name=update_data.name,
        image=update_data.image
    )
    if response is None:
        await message.answer("Internal error.")
        return

    await message.answer(str(response["data"]))