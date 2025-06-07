from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("status"))
async def command_status(message: Message) -> None:
    await message.reply("received /status")
