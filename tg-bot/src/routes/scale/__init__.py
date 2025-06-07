from dataclasses import dataclass

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.fsm import UserState

router = Router()


@dataclass(kw_only=True)
class ScaleData:
    service: str
    n: int

    @staticmethod
    def parse_command(text: str) -> "ScaleData | None":
        tokens = text.split()

        if len(tokens) != 3:
            return None

        if tokens[0] != "/scale":
            return None

        if not tokens[2].startswith("+"):
            return None

        try:
            n = int(tokens[2])
        except ValueError:
            return None

        return ScaleData(service=tokens[1], n=int(n))


@router.message(Command("scale"))
async def command_scale(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    scale_data = ScaleData.parse_command(message.text)
    if scale_data is None:
        await state.set_state(UserState.scale_bad_format)
        await scale_bad_format(message)
        return

    await scale_good_format(message, state, scale_data)


@router.message(UserState.scale_bad_format)
async def scale_bad_format(message: Message) -> None:
    await message.reply("/scale <SERVICE_NAME> +<N>")
    raise NotImplementedError


async def scale_good_format(
    message: Message,
    state: FSMContext,
    scale_data: ScaleData,
) -> None:
    await message.reply(f"received /scale {scale_data.service} +{scale_data.n}")
    await state.set_state(UserState.default)
    raise NotImplementedError
