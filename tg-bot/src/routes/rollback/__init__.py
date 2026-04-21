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

from src.fsm import UserState
from src.i18n import get_effective_language, tr
from src.routes import start
from src import api
from src.routes.actions_password import (
    prompt_actions_password,
    requires_actions_password,
)
from src.routes.status_view import format_deployment_status
from src.validation import is_valid_k8s_dns_label

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

        if not is_valid_k8s_dns_label(args[0]) or not is_valid_k8s_dns_label(args[1]):
            return None

        return RollbackData(namespace=args[0], name=args[1])


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


async def rollback_confirmation_keyboard(state: FSMContext) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text=await tr(state, "yes"), callback_data="rollback-yes"),
            InlineKeyboardButton(text=await tr(state, "no"), callback_data="rollback-no"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def begin_rollback_menu_flow(message: Message, state: FSMContext) -> None:
    await start.flush_pending_go_home_if_any(message, state)

    deployments = api.v1.kubernetes.metrics.deployments()
    if deployments is None or len(deployments) == 0:
        await start.return_to_main_menu(
            message,
            state,
            notice=await tr(state, "could_not_load_deployments"),
            history_command="/rollback",
        )
        return

    options = [{"namespace": d["namespace"], "name": d["name"]} for d in deployments]
    await state.update_data(rollback_deployments=options)
    await state.set_state(UserState.rollback_pick_deployment)
    await start.edit_main_menu_stage(
        message,
        state,
        await tr(state, "rollback_choose_deployment"),
        reply_markup=await deployments_keyboard(
            options, state, "rollback-pick-", "rollback-cancel"
        ),
    )


async def show_rollback_confirm(
    message: Message, state: FSMContext, namespace: str, name: str
) -> None:
    await state.update_data(namespace=namespace, name=name)
    await state.set_state(UserState.rollback_confirm)

    await start.edit_main_menu_stage(
        message,
        state,
        await tr(
            state,
            "rollback_confirm",
            name=name,
            namespace=namespace,
        ),
        reply_markup=await rollback_confirmation_keyboard(state),
        parse_mode=ParseMode.MARKDOWN,
    )


async def complete_rollback(
    message: Message,
    state: FSMContext,
    namespace: str,
    name: str,
) -> None:
    cmd = f"/rollback {namespace}:{name}"
    result = api.v1.kubernetes.service.rollback(namespace, name)

    if type(result) is str:
        if result == "Internal Server Error":
            await start.return_to_main_menu(
                message,
                state,
                notice=await tr(state, "rollback_no_revision"),
                history_command=cmd,
            )
            return

        await start.return_to_main_menu(
            message, state, notice=result, history_command=cmd
        )
        return

    notice = await tr(state, "rollback_requested", namespace=namespace, name=name)
    notice = notice + "\n\n" + str(result)
    status_response = api.v1.kubernetes.service.status(namespace, name)
    if status_response is not None:
        language = await get_effective_language(state)
        notice = notice + "\n\n" + format_deployment_status(
            namespace, name, status_response["data"], language
        )

    await start.return_to_main_menu(
        message, state, notice=notice, history_command=cmd
    )


async def run_rollback_or_prompt_password(
    message: Message,
    state: FSMContext,
    namespace: str,
    name: str,
) -> None:
    if requires_actions_password():
        await prompt_actions_password(
            message,
            state,
            {"kind": "rollback_exec", "namespace": namespace, "name": name},
        )
        return
    await complete_rollback(message, state, namespace, name)


@router.callback_query(StateFilter(UserState.default, UserState.awaiting_go_home), F.data == "rollback")
async def query_rollback(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await start.flush_pending_go_home_if_any(query.message, state)
    await begin_rollback_menu_flow(query.message, state)


@router.callback_query(UserState.rollback_pick_deployment, F.data.startswith("rollback-pick-"))
async def query_rollback_pick(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return

    data = await state.get_data()
    options: list[dict[str, str]] = data.get("rollback_deployments", [])
    idx_str = query.data.removeprefix("rollback-pick-")
    if not idx_str.isdigit():
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "invalid_selection"),
            history_command="/rollback",
        )
        return

    idx = int(idx_str)
    if idx < 0 or idx >= len(options):
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "invalid_selection"),
            history_command="/rollback",
        )
        return

    selected = options[idx]
    await show_rollback_confirm(
        query.message, state, selected["namespace"], selected["name"]
    )


@router.callback_query(UserState.rollback_pick_deployment, F.data == "rollback-cancel")
async def query_rollback_cancel(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await start.return_to_main_menu(query.message, state)


@router.message(UserState.default, Command("rollback"))
async def command_rollback(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    rollback_data = RollbackData.parse_command(message.text)
    if rollback_data is None:
        deployments = api.v1.kubernetes.metrics.deployments()
        if deployments is None or len(deployments) == 0:
            await start.edit_main_menu_stage_with_go_home(
                message,
                state,
                await tr(state, "rollback_invalid_usage"),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return

        await begin_rollback_menu_flow(message, state)
        return

    await show_rollback_confirm(
        message, state, rollback_data.namespace, rollback_data.name
    )


@router.callback_query(UserState.rollback_confirm, F.data == "rollback-yes")
async def roll_back(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    namespace: str | None = data.get("namespace")
    name: str | None = data.get("name")

    if query.message is None:
        return

    if not all([namespace, name]):
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "rollback_missing_data"),
            history_command="/rollback",
        )
        return

    if namespace is None or name is None:
        return

    await run_rollback_or_prompt_password(query.message, state, namespace, name)


@router.callback_query(UserState.rollback_confirm, F.data == "rollback-no")
async def dont_roll_back(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    assert query.message is not None
    await start.return_to_main_menu(query.message, state)
