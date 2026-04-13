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

        return RestartData(namespace=args[0], name=args[1])


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


@router.callback_query(UserState.default, F.data == "restart")
async def query_restart(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None:
        return

    deployments = api.v1.kubernetes.metrics.deployments()
    if deployments is None or len(deployments) == 0:
        await query.message.answer("Could not load deployments.")
        await start.command_start(query.message, state)
        return

    options = [{"namespace": d["namespace"], "name": d["name"]} for d in deployments]
    await state.update_data(restart_deployments=options)
    await state.set_state(UserState.restart_pick_deployment)
    await query.message.answer(
        "Choose deployment to restart:",
        reply_markup=deployments_keyboard(options, "restart-pick-", "restart-cancel"),
    )


@router.callback_query(UserState.restart_pick_deployment, F.data.startswith("restart-pick-"))
async def query_restart_pick(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None:
        return

    data = await state.get_data()
    options: list[dict[str, str]] = data.get("restart_deployments", [])
    idx_str = query.data.removeprefix("restart-pick-")
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
    response = api.v1.kubernetes.service.restart(selected["namespace"], selected["name"])
    if response is None:
        await query.message.answer("Internal error.")
        await start.command_start(query.message, state)
        return

    await query.message.answer(
        f"🔁 Restart requested for {selected['namespace']}:{selected['name']}."
    )
    status_response = api.v1.kubernetes.service.status(
        selected["namespace"], selected["name"]
    )
    if status_response is not None:
        await query.message.answer(
            format_deployment_status(
                selected["namespace"],
                selected["name"],
                status_response["data"],
            )
        )
    await start.command_start(query.message, state)


@router.callback_query(UserState.restart_pick_deployment, F.data == "restart-cancel")
async def query_restart_cancel(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None:
        return
    await query.message.answer("Operation cancelled.")
    await start.command_start(query.message, state)


@router.message(UserState.default, Command("restart"))
async def command_restart(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    restart_data = RestartData.parse_command(message.text)
    if restart_data is None:
        await state.set_state(UserState.restart_prompted_name)
        await message.answer(
            "`/restart <NAMESPACE>:<NAME>`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    response = api.v1.kubernetes.service.restart(
        restart_data.namespace, restart_data.name
    )
    if response is None:
        await message.answer("Internal error.")
        return
    await message.answer(
        f"🔁 Restart requested for {restart_data.namespace}:{restart_data.name}."
    )
    status_response = api.v1.kubernetes.service.status(
        restart_data.namespace, restart_data.name
    )
    if status_response is not None:
        await message.answer(
            format_deployment_status(
                restart_data.namespace,
                restart_data.name,
                status_response["data"],
            )
        )
    await start.command_start(message, state)
