from html import escape as html_escape

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from src.i18n import (
    DEFAULT_LANGUAGE,
    PENDING_FIRST_LANGUAGE_KEY,
    SUPPORTED_LANGUAGES,
    get_effective_language,
    get_language,
    set_language,
    tr,
    tr_by_lang,
)
from src.fsm import UserState

router = Router()
HOME_CALLBACK_DATA = "go-home"
LANGUAGE_MENU_CALLBACK_DATA = "language-menu"
SET_LANGUAGE_CALLBACK_PREFIX = "set-language:"
MAIN_MENU_MSG_ID_KEY = "main_menu_message_id"
ACTION_HISTORY_KEY = "action_history"
PENDING_HISTORY_SUMMARY_KEY = "pending_history_summary"
MAX_HISTORY = 50
HISTORY_CALLBACK_DATA = "history"
HISTORY_CLOSE_CALLBACK_DATA = "history-close"
HISTORY_RULE_WIDTH = 30


async def edit_main_menu_stage(
    message: Message,
    state: FSMContext,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    parse_mode: str | None = None,
) -> None:
    """Show the current flow step by editing the welcome/menu anchor message."""
    text = _clip4096(text)
    data = await state.get_data()
    mid: int | None = data.get(MAIN_MENU_MSG_ID_KEY)
    chat_id = message.chat.id
    bot = message.bot
    if mid is None:
        sent = await message.answer(
            text, reply_markup=reply_markup, parse_mode=parse_mode
        )
        await state.update_data(**{MAIN_MENU_MSG_ID_KEY: sent.message_id})
        return
    try:
        await bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=mid,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except TelegramBadRequest as e:
        err = str(e).lower()
        if "message is not modified" in err:
            try:
                await bot.edit_message_reply_markup(
                    chat_id=chat_id, message_id=mid, reply_markup=reply_markup
                )
            except TelegramBadRequest:
                pass
        else:
            sent = await message.answer(
                text, reply_markup=reply_markup, parse_mode=parse_mode
            )
            await state.update_data(**{MAIN_MENU_MSG_ID_KEY: sent.message_id})


async def edit_main_menu_stage_with_go_home(
    message: Message,
    state: FSMContext,
    text: str,
    parse_mode: str | None = None,
) -> None:
    """Validation error on the anchor + single go-home row."""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=await tr(state, "back_home_button"),
                    callback_data=HOME_CALLBACK_DATA,
                )
            ]
        ]
    )
    await edit_main_menu_stage(message, state, text, kb, parse_mode=parse_mode)


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    if await get_language(state) is None:
        await send_language_prompt_only(message, state, is_first_start=True)
        return
    await send_welcome_menu(message, state)


