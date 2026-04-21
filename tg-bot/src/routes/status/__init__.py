from dataclasses import dataclass

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src import api
from src.fsm import UserState
from src.i18n import get_effective_language, tr
from src.routes import start
from src.routes.status_view import format_deployment_status
from src.validation import is_valid_k8s_dns_label

router = Router()


async def deployments_keyboard(
    deployments: list[dict[str, str]],
    state: FSMContext,
    prefix: str,
    cancel_data: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=await tr(state, "cancel"), callback_data=cancel_data)],
    ]
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text=f"{dep['namespace']}/{dep['name']}",
                    callback_data=f"{prefix}{idx}",
                )
            ]
            for idx, dep in enumerate(deployments[:20])
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


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

        if not is_valid_k8s_dns_label(args[0]) or not is_valid_k8s_dns_label(args[1]):
            return None

        return StatusData(namespace=args[0], name=args[1])


@router.callback_query(StateFilter(UserState.default, UserState.awaiting_go_home), F.data == "status")
async def query_status(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await start.flush_pending_go_home_if_any(query.message, state)

    deployments = api.v1.kubernetes.metrics.deployments()
    if deployments is None or len(deployments) == 0:
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "could_not_load_deployments"),
            history_command="/status",
        )
        return

    options = [{"namespace": d["namespace"], "name": d["name"]} for d in deployments]
    await state.update_data(status_deployments=options)
    await state.set_state(UserState.status_prompted)
    await start.edit_main_menu_stage(
        query.message,
        state,
        await tr(state, "status_choose_deployment"),
        reply_markup=await deployments_keyboard(
            options, state, "status-pick-", "status-cancel"
        ),
    )


@router.callback_query(UserState.status_prompted, F.data.startswith("status-pick-"))
async def query_status_pick(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return

    data = await state.get_data()
    options: list[dict[str, str]] = data.get("status_deployments", [])
    idx_str = query.data.removeprefix("status-pick-")
    if not idx_str.isdigit():
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "invalid_selection"),
            history_command="/status",
        )
        return

    idx = int(idx_str)
    if idx < 0 or idx >= len(options):
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "invalid_selection"),
            history_command="/status",
        )
        return

    selected = options[idx]
    cmd = f"/status {selected['namespace']}:{selected['name']}"
    response = api.v1.kubernetes.service.status(selected["namespace"], selected["name"])
    if response is None:
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "internal_error"),
            history_command=cmd,
        )
        return

    language = await get_effective_language(state)
    notice = format_deployment_status(
        selected["namespace"],
        selected["name"],
        response["data"],
        language,
    )
    await start.return_to_main_menu(
        query.message, state, notice=notice, history_command=cmd
    )


@router.callback_query(UserState.status_prompted, F.data == "status-cancel")
async def query_status_cancel(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await start.return_to_main_menu(query.message, state)


@router.message(UserState.default, Command("status"))
async def command_status(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    status_data = StatusData.parse_command(message.text)
    if status_data is None:
        deployments = api.v1.kubernetes.metrics.deployments()
        if deployments is None or len(deployments) == 0:
            await start.edit_main_menu_stage_with_go_home(
                message,
                state,
                await tr(state, "status_invalid_usage"),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return

        options = [{"namespace": d["namespace"], "name": d["name"]} for d in deployments]
        await state.update_data(status_deployments=options)
        await state.set_state(UserState.status_prompted)
        await start.edit_main_menu_stage(
            message,
            state,
            await tr(state, "status_choose_deployment"),
            reply_markup=await deployments_keyboard(
                options, state, "status-pick-", "status-cancel"
            ),
        )
        return

    cmd = f"/status {status_data.namespace}:{status_data.name}"
    response = api.v1.kubernetes.service.status(status_data.namespace, status_data.name)
    if response is None:
        await start.return_to_main_menu(
            message,
            state,
            notice=await tr(state, "internal_error"),
            history_command=cmd,
        )
        return

    language = await get_effective_language(state)
    notice = format_deployment_status(
        status_data.namespace,
        status_data.name,
        response["data"],
        language,
    )
    await start.return_to_main_menu(message, state, notice=notice, history_command=cmd)
