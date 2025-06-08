from dataclasses import dataclass
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery
from src import api
from src.fsm import UserState
from aiogram.fsm.context import FSMContext
from src.routes import start

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
    return "What service would you like to change the number of replicas of?"


@router.callback_query(UserState.default, F.data == "scale")
async def query_scale(query: CallbackQuery, state: FSMContext) -> None:
    assert query.message is not None
    await state.set_state(UserState.scale_prompted_service)
    await query.message.answer("received a /scale")


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
        f"Scaled {scale_data.namespace}:{scale_data.name} to {scale_data.replicas} replicas\n"
        f"Response: {response['data']}"
    )
    await start.command_start(message, state)
