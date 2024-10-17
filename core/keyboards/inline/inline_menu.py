from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

btn_done = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Проверить бота", callback_data="check_bot"),
        ]
    ]
)

btn_add_btn_link = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Добавить кнопку-ссылку", callback_data="add_btn_link"),
            InlineKeyboardButton(text="Сохранить", callback_data="save_post")
        ]
    ]
)