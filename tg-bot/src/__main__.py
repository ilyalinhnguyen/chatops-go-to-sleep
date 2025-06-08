import asyncio
import logging
import os
import sys

import dotenv
from aiogram import Bot, Dispatcher

from . import api
from .routes import router


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    dotenv.load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    if bot_token is None:
        raise RuntimeError()

    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(Bot(token=bot_token))


if __name__ == "__main__":
    print(api.v1.kubernetes.metrics.cluster())

    # asyncio.run(main())
