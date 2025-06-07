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

from src.fsm import UserState
from src.routes import start

router = Router()


@dataclass(kw_only=True)
class ScaleData:
    service: str
    n: int

    @staticmethod
    def parse_command(text: str) -> "ScaleData | None":
        tokens = text.split()

        if len(tokens) != 3:
            return None

        if tokens[0] != "/scale":
            return None

        if not tokens[2].startswith("+"):
            return None

        try:
            n = int(tokens[2])
        except ValueError:
            return None

        return ScaleData(service=tokens[1], n=int(n))


def prompt_service_message() -> str:
    return "What service would you like to change the number of replicas of?"


@router.message(UserState.default, Command("scale"), F.text == "/scale")
async def command_scale_pure(message: Message, state: FSMContext) -> None:
    await message.answer(prompt_service_message())
    await state.set_state(UserState.scale_prompted_service)


@router.callback_query(UserState.default, F.data == "scale")
async def query_scale(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await query.message.answer(prompt_service_message())
    await state.set_state(UserState.scale_prompted_service)


@router.message(UserState.default, Command("scale"))
async def command_scale(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    scale_data = ScaleData.parse_command(message.text)
    if scale_data is None:
        await message.answer(
            "`/scale <SERVICE_NAME> +<N>`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    await state.update_data(service=scale_data.service, n=scale_data.n)
    await state.set_state(UserState.scale_confirm)
    await confirm(message, state)


@router.message(UserState.scale_prompted_service)
async def received_service(message: Message, state: FSMContext) -> None:
    service: str | None = await state.get_value("service")
    if service is None:
        if message.text is None:
            await command_scale_pure(message, state)
            return

        service = message.text
        await state.update_data(service=message.text)
        await state.set_state(UserState.scale_prompted_n)

    await message.answer(
        f"What number of replicas should we set for the service {service}?",
    )


@router.message(UserState.scale_prompted_n)
async def received_n(message: Message, state: FSMContext) -> None:
    if message.text is None:
        await received_service(message, state)
        return

    try:
        n = int(message.text)
    except ValueError:
        await received_service(message, state)
        return

    await state.update_data(n=n)
    await state.set_state(UserState.scale_confirm)
    await confirm(message, state)


async def confirm(message: Message, state: FSMContext) -> None:
    service: str | None = await state.get_value("service")
    assert service is not None
    n: int | None = await state.get_value("n")
    assert n is not None

    keyboard = [
        [
            InlineKeyboardButton(text="Yes", callback_data="scale-yes"),
            InlineKeyboardButton(text="No", callback_data="scale-no"),
        ],
    ]

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(
        f"Are you sure you want to change the number of replicas of the service {service} to {n}?",
        reply_markup=markup,
    )


@router.callback_query(UserState.scale_confirm, F.data == "scale-yes")
async def do_scale(query: CallbackQuery, state: FSMContext) -> None:
    service: str | None = await state.get_value("service")
    assert service is not None
    n: int | None = await state.get_value("n")
    assert n is not None

    assert query.message is not None
    await query.message.answer(
        f"Pseudo changing the number of replicas of {service} to {n}…"
    )

    await start.command_start(query.message, state)


@router.callback_query(UserState.scale_confirm, F.data == "scale-no")
async def dont_scale(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await query.message.answer("Operation cancelled.")

    await start.command_start(query.message, state)
