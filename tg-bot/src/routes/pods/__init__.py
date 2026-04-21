import json
from dataclasses import dataclass

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from src import api
from src.formatting import json_pre_html
from src.fsm import UserState
from src.i18n import tr
from src.routes import start
from src.validation import is_valid_k8s_dns_label

router = Router()


@router.callback_query(StateFilter(UserState.default, UserState.awaiting_go_home), F.data == "pods")
async def callback_pods(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await start.flush_pending_go_home_if_any(query.message, state)

    response = api.v1.kubernetes.metrics.pods(None)
    if response is None:
        await start.return_to_main_menu(
            query.message,
            state,
            notice=await tr(state, "internal_error"),
            history_command="/pods",
        )
        return

    plain = json.dumps(response, indent=2)[:3500]
    await start.return_to_main_menu(
        query.message,
        state,
        notice=json_pre_html(plain),
        history_line=await start.build_history_entry(state, "/pods", plain),
        notice_parse_mode=ParseMode.HTML,
    )


@dataclass(kw_only=True)
class PodsData:
    namespace: str | None

    @staticmethod
    def parse_command(text: str) -> "PodsData | None":
        tokens = text.split()

        if len(tokens) not in [1, 2]:
            return None

        if tokens[0] != "/pods":
            return None

        if len(tokens) == 2:
            if not is_valid_k8s_dns_label(tokens[1]):
                return None
            return PodsData(namespace=tokens[1])
        else:
            return PodsData(namespace=None)


@router.message(UserState.default, Command("pods"))
async def command_pods(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    pods_data = PodsData.parse_command(message.text)
    if pods_data is None:
        await start.edit_main_menu_stage_with_go_home(
            message,
            state,
            await tr(state, "pods_invalid_usage"),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    cmd = f"/pods {pods_data.namespace}" if pods_data.namespace else "/pods"
    response = api.v1.kubernetes.metrics.pods(pods_data.namespace)
    if response is None:
        await start.return_to_main_menu(
            message,
            state,
            notice=await tr(state, "internal_error"),
            history_command=cmd,
        )
        return

    plain = json.dumps(response, indent=2)[:3500]
    await start.return_to_main_menu(
        message,
        state,
        notice=json_pre_html(plain),
        history_line=await start.build_history_entry(state, cmd, plain),
        notice_parse_mode=ParseMode.HTML,
    )
