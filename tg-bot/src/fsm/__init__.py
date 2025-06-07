from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    default = State()
    scale_prompt_service = State()
    scale_prompt_n = State()
    scale_done = State()
    rollback_prompted_version = State()
    rollback_confirm = State()
    scale_bad_format = State()
