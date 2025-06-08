from dataclasses import dataclass

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, exception
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.fsm import UserState
from src.routes import start
from src import api

router = Router()


@dataclass(kw_only=True)
class RollbackData:
    namespace: str
    name: str

    @staticmethod
    def parse_command(text: str) -> "RollbackData | None":
        tokens = text.split()

        if len(tokens) != 2:
            return None

        if tokens[0] != "/rollback":
            return None

        args = tokens[1].split(":")
        if len(args) != 2:
            return None

        return RollbackData(namespace=args[0], name=args[1])


def prompt_version_message() -> str:
    return "What version should we roll back the deployment to?"


# @router.message(UserState.default, Command("rollback"), F.text == "/rollback")
# async def command_rollback_pure(message: Message, state: FSMContext) -> None:
#     await message.answer(prompt_version_message())
#     await state.set_state(UserState.rollback_prompted_version)


@router.callback_query(UserState.default, F.data == "rollback")
async def query_rollback(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await query.message.answer(prompt_version_message())
    await state.set_state(UserState.rollback_prompted_version)


# @router.message(UserState.rollback_prompted_version)
# async def received_version(message: Message, state: FSMContext) -> None:
    # if message.text is None:
        # await command_rollback_pure(message, state)
        # return
#
    # await state.update_data(version=message.text)
    # await state.set_state(UserState.rollback_confirm)
    # await confirm(message, state)


@router.message(UserState.default, Command("rollback"))
async def command_rollback(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    rollback_data = RollbackData.parse_command(message.text)
    if rollback_data is None:
        await message.answer(
            "`/rollback <NAMESPACE>:<NAME>`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    await state.update_data(
        namespace=rollback_data.namespace,
        name=rollback_data.name,
    )
    await state.set_state(UserState.rollback_confirm)
    # await confirm(message, state)

    keyboard = [
        [
            InlineKeyboardButton(text="Yes", callback_data="rollback-yes"),
            InlineKeyboardButton(text="No", callback_data="rollback-no"),
        ],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(
        f"Are you sure you want to roll back `{rollback_data.name}` in `{rollback_data.namespace}`?",
        reply_markup=markup,
        parse_mode=ParseMode.MARKDOWN,
    )


async def confirm(message: Message, state: FSMContext) -> None:
    version: str | None = await state.get_value("version")
    assert version is not None

    keyboard = [
        [
            InlineKeyboardButton(text="Yes", callback_data="rollback-yes"),
            InlineKeyboardButton(text="No", callback_data="rollback-no"),
        ],
    ]

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(
        f"Are you sure you want to roll back to version {version}?",
        reply_markup=markup,
    )


@router.callback_query(UserState.rollback_confirm, F.data == "rollback-yes")
async def roll_back(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    namespace: str|None = data.get("namespace")
    name: str|None = data.get("name")

    if query.message is None:
        return

    if not all([namespace, name]):
        await query.message.answer("Missing rollback data.")
        await start.command_start(query.message, state)
        return

    await query.message.answer("Rolling back, please wait...")
   
    if namespace is None or name is None:
        return

    result = api.v1.kubernetes.service.rollback(namespace, name)

    if type(result) is str:
        if result == "Internal Server Error":
            await query.message.answer("No revision found for deployment")
            return

        await query.message.answer(result)
        return

    await query.message.answer(str(result))

    await start.command_start(query.message, state)


@router.callback_query(UserState.rollback_confirm, F.data == "rollback-no")
async def dont_roll_back(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await query.message.answer("Operation cancelled.")

    await start.command_start(query.message, state)
