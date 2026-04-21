import json
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
from src.formatting import json_pre_html
from src.fsm import UserState
from src.i18n import tr
from src.routes import start
from src.validation import is_valid_k8s_dns_label

router = Router()


@dataclass(kw_only=True)
class DeploymentData:
    name: str

    @staticmethod
    def parse_command(text: str) -> "DeploymentData | None":
        tokens = text.split()

        if len(tokens) != 2:
            return None

        if tokens[0].split("@", 1)[0] != "/deployments":
            return None

        if not is_valid_k8s_dns_label(tokens[1]):
            return None

        return DeploymentData(name=tokens[1])


def _is_bare_deployments_command(text: str) -> bool:
    parts = text.split()
    if len(parts) != 1:
        return False
    head = parts[0].split("@", 1)[0]
    return head == "/deployments"


async def deployments_picker_keyboard(
    deployments: list[dict[str, str]],
    state: FSMContext,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=await tr(state, "return_all"),
                callback_data="deployments-all",
            ),
            InlineKeyboardButton(
                text=await tr(state, "cancel"),
                callback_data="deployments-cancel",
            ),
        ],
    ]
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text=f"{dep['namespace']}/{dep['name']}",
                    callback_data=f"deployments-pick-{idx}",
                )
            ]
            for idx, dep in enumerate(deployments[:20])
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _open_deployments_picker(message: Message, state: FSMContext) -> None:
    deployments = api.v1.kubernetes.metrics.deployments()
    if deployments is None or len(deployments) == 0:
        await start.return_to_main_menu(
            message,
            state,
            notice=await tr(state, "could_not_load_deployments"),
            history_command="/deployments",
        )
        return

    options = [{"namespace": d["namespace"], "name": d["name"]} for d in deployments]
    await state.update_data(deployments_options=options)
    await state.set_state(UserState.deployments_prompted)
    await start.edit_main_menu_stage(
        message,
        state,
        await tr(state, "deployments_choose_deployment"),
        reply_markup=await deployments_picker_keyboard(options, state),
    )


@router.callback_query(StateFilter(UserState.default, UserState.awaiting_go_home), F.data == "deployments")
async def callback_deployments(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await query.answer()
    await start.flush_pending_go_home_if_any(query.message, state)
    await _open_deployments_picker(query.message, state)


@router.callback_query(UserState.deployments_prompted, F.data == "deployments-all")
async def callback_deployments_all(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await query.answer()

    response = api.v1.kubernetes.metrics.deployments()
    if response is None:
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "internal_error"),
            history_command="/deployments (all)",
        )
        return

    plain = json.dumps(response, indent=2)[:3500]
    await start.return_to_main_menu(
        query.message,
        state,
        notice=json_pre_html(plain),
        history_line=await start.build_history_entry(state, "/deployments (all)", plain),
        notice_parse_mode=ParseMode.HTML,
    )


@router.callback_query(UserState.deployments_prompted, F.data.startswith("deployments-pick-"))
async def callback_deployments_pick(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return

    data = await state.get_data()
    options: list[dict[str, str]] = data.get("deployments_options", [])
    idx_str = query.data.removeprefix("deployments-pick-")
    if not idx_str.isdigit():
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "invalid_selection"),
            history_command="/deployments",
        )
        return

    idx = int(idx_str)
    if idx < 0 or idx >= len(options):
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "invalid_selection"),
            history_command="/deployments",
        )
        return

    selected = options[idx]
    name = selected["name"]
    response = api.v1.kubernetes.metrics.deployments_by_name(name)
    if response is None:
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "internal_error"),
            history_command=f"/deployments {name}",
        )
        return

    plain = json.dumps(response, indent=2)[:3500]
    await start.return_to_main_menu(
        query.message,
        state,
        notice=json_pre_html(plain),
        history_line=await start.build_history_entry(
            state, f"/deployments {name}", plain
        ),
        notice_parse_mode=ParseMode.HTML,
    )


@router.callback_query(UserState.deployments_prompted, F.data == "deployments-cancel")
async def callback_deployments_cancel(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    assert query.message is not None
    await start.return_to_main_menu(query.message, state)


@router.message(UserState.default, Command("deployments"))
async def command_deployments(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    deployment_data = DeploymentData.parse_command(message.text)
    if deployment_data is None:
        if _is_bare_deployments_command(message.text):
            await _open_deployments_picker(message, state)
            return
        await start.edit_main_menu_stage_with_go_home(
            message,
            state,
            await tr(state, "deployments_invalid_usage"),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    response = api.v1.kubernetes.metrics.deployments_by_name(deployment_data.name)
    if response is None:
        await start.return_to_main_menu(
            message,
            state,
            notice=await tr(state, "internal_error"),
            history_command=f"/deployments {deployment_data.name}",
        )
        return

    plain = json.dumps(response, indent=2)[:3500]
    await start.return_to_main_menu(
        message,
        state,
        notice=json_pre_html(plain),
        history_line=await start.build_history_entry(
            state, f"/deployments {deployment_data.name}", plain
        ),
        notice_parse_mode=ParseMode.HTML,
    )
