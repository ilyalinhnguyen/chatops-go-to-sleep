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

        try:
            replicas = int(tokens[2])
            if replicas < 0:
                return None
        except ValueError:
            return None

        return ScaleData(
            namespace=service_parts[0], name=service_parts[1], replicas=replicas
        )


def prompt_service_message() -> str:
    return "Choose deployment to scale:"


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


@router.callback_query(UserState.default, F.data == "scale")
async def query_scale(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None:
        return

    deployments = api.v1.kubernetes.metrics.deployments()
    if deployments is None or len(deployments) == 0:
        await query.message.answer("Could not load deployments.")
        await start.command_start(query.message, state)
        return

    options = [{"namespace": d["namespace"], "name": d["name"]} for d in deployments]
    await state.update_data(scale_deployments=options)
    await state.set_state(UserState.scale_prompted_service)
    await query.message.answer(
        prompt_service_message(),
        reply_markup=deployments_keyboard(options, "scale-pick-", "scale-cancel"),
    )


@router.callback_query(UserState.scale_prompted_service, F.data.startswith("scale-pick-"))
async def query_scale_pick(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None:
        return

    data = await state.get_data()
    options: list[dict[str, str]] = data.get("scale_deployments", [])
    idx_str = query.data.removeprefix("scale-pick-")

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
    await state.update_data(namespace=selected["namespace"], name=selected["name"])
    await state.set_state(UserState.scale_prompted_n)
    await query.message.answer(
        f"Selected `{selected['namespace']}:{selected['name']}`. Send replicas count (e.g. `2`).",
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(UserState.scale_prompted_service, F.data == "scale-cancel")
async def query_scale_cancel(query: CallbackQuery, state: FSMContext) -> None:
    if query.message is None:
        return
    await query.message.answer("Operation cancelled.")
    await start.command_start(query.message, state)


@router.message(UserState.scale_prompted_n)
async def query_scale_replicas(message: Message, state: FSMContext) -> None:
    if message.text is None or not message.text.strip().isdigit():
        await message.answer("Send a non-negative integer replicas count.")
        return

    replicas = int(message.text.strip())
    data = await state.get_data()
    namespace: str | None = data.get("namespace")
    name: str | None = data.get("name")
    if namespace is None or name is None:
        await message.answer("Missing deployment selection.")
        await start.command_start(message, state)
        return

    response = api.v1.kubernetes.service.scale(
        namespace=namespace,
        name=name,
        replicas=replicas,
    )
    if response is None:
        await message.answer("Internal error.")
        await start.command_start(message, state)
        return

    await message.answer(f"⚖️ Scaled {namespace}:{name} to {replicas} replicas.")
    status_response = api.v1.kubernetes.service.status(namespace, name)
    if status_response is not None:
        await message.answer(
            format_deployment_status(namespace, name, status_response["data"])
        )
    await start.command_start(message, state)


@router.message(UserState.default, Command("scale"))
async def command_scale(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    scale_data = ScaleData.parse_command(message.text)
    if scale_data is None:
        await message.answer(
            "`/scale <NAMESPACE>:<NAME> <REPLICAS>`\n",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    response = api.v1.kubernetes.service.scale(
        namespace=scale_data.namespace,
        name=scale_data.name,
        replicas=scale_data.replicas,
    )

    if response is None:
        await message.answer("Internal error.")
        return

    await message.answer(
        f"⚖️ Scaled {scale_data.namespace}:{scale_data.name} to {scale_data.replicas} replicas."
    )
    status_response = api.v1.kubernetes.service.status(
        scale_data.namespace, scale_data.name
    )
    if status_response is not None:
        await message.answer(
            format_deployment_status(
                scale_data.namespace,
                scale_data.name,
                status_response["data"],
            )
        )
    await start.command_start(message, state)
