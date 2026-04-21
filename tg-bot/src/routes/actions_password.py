"""Password gate for restart / rollback / scale — only right before API (TG_ACTIONS_PASSWORD)."""

import os
import secrets

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.fsm import UserState
from src.i18n import tr
from src.routes import start

router = Router()

PASSWORD_GATE_KEY = "password_gate"
SENSITIVE_CANCEL = "sensitive-cancel"


def requires_actions_password() -> bool:
    v = os.getenv("TG_ACTIONS_PASSWORD")
    return v is not None and v.strip() != ""


def verify_actions_password(user_input: str) -> bool:
    if not requires_actions_password():
        return True
    expected = os.getenv("TG_ACTIONS_PASSWORD", "").strip()
    return secrets.compare_digest(user_input.strip(), expected)


async def _cancel_keyboard(state: FSMContext) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=await tr(state, "cancel"),
                    callback_data=SENSITIVE_CANCEL,
                )
            ],
        ]
    )


async def prompt_actions_password(message: Message, state: FSMContext, gate: dict) -> None:
    await state.set_state(UserState.awaiting_actions_password)
    await state.update_data(**{PASSWORD_GATE_KEY: gate})
    await start.edit_main_menu_stage(
        message,
        state,
        await tr(state, "actions_password_prompt"),
        reply_markup=await _cancel_keyboard(state),
    )


@router.callback_query(UserState.awaiting_actions_password, F.data == SENSITIVE_CANCEL)
async def sensitive_cancel(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await state.update_data(**{PASSWORD_GATE_KEY: None})
    await start.return_to_main_menu(query.message, state)


@router.message(UserState.awaiting_actions_password, F.text)
async def sensitive_password_message(message: Message, state: FSMContext) -> None:
    if not verify_actions_password(message.text or ""):
        await start.edit_main_menu_stage(
            message,
            state,
            await tr(state, "actions_password_wrong"),
            reply_markup=await _cancel_keyboard(state),
        )
        return

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    data = await state.get_data()
    gate: dict | None = data.get(PASSWORD_GATE_KEY)
    await state.update_data(**{PASSWORD_GATE_KEY: None})
    if not gate:
        await start.return_to_main_menu(message, state)
        return

    kind = gate.get("kind")
    if kind == "restart_exec":
        from src.routes import restart as restart_mod

        await restart_mod.complete_restart(
            message, state, str(gate["namespace"]), str(gate["name"])
        )
        return
    if kind == "rollback_exec":
        from src.routes import rollback as rollback_mod

        await rollback_mod.complete_rollback(
            message, state, str(gate["namespace"]), str(gate["name"])
        )
        return
    if kind == "scale_exec":
        from src.routes import scale as scale_mod

        await scale_mod.complete_scale(
            message,
            state,
            str(gate["namespace"]),
            str(gate["name"]),
            int(gate["replicas"]),
        )
        return

    await start.return_to_main_menu(message, state)
