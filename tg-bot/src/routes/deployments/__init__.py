import json
from dataclasses import dataclass

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from src import api
from src.fsm import UserState

router = Router()


@dataclass(kw_only=True)
class DeploymentData:
    name: str | None

    @staticmethod
    def parse_command(text: str) -> "DeploymentData | None":
        tokens = text.split()

        if len(tokens) not in [1, 2]:
            return None

        if tokens[0] != "/deployments":
            return None

        if len(tokens) == 2:
            return DeploymentData(name=tokens[1])
        else:
            return DeploymentData(name=None)


@router.message(UserState.default, Command("deployments"))
async def command_deployments(message: Message) -> None:
    assert message.text is not None

    deployment_data = DeploymentData.parse_command(message.text)
    if deployment_data is None:
        await message.answer("`/deployments [NAME]`", parse_mode=ParseMode.MARKDOWN_V2)
        return

    if deployment_data.name is not None:
        response = api.v1.kubernetes.metrics.deployments_by_name(deployment_data.name)
    else:
        response = api.v1.kubernetes.metrics.deployments()
    if response is None:
        await message.answer("Internal error.")
        return

    await message.answer(
        f"```json\n{json.dumps(response, indent=2)[:4000]}```",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
