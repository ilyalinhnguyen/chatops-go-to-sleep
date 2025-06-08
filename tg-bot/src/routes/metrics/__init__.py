# from dataclasses import dataclass

from aiogram import (
    # F,
    Router,
)

# from aiogram.enums import ParseMode
# from aiogram.filters import Command
# from aiogram.types import Message
# from aiogram.types.callback_query import CallbackQuery
# from src import api
# from src.fsm import UserState

router = Router()


# @router.message(UserState.default, Command("restart"))
# async def command_restart(message: Message) -> None:
#     assert message.text is not None

#     response = api.v1.prometheus.metrics.basic()
#     if response is None:
#         await message.answer("Internal error.")
#         return

#     await message.answer(str(response["data"]))
