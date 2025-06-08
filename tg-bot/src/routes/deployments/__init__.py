import json
from dataclasses import dataclass

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from src import api
from src.fsm import UserState
from src.routes import start

router = Router()


@dataclass(kw_only=True)
class DeploymentData:
    name: str

    @staticmethod
    def parse_command(text: str) -> "DeploymentData | None":
        tokens = text.split()

        if len(tokens) != 2:
            return None

        if tokens[0] != "/deployments":
            return None

        return DeploymentData(name=tokens[1])


def message_text() -> str:
    return "Send the name of a specific deployment or press the button."


def inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Return all", callback_data="deployments-all")]
        ],
    )


@router.callback_query(UserState.default, F.data == "deployments")
async def callback_deployments(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await query.message.answer(message_text(), reply_markup=inline_keyboard())
    await state.set_state(UserState.deployments)


@router.message(UserState.default, Command("deployments"), F.text == "/deployments")
async def command_deployments_pure(message: Message, state: FSMContext) -> None:
    await message.answer(message_text(), reply_markup=inline_keyboard())
    await state.set_state(UserState.deployments)


@router.callback_query(UserState.deployments, F.data == "deployments-all")
async def callback_deployments_all(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None

    response = api.v1.kubernetes.metrics.deployments()
    if response is None:
        await query.message.answer("Internal error.")
        await start.command_start(query.message, state)
        return

    await query.message.answer(
        f"```json\n{json.dumps(response, indent=2)[:4000]}```",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    await start.command_start(query.message, state)


@router.message(UserState.deployments)
async def d(message: Message, state: FSMContext) -> None:
    if message.text is None:
        await message.answer("Your message should contain text.")
        return

    response = api.v1.kubernetes.metrics.deployments_by_name(message.text)
    if response is None:
        await message.answer("Internal error.")
        await start.command_start(message, state)
        return

    await message.answer(
        f"```json\n{json.dumps(response, indent=2)[:4000]}```",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


@router.message(UserState.default, Command("deployments"))
async def command_deployments(message: Message) -> None:
    assert message.text is not None

    deployment_data = DeploymentData.parse_command(message.text)
    if deployment_data is None:
        await message.answer("`/deployments <NAME>`", parse_mode=ParseMode.MARKDOWN_V2)
        return

    response = api.v1.kubernetes.metrics.deployments_by_name(deployment_data.name)
    if response is None:
        await message.answer("Internal error.")
        return

    await message.answer(
        f"```json\n{json.dumps(response, indent=2)[:4000]}```",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
