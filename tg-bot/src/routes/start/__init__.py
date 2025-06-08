from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from src.fsm import UserState

router = Router()


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await show_menu(message, state)


async def show_menu(message: Message, state: FSMContext) -> None:
    keyboard = [
        [InlineKeyboardButton(text="Deployments", callback_data="deployments")],
        [InlineKeyboardButton(text="Pods", callback_data="pods")],
        [InlineKeyboardButton(text="Restart", callback_data="restart")],
        [InlineKeyboardButton(text="Rollback", callback_data="rollback")],
        [InlineKeyboardButton(text="Scale", callback_data="scale")],
        [InlineKeyboardButton(text="Status", callback_data="status")],
    ]

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer("Choose an action.", reply_markup=markup)

    await state.clear()
    await state.set_state(UserState.default)