@router.callback_query(
    StateFilter(UserState.default, UserState.awaiting_go_home),
    F.data == LANGUAGE_MENU_CALLBACK_DATA,
)
async def callback_language_menu(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await flush_pending_go_home_if_any(query.message, state)
    await send_language_prompt_only(query.message, state, is_first_start=False)


@router.callback_query(F.data.startswith(SET_LANGUAGE_CALLBACK_PREFIX))
async def callback_set_language(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await flush_pending_go_home_if_any(query.message, state)

    language = query.data.removeprefix(SET_LANGUAGE_CALLBACK_PREFIX)
    if language not in SUPPORTED_LANGUAGES:
        return

    data = await state.get_data()
    is_first_pick = bool(data.get(PENDING_FIRST_LANGUAGE_KEY))

    await set_language(state, language)
    await state.update_data(**{PENDING_FIRST_LANGUAGE_KEY: False})

    if not is_first_pick:
        await query.message.answer(await tr(state, "language_changed"))

    await send_welcome_menu(query.message, state)


def _clip4096(text: str) -> str:
    if len(text) > 4096:
        return text[:4090] + "…"
    return text


def _history_rule(char: str, width: int = HISTORY_RULE_WIDTH) -> str:
    return char * width


async def build_history_entry(
    state: FSMContext,
    command: str | None,
    result: str,
) -> str:
    """One stored history record: labeled command (caps) + labeled result."""
    r = result.strip()
    if len(r) > 3500:
        r = r[:3490] + "…"
    if command and command.strip():
        c = command.strip().upper()
        lc = await tr(state, "history_label_command")
        lr = await tr(state, "history_label_result")
        div = _history_rule("─")
        return f"{lc}\n{c}\n{div}\n{lr}\n{r}"
    return r


async def restore_menu_immediate(message: Message, state: FSMContext) -> None:
    """Cancel / cleanup: restore the welcome/menu anchor to the main menu."""
    language = await get_effective_language(state)
    data = await state.get_data()
    main_menu_id: int | None = data.get(MAIN_MENU_MSG_ID_KEY)
    history: list[str] = list(data.get(ACTION_HISTORY_KEY, []))

    await state.clear()
    await state.set_state(UserState.default)
    await set_language(state, language)
    await state.update_data(
        **{
            MAIN_MENU_MSG_ID_KEY: main_menu_id,
            ACTION_HISTORY_KEY: history,
        }
    )

    menu_welcome = await tr(state, "menu_welcome")
    lang = await get_effective_language(state)
    kb = main_menu_keyboard(lang)
    await edit_main_menu_stage(message, state, menu_welcome, kb, parse_mode=None)


async def finalize_with_result_and_go_home(
    message: Message,
    state: FSMContext,
    notice: str,
    history_line: str | None = None,
    history_command: str | None = None,
    notice_parse_mode: str | None = None,
) -> None:
    """Edit the welcome/menu anchor: result + back prompt + go-home button."""
    text_notice = _clip4096(notice)
    prompt = await tr(state, "back_home_prompt")
    if notice_parse_mode == ParseMode.HTML:
        text_combined = _clip4096(f"{text_notice}\n\n{html_escape(prompt)}")
    else:
        text_combined = _clip4096(f"{text_notice}\n\n{prompt}")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=await tr(state, "back_home_button"),
                    callback_data=HOME_CALLBACK_DATA,
                )
            ]
        ]
    )
    await edit_main_menu_stage(
        message, state, text_combined, kb, parse_mode=notice_parse_mode
    )

    hl = (
        history_line
        if history_line is not None
        else await build_history_entry(state, history_command, notice)
    )
    hl = _clip4096(hl)
    await state.update_data(**{PENDING_HISTORY_SUMMARY_KEY: hl})
    await state.set_state(UserState.awaiting_go_home)


async def flush_pending_go_home_if_any(message: Message, state: FSMContext) -> None:
    """If user starts a new menu action while result+go-home are pending, finish the previous round."""
    cur = await state.get_state()
    if cur is not None and cur.endswith("awaiting_go_home"):
        await on_go_home(message, state)


async def on_go_home(message: Message, state: FSMContext) -> None:
    """After user presses go-home: merge history and restore the welcome/menu anchor."""
    language = await get_effective_language(state)
    data = await state.get_data()
    main_menu_id: int | None = data.get(MAIN_MENU_MSG_ID_KEY)
    pending: str | None = data.get(PENDING_HISTORY_SUMMARY_KEY)
    history: list[str] = list(data.get(ACTION_HISTORY_KEY, []))

    if pending:
        history.append(pending)
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]

    await state.clear()
    await state.set_state(UserState.default)
    await set_language(state, language)
    await state.update_data(
        **{
            MAIN_MENU_MSG_ID_KEY: main_menu_id,
            ACTION_HISTORY_KEY: history,
        }
    )

    menu_welcome = await tr(state, "menu_welcome")
    lang = await get_effective_language(state)
    kb = main_menu_keyboard(lang)
    await edit_main_menu_stage(message, state, menu_welcome, kb, parse_mode=None)


