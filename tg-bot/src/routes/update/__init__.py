from dataclasses import dataclass

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.types.callback_query import CallbackQuery
from src import api
from src.fsm import UserState
from src.routes import start

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
    await query.message.answer("Not implemented :(\nUse /update")


@router.message(UserState.default, Command("update"))
async def command_update(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    update_data = UpdateData.parse_command(message.text)
    if update_data is None:
        await message.answer(
            "`/update <NAMESPACE>:<NAME> <NEW_IMAGE>`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    await state.set_state(UserState.update_confirm)
    await confirm(message, state)


async def confirm(message: Message, state: FSMContext) -> None:
    namespace: str | None = await state.get_value("namespace")
    assert namespace is not None
    name: str | None = await state.get_value("name")
    assert name is not None
    image: str | None = await state.get_value("image")
    assert image is not None

    keyboard = [
        [
            InlineKeyboardButton(text="Yes", callback_data="update-yes"),
            InlineKeyboardButton(text="No", callback_data="update-no"),
        ],
    ]

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(
        f"Are you sure you want to update the image of the service {namespace}:{name} to {image}?",
        reply_markup=markup,
    )


@router.callback_query(UserState.update_confirm, F.data == "update-yes")
async def do_update(query: CallbackQuery, state: FSMContext) -> None:
    namespace: str | None = await state.get_value("namespace")
    assert namespace is not None
    name: str | None = await state.get_value("name")
    assert name is not None
    image: str | None = await state.get_value("image")
    assert image is not None

    assert query.message is not None

    response = api.v1.kubernetes.service.update_image(
        namespace=namespace,
        name=name,
        image=image,
    )
    if response is None:
        await query.message.answer("Internal error.")
        return

    await query.message.answer(str(response["data"]))

    await start.command_start(query.message, state)


@router.callback_query(UserState.update_confirm, F.data == "update-no")
async def dont_update(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await query.message.answer("Operation cancelled.")

    await start.command_start(query.message, state)
