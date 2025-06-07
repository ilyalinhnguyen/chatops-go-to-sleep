import asyncio
import logging
import os
import sys

import dotenv
from aiogram import Bot, Dispatcher

dp = Dispatcher()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    dotenv.load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    if bot_token is None:
        raise RuntimeError()

    bot = Bot(token=bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
