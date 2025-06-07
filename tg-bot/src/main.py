import asyncio

from aiogram import Bot, Dispatcher

dp = Dispatcher()


async def main() -> None:
    TOKEN = "..."
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)
    print("Hello from tg-bot!")


if __name__ == "__main__":
    asyncio.run(main())
