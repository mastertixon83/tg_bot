from aiogram.fsm.state import StatesGroup, State


class AddBot(StatesGroup):
    set_token = State()
    check_bot = State()
    add_post = State()
    add_btn_link = State()
    enter_button_data = State()
