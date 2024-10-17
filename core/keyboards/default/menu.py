from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

mainMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Создать бота"),
            KeyboardButton(text="Найти фото"),
        ],
        [
            KeyboardButton(text="Добавить пост в БД")
        ]
    ],
    resize_keyboard=True
)