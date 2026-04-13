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
from src.routes.status_view import format_deployment_status

router = Router()


def deployments_keyboard(
    deployments: list[dict[str, str]],
    prefix: str,
    cancel_data: str,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{dep['namespace']}/{dep['name']}",
                callback_data=f"{prefix}{idx}",
            )
        ]
        for idx, dep in enumerate(deployments[:20])
    ]
    rows.append([InlineKeyboardButton(text="Cancel", callback_data=cancel_data)])
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

        return StatusData(namespace=args[0], name=args[1])


@router.callback_query(UserState.default, F.data == "status")
async def query_status(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None:
        return

    deployments = api.v1.kubernetes.metrics.deployments()
    if deployments is None or len(deployments) == 0:
        await query.message.answer("Could not load deployments.")
        await start.command_start(query.message, state)
        return

    options = [{"namespace": d["namespace"], "name": d["name"]} for d in deployments]
    await state.update_data(status_deployments=options)
    await state.set_state(UserState.status_prompted)
    await query.message.answer(
        "Choose deployment to check status:",
        reply_markup=deployments_keyboard(options, "status-pick-", "status-cancel"),
    )


@router.callback_query(UserState.status_prompted, F.data.startswith("status-pick-"))
async def query_status_pick(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None:
        return

    data = await state.get_data()
    options: list[dict[str, str]] = data.get("status_deployments", [])
    idx_str = query.data.removeprefix("status-pick-")
    if not idx_str.isdigit():
        await query.message.answer("Invalid selection.")
        await start.command_start(query.message, state)
        return

    idx = int(idx_str)
    if idx < 0 or idx >= len(options):
        await query.message.answer("Invalid selection.")
        await start.command_start(query.message, state)
        return

    selected = options[idx]
    response = api.v1.kubernetes.service.status(selected["namespace"], selected["name"])
    if response is None:
        await query.message.answer("Internal error.")
        await start.command_start(query.message, state)
        return

    await query.message.answer(
        format_deployment_status(
            selected["namespace"],
            selected["name"],
            response["data"],
        )
    )
    await start.command_start(query.message, state)


@router.callback_query(UserState.status_prompted, F.data == "status-cancel")
async def query_status_cancel(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None:
        return
    await query.message.answer("Operation cancelled.")
    await start.command_start(query.message, state)


@router.message(UserState.default, Command("status"))
async def command_status(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    status_data = StatusData.parse_command(message.text)
    if status_data is None:
        deployments = api.v1.kubernetes.metrics.deployments()
        if deployments is None or len(deployments) == 0:
            await message.answer(
                "`/status <NAMESPACE>:<NAME>`",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return

        options = [{"namespace": d["namespace"], "name": d["name"]} for d in deployments]
        await state.update_data(status_deployments=options)
        await state.set_state(UserState.status_prompted)
        await message.answer(
            "Choose deployment to check status:",
            reply_markup=deployments_keyboard(options, "status-pick-", "status-cancel"),
        )
        return

    response = api.v1.kubernetes.service.status(status_data.namespace, status_data.name)
    if response is None:
        await message.answer("Internal error.")
        return

    await message.answer(
        format_deployment_status(
            status_data.namespace,
            status_data.name,
            response["data"],
        )
    )
    await start.command_start(message, state)
