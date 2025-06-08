from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    default = State()
    scale_prompted_service = State()
    scale_prompted_n = State()
    scale_confirm = State()
    rollback_prompted_version = State()
    rollback_confirm = State()
    update_confirm = State()
    restart_prompted = State()
    restart_prompted_name = State()
    status_prompted = State()
