from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    default = State()
    scale_bad_format = State()
