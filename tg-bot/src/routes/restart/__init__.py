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
from src.routes.actions_password import (
    prompt_actions_password,
    requires_actions_password,
)
from src.routes.status_view import format_deployment_status
from src.validation import is_valid_k8s_dns_label

router = Router()


@dataclass(kw_only=True)
class RestartData:
    namespace: str
    name: str

    @staticmethod
    def parse_command(text: str) -> "RestartData | None":
        tokens = text.split()

        if len(tokens) != 2:
            return None

        if tokens[0] != "/restart":
            return None

        args = tokens[1].split(":")

        if len(args) != 2:
            return None

        if not is_valid_k8s_dns_label(args[0]) or not is_valid_k8s_dns_label(args[1]):
            return None

        return RestartData(namespace=args[0], name=args[1])


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


async def begin_restart_menu_flow(message: Message, state: FSMContext) -> None:
    await start.flush_pending_go_home_if_any(message, state)

    deployments = api.v1.kubernetes.metrics.deployments()
    if deployments is None or len(deployments) == 0:
        await start.return_to_main_menu(
            message,
            state,
            notice=await tr(state, "could_not_load_deployments"),
            history_command="/restart",
        )
        return

    options = [{"namespace": d["namespace"], "name": d["name"]} for d in deployments]
    await state.update_data(restart_deployments=options)
    await state.set_state(UserState.restart_pick_deployment)
    await start.edit_main_menu_stage(
        message,
        state,
        await tr(state, "restart_choose_deployment"),
        reply_markup=await deployments_keyboard(
            options, state, "restart-pick-", "restart-cancel"
        ),
    )


async def complete_restart(
    message: Message,
    state: FSMContext,
    namespace: str,
    name: str,
) -> None:
    response = api.v1.kubernetes.service.restart(namespace, name)
    cmd = f"/restart {namespace}:{name}"
    if response is None:
        await start.return_to_main_menu(
            message,
            state,
            notice=await tr(state, "internal_error"),
            history_command=cmd,
        )
        return
    notice = await tr(
        state,
        "restart_requested",
        namespace=namespace,
        name=name,
    )
    status_response = api.v1.kubernetes.service.status(namespace, name)
    if status_response is not None:
        language = await get_effective_language(state)
        notice = notice + "\n\n" + format_deployment_status(
            namespace,
            name,
            status_response["data"],
            language,
        )
    await start.return_to_main_menu(
        message, state, notice=notice, history_command=cmd
    )


async def run_restart_or_prompt_password(
    message: Message,
    state: FSMContext,
    namespace: str,
    name: str,
) -> None:
    if requires_actions_password():
        await prompt_actions_password(
            message,
            state,
            {"kind": "restart_exec", "namespace": namespace, "name": name},
        )
        return
    await complete_restart(message, state, namespace, name)


@router.callback_query(StateFilter(UserState.default, UserState.awaiting_go_home), F.data == "restart")
async def query_restart(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await start.flush_pending_go_home_if_any(query.message, state)
    await begin_restart_menu_flow(query.message, state)


@router.callback_query(UserState.restart_pick_deployment, F.data.startswith("restart-pick-"))
async def query_restart_pick(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return

    data = await state.get_data()
    options: list[dict[str, str]] = data.get("restart_deployments", [])
    idx_str = query.data.removeprefix("restart-pick-")
    if not idx_str.isdigit():
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "invalid_selection"),
            history_command="/restart",
        )
        return

    idx = int(idx_str)
    if idx < 0 or idx >= len(options):
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "invalid_selection"),
            history_command="/restart",
        )
        return

    selected = options[idx]
    await run_restart_or_prompt_password(
        query.message, state, selected["namespace"], selected["name"]
    )


@router.callback_query(UserState.restart_pick_deployment, F.data == "restart-cancel")
async def query_restart_cancel(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await start.return_to_main_menu(query.message, state)


@router.message(UserState.default, Command("restart"))
async def command_restart(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    restart_data = RestartData.parse_command(message.text)
    if restart_data is None:
        await state.set_state(UserState.restart_prompted_name)
        await start.edit_main_menu_stage_with_go_home(
            message,
            state,
            await tr(state, "restart_invalid_usage"),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    await run_restart_or_prompt_password(
        message, state, restart_data.namespace, restart_data.name
    )
