from dataclasses import dataclass

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.fsm import UserState
from src.routes import start

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


def prompt_version_message() -> str:
    return "What version should we roll back the deployment to?"


@router.message(UserState.default, Command("rollback"), F.text == "/rollback")
async def command_rollback_pure(message: Message, state: FSMContext) -> None:
    await message.answer(prompt_version_message())
    await state.set_state(UserState.rollback_prompted_version)


@router.callback_query(UserState.default, F.data == "rollback")
async def query_rollback(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await query.message.answer(prompt_version_message())
    await state.set_state(UserState.rollback_prompted_version)


@router.message(UserState.rollback_prompted_version)
async def received_version(message: Message, state: FSMContext) -> None:
    if message.text is None:
        await command_rollback_pure(message, state)
        return

    await state.update_data(version=message.text)
    await state.set_state(UserState.rollback_confirm)
    await confirm(message, state)


@router.message(UserState.default, Command("rollback"))
async def command_rollback(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    rollback_data = RollbackData.parse_command(message.text)
    if rollback_data is None:
        await message.answer("/rollback <VERSION>")
        return

    await state.update_data(version=rollback_data.version)
    await state.set_state(UserState.rollback_confirm)
    await confirm(message, state)


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
    version: str | None = await state.get_value("version")
    assert version is not None

    assert query.message is not None
    await query.message.answer(f"Pseudo rolling back to version {version}…")

    await start.command_start(query.message, state)


@router.callback_query(UserState.rollback_confirm, F.data == "rollback-no")
async def dont_roll_back(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await query.message.answer("Operation cancelled.")

    await start.command_start(query.message, state)