async def return_to_main_menu(
    message: Message,
    state: FSMContext,
    notice: str | None = None,
    history_line: str | None = None,
    history_command: str | None = None,
    notice_parse_mode: str | None = None,
) -> None:
    """With notice: edit anchor to result + go-home. Without notice: restore main menu on anchor (cancel)."""
    if notice is not None:
        await finalize_with_result_and_go_home(
            message,
            state,
            notice,
            history_line,
            history_command,
            notice_parse_mode=notice_parse_mode,
        )
        return
    await restore_menu_immediate(message, state)


@router.callback_query(F.data == HISTORY_CALLBACK_DATA)
async def callback_history(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    await flush_pending_go_home_if_any(query.message, state)
    data = await state.get_data()
    lines = list(data.get(ACTION_HISTORY_KEY, []))
    if not lines:
        text = await tr(state, "history_empty")
    else:
        entries = list(reversed(lines[-20:]))
        outer = _history_rule("━")
        chunks: list[str] = []
        for i, entry in enumerate(entries, start=1):
            heading = await tr(state, "history_record_heading", n=i)
            chunks.append(f"{outer}\n{heading}\n{outer}\n\n{entry}")
        body = "\n\n".join(chunks)
        title = await tr(state, "history_title")
        hint = await tr(state, "history_hint")
        text = f"▸ {title}\n{hint}\n\n{body}"
    text = _clip4096(text)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=await tr(state, "history_close"),
                    callback_data=HISTORY_CLOSE_CALLBACK_DATA,
                )
            ]
        ]
    )
    await query.message.answer(text, reply_markup=kb)


@router.callback_query(F.data == HISTORY_CLOSE_CALLBACK_DATA)
async def callback_history_close(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.message is None:
        return
    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇷🇺 Русский",
                    callback_data=f"{SET_LANGUAGE_CALLBACK_PREFIX}ru",
                ),
                InlineKeyboardButton(
                    text="🇬🇧 English",
                    callback_data=f"{SET_LANGUAGE_CALLBACK_PREFIX}en",
                ),
            ]
        ]
    )


async def send_language_prompt_only(
    message: Message, state: FSMContext, is_first_start: bool
) -> None:
    await state.update_data(**{PENDING_FIRST_LANGUAGE_KEY: is_first_start})
    await state.set_state(UserState.awaiting_language_selection)
    await message.answer(
        tr_by_lang(DEFAULT_LANGUAGE, "choose_language"),
        reply_markup=language_keyboard(),
    )


def main_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=tr_by_lang(language, "menu_deployments"),
                callback_data="deployments",
            )
        ],
        [InlineKeyboardButton(text=tr_by_lang(language, "menu_pods"), callback_data="pods")],
        [
            InlineKeyboardButton(
                text=tr_by_lang(language, "menu_restart"),
                callback_data="restart",
            )
        ],
        [
            InlineKeyboardButton(
                text=tr_by_lang(language, "menu_rollback"),
                callback_data="rollback",
            )
        ],
        [InlineKeyboardButton(text=tr_by_lang(language, "menu_scale"), callback_data="scale")],
        [InlineKeyboardButton(text=tr_by_lang(language, "menu_status"), callback_data="status")],
        [
            InlineKeyboardButton(
                text=tr_by_lang(language, "menu_history"),
                callback_data=HISTORY_CALLBACK_DATA,
            )
        ],
        [
            InlineKeyboardButton(
                text=tr_by_lang(language, "menu_language"),
                callback_data=LANGUAGE_MENU_CALLBACK_DATA,
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def send_welcome_menu(message: Message, state: FSMContext) -> None:
    language = await get_effective_language(state)
    await set_language(state, language)
    data = await state.get_data()
    existing_history = list(data.get(ACTION_HISTORY_KEY, []))
    await message.answer(tr_by_lang(language, "welcome_fun_line"))
    sent_menu = await message.answer(
        await tr(state, "menu_welcome"),
        reply_markup=main_menu_keyboard(language),
    )
    await state.update_data(
        **{
            MAIN_MENU_MSG_ID_KEY: sent_menu.message_id,
            ACTION_HISTORY_KEY: existing_history,
        }
    )
    await state.set_state(UserState.default)
