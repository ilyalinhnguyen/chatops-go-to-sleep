import logging
from collections.abc import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


def parse_id_list(raw: str | None) -> set[int]:
    if raw is None or raw.strip() == "":
        return set()

    ids: set[int] = set()
    for part in raw.split(","):
        value = part.strip()
        if value == "":
            continue
        ids.add(int(value))
    return ids


class AllowlistMiddleware(BaseMiddleware):
    def __init__(
        self,
        allowed_user_ids: set[int],
        allowed_chat_ids: set[int],
    ) -> None:
        self.allowed_user_ids = allowed_user_ids
        self.allowed_chat_ids = allowed_chat_ids

    def _is_allowed(self, user_id: int | None, chat_id: int | None) -> bool:
        if not self.allowed_user_ids and not self.allowed_chat_ids:
            return True

        if user_id is not None and user_id in self.allowed_user_ids:
            return True
        if chat_id is not None and chat_id in self.allowed_chat_ids:
            return True
        return False

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[object]],
        event: TelegramObject,
        data: dict,
    ) -> object | None:
        user_id: int | None = None
        chat_id: int | None = None

        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            chat_id = event.chat.id if event.chat else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            chat_id = event.message.chat.id if event.message and event.message.chat else None

        if self._is_allowed(user_id, chat_id):
            return await handler(event, data)

        logging.warning("Blocked unauthorized Telegram user", extra={"user_id": user_id, "chat_id": chat_id})

        if isinstance(event, CallbackQuery):
            await event.answer("⛔ Access denied", show_alert=True)
            return None

        if isinstance(event, Message):
            await event.answer("⛔ Access denied")
            return None

        return None
