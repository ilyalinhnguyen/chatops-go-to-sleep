from dataclasses import dataclass

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
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
from src.validation import is_valid_k8s_dns_label, parse_nonneg_int_digits_only

router = Router()


@dataclass(kw_only=True)
class ScaleData:
    namespace: str
    name: str
    replicas: int

    @staticmethod
    def parse_command(text: str) -> "ScaleData | None":
        tokens = text.split()

        if len(tokens) != 3:
            return None

        if tokens[0] != "/scale":
            return None

        service_parts = tokens[1].split(":")
        if len(service_parts) != 2:
            return None

        if not is_valid_k8s_dns_label(service_parts[0]) or not is_valid_k8s_dns_label(
            service_parts[1]
        ):
            return None

        rep = parse_nonneg_int_digits_only(tokens[2])
        if rep is None:
            return None

        return ScaleData(
            namespace=service_parts[0], name=service_parts[1], replicas=rep
        )


async def prompt_service_message(state: FSMContext) -> str:
    return await tr(state, "scale_choose_deployment")


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


async def scale_cancel_keyboard_i18n(state: FSMContext) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=await tr(state, "cancel"), callback_data="scale-cancel")],
        ]
    )


async def begin_scale_menu_flow(message: Message, state: FSMContext) -> None:
    await start.flush_pending_go_home_if_any(message, state)

    deployments = api.v1.kubernetes.metrics.deployments()
    if deployments is None or len(deployments) == 0:
        await start.return_to_main_menu(
            message,
            state,
            notice=await tr(state, "could_not_load_deployments"),
            history_command="/scale",
        )
        return

    options = [{"namespace": d["namespace"], "name": d["name"]} for d in deployments]
    await state.update_data(scale_deployments=options)
    await state.set_state(UserState.scale_prompted_service)
    await start.edit_main_menu_stage(
        message,
        state,
        await prompt_service_message(state),
        reply_markup=await deployments_keyboard(options, state, "scale-pick-", "scale-cancel"),
    )


async def complete_scale(
    message: Message,
    state: FSMContext,
    namespace: str,
    name: str,
    replicas: int,
) -> None:
    response = api.v1.kubernetes.service.scale(
        namespace=namespace,
        name=name,
        replicas=replicas,
    )

    cmd = f"/scale {namespace}:{name} {replicas}"
    if response is None:
        await start.return_to_main_menu(
            message,
            state,
            notice=await tr(state, "internal_error"),
            history_command=cmd,
        )
        return

    notice = await tr(state, "scale_done", namespace=namespace, name=name, replicas=replicas)
    status_response = api.v1.kubernetes.service.status(namespace, name)
    if status_response is not None:
        language = await get_effective_language(state)
        notice = (
            notice
            + "\n\n"
            + format_deployment_status(
                namespace,
                name,
                status_response["data"],
                language,
            )
        )

    await start.return_to_main_menu(
        message, state, notice=notice, history_command=cmd
    )


async def run_scale_or_prompt_password(
    message: Message,
    state: FSMContext,
    namespace: str,
    name: str,
    replicas: int,
) -> None:
    if requires_actions_password():
        await prompt_actions_password(
            message,
            state,
            {
                "kind": "scale_exec",
                "namespace": namespace,
                "name": name,
                "replicas": replicas,
            },
        )
        return
    await complete_scale(message, state, namespace, name, replicas)


async def execute_scale_command(
    message: Message,
    state: FSMContext,
    namespace: str,
    name: str,
    replicas: int,
) -> None:
    await run_scale_or_prompt_password(
        message, state, namespace, name, replicas
    )


@router.callback_query(StateFilter(UserState.default, UserState.awaiting_go_home), F.data == "scale")
async def query_scale(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await start.flush_pending_go_home_if_any(query.message, state)
    await begin_scale_menu_flow(query.message, state)


@router.callback_query(UserState.scale_prompted_service, F.data.startswith("scale-pick-"))
async def query_scale_pick(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return

    data = await state.get_data()
    options: list[dict[str, str]] = data.get("scale_deployments", [])
    idx_str = query.data.removeprefix("scale-pick-")

    if not idx_str.isdigit():
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "invalid_selection"),
            history_command="/scale",
        )
        return

    idx = int(idx_str)
    if idx < 0 or idx >= len(options):
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "invalid_selection"),
            history_command="/scale",
        )
        return

    selected = options[idx]
    await state.update_data(namespace=selected["namespace"], name=selected["name"])
    await state.set_state(UserState.scale_prompted_n)

    lines: list[str] = [
        await tr(
            state,
            "scale_selected_send_replicas",
            namespace=selected["namespace"],
            name=selected["name"],
        )
    ]
    status_response = api.v1.kubernetes.service.status(
        selected["namespace"], selected["name"]
    )
    if status_response is not None:
        d = status_response["data"]
        lines.append(
            await tr(
                state,
                "scale_now_replicas",
                replicas=d["replicas"],
                ready=d["ready"],
            )
        )

    text = "\n\n".join(lines)
    await start.edit_main_menu_stage(
        query.message,
        state,
        text,
        reply_markup=await scale_cancel_keyboard_i18n(state),
        parse_mode=ParseMode.MARKDOWN,
    )


async def _scale_cancel(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await start.return_to_main_menu(query.message, state)


@router.callback_query(UserState.scale_prompted_service, F.data == "scale-cancel")
async def query_scale_cancel_service(query: CallbackQuery, state: FSMContext) -> None:
    await _scale_cancel(query, state)


@router.callback_query(UserState.scale_prompted_n, F.data == "scale-cancel")
async def query_scale_cancel_n(query: CallbackQuery, state: FSMContext) -> None:
    await _scale_cancel(query, state)


async def _try_delete_user_message(message: Message) -> None:
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


@router.message(UserState.scale_prompted_n)
async def query_scale_replicas(message: Message, state: FSMContext) -> None:
    replicas = parse_nonneg_int_digits_only(message.text)
    if replicas is None:
        await start.edit_main_menu_stage(
            message,
            state,
            await tr(state, "validation_number_digits_only"),
            reply_markup=await scale_cancel_keyboard_i18n(state),
        )
        await _try_delete_user_message(message)
        return

    await _try_delete_user_message(message)

    data = await state.get_data()
    namespace: str | None = data.get("namespace")
    name: str | None = data.get("name")
    if namespace is None or name is None:
        await start.return_to_main_menu(
            message,
            state,
            notice=await tr(state, "scale_missing_selection"),
            history_command="/scale",
        )
        return

    await run_scale_or_prompt_password(
        message, state, namespace, name, replicas
    )


@router.message(UserState.default, Command("scale"))
async def command_scale(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    scale_data = ScaleData.parse_command(message.text)
    if scale_data is None:
        await start.edit_main_menu_stage_with_go_home(
            message,
            state,
            await tr(state, "scale_invalid_usage"),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    await execute_scale_command(
        message,
        state,
        scale_data.namespace,
        scale_data.name,
        scale_data.replicas,
    )
