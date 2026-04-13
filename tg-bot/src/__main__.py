import asyncio
import logging
import os
import sys

import dotenv
from aiogram import Bot, Dispatcher

from .access import AllowlistMiddleware, parse_id_list
from .routes import router


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    dotenv.load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    if bot_token is None:
        raise RuntimeError("BOT_TOKEN is not set")

    allowed_user_ids = parse_id_list(os.getenv("TG_ALLOWED_USER_IDS"))
    allowed_chat_ids = parse_id_list(os.getenv("TG_ALLOWED_CHAT_IDS"))

    dp = Dispatcher()
    allowlist_middleware = AllowlistMiddleware(
        allowed_user_ids=allowed_user_ids,
        allowed_chat_ids=allowed_chat_ids,
    )
    dp.message.middleware(allowlist_middleware)
    dp.callback_query.middleware(allowlist_middleware)
    dp.include_router(router)

    await dp.start_polling(Bot(token=bot_token))


if __name__ == "__main__":
    asyncio.run(main())
