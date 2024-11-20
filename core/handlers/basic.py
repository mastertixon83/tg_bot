from aiogram import Bot, F, Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile, ChatMemberAdministrator, ChatMemberOwner
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder
from loguru import logger
from datetime import datetime
import requests

from core.utils.states import AddBot  # Убедитесь, что ваш импорт состояния корректен
from core.keyboards.default import mainMenu
from core.keyboards.inline import btn_done, btn_add_btn_link  # Убедитесь, что btn_done правильно импортирован
from core.database.database import Database
from config import MEDIA

from core.celery.tasks import send_periodic_message
from core.celery.services import send_message_to_channel

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    await state.clear()
    text = f"Привет {message.from_user.first_name}, рад приветсвовать тебя!!!"
    await message.answer(text=text, reply_markup=mainMenu)


# @router.message(StateFilter(None))
# async def test_select(message: Message):
#     logger.debug(message.html_text)


@router.message(StateFilter(None), F.text == "Найти фото")
async def test_select(message: Message, state: FSMContext, db: Database):
    # second_bot = Bot(token="7428797811:AAF0zPdkhpBADfbBmlNq-JOxb2blQE5KPcg")
    # await send_message_to_channel()

@router.message(StateFilter(None), F.text == "Ссылка на сайт")
async def test_select(message: Message, state: FSMContext, db: Database):
    await message.answer("Супер сайт: http://93.183.105.111/")


@router.message(StateFilter(None), F.text == "Добавить пост в БД")
async def save_ads_start(message: Message, state: FSMContext, db: Database):
    """Начало добавления поста в БД"""
    await message.answer(text="Отправь мне текст рекламного поста и я сохраню его в БД", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddBot.add_post)


@router.message(AddBot.add_post, F.text)
async def save_post_text(message: Message, state: FSMContext, db: Database) -> None:
    """Добавление кнопки-ссылки к посту"""
    post = db.save_ads_to_db(html_text=message.html_text)

    await state.update_data(post_id=post[0])

    await message.answer("Отлично! Текст сохранен, добавить кнопку-ссылку под пост?", reply_markup=btn_add_btn_link)
    await state.set_state(AddBot.add_btn_link)


@router.callback_query(StateFilter(AddBot.add_btn_link), F.data == "add_btn_link")
async def add_btn_link(callback_query: CallbackQuery, state: FSMContext):
    """Обрабатываем нажатие на кнопку 'Добавить'"""
    await callback_query.message.delete()
    await callback_query.message.answer("Отправь мне текст кнопки и ссылку для неё. Пример: Текст - https://google.com")

    # Переходим в состояние добавления кнопки
    await state.set_state(AddBot.enter_button_data)

    # Не забываем подтвердить callback
    await callback_query.answer()


@router.message(AddBot.enter_button_data, F.text)
async def save_btn_link(message: Message, state: FSMContext, db: Database) -> None:
    """Сохранение кнопки-ссылки к посту"""
    try:
        # Ожидаем данные в формате: "текст | ссылка"
        button_text, button_link = map(str.strip, message.text.split('-'))

        # Получаем ID поста из состояния
        data = await state.get_data()
        post_id = data.get('post_id')

        # Сохраняем кнопку в БД
        db.add_btn_link_to_post(post_id, button_text, button_link)

        # Подтверждаем добавление кнопки
        await message.answer("Кнопка-ссылка успешно добавлена!", reply_markup=btn_add_btn_link)
        await state.set_state(AddBot.add_btn_link)
    except ValueError:
        await message.answer("Неправильный формат! Пожалуйста, отправьте текст и ссылку в формате: текст - ссылка.")
        return


@router.callback_query(StateFilter(AddBot.add_btn_link), F.data == "save_post")
async def save_add_btn(callback_query: CallbackQuery, state: FSMContext):
    """Обрабатываем нажатие на кнопку 'Сохранить'"""
    await callback_query.message.delete()
    await callback_query.message.answer("Пост сохранён!", reply_markup=mainMenu)

    # Завершаем FSM
    await state.clear()

    # Не забываем подтвердить callback
    await callback_query.answer()


@router.message(StateFilter(None), F.text == "Создать бота")
async def handle_create_bot(message: Message, state: FSMContext):
    """Обработка нажатия кнопки 'Создать бота'"""
    text = """1. Перейди в @BotFather, 
2. выбери команду /newbot
3. после чего отправьте мне токен
    """
    send_message = await message.answer(text=text, reply_markup=ReplyKeyboardRemove())
    await state.update_data(message_id=send_message.message_id)
    await state.set_state(AddBot.set_token)


@router.message(AddBot.set_token, F.text)
async def handle_set_token(message: Message, state: FSMContext) -> None:
    """Обработка отправки токена бота"""
    # data = await state.get_data()
    # message_id = data.get("message_id")
    # await message.chat.delete_message(message_id)

    text = """Теперь добавьте вашего бота в администраторы канала, после отправьте сообщение в канал и нажмите на кнопку Проверить бота"""
    send_message = await message.answer(text=text, reply_markup=btn_done)
    await state.update_data(token=message.text.strip())
    await state.update_data(message_id=send_message.message_id)
    await state.update_data(main_bot_chat_id=send_message.chat.id)
    await state.set_state(AddBot.check_bot)


@router.callback_query(F.data == 'check_bot', StateFilter(AddBot.check_bot))
async def handle_check_bot(callback_query: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Обработка нажатия кнопки 'Проверить бота'"""
    user_id = callback_query.from_user.id

    await callback_query.answer()  # Отключаем уведомление о нажатии кнопки
    data = await state.get_data()

    second_bot = Bot(token=data.get("token"))
    url = f"https://api.telegram.org/bot{data.get('token')}/getme"
    bot_info = requests.get(url)

    data_resp = bot_info.json()
    if bot_info.status_code == 200 and data_resp['ok']:
        bot_info = data_resp['result']
        username = bot_info['username']

    url = f"https://api.telegram.org/bot{data.get('token')}/getUpdates"
    updates_resp = requests.get(url)
    if updates_resp.status_code == 200:
        updates = updates_resp.json()

        update = updates['result']
        try:
            channel_post = update[0].get("channel_post")
        except Exception as ex:
            await callback_query.message.delete()
            await callback_query.message.answer("Что-то пошло не так повторите попытку", reply_markup=mainMenu)
            await state.clear()
            return

        # Проверяем, есть ли сообщение в канале
        if channel_post:
            channel_post = update[0]['channel_post']
            chat_id = channel_post['chat']['id']
            channel_title = channel_post['chat']['title']
            # await second_bot.send_message(chat_id=chat_id, text="message")

            try:
                member = await second_bot.get_chat_member(chat_id=chat_id, user_id=(await second_bot.me()).id)
            except Exception as ex:
                logger.error(ex)

            # Проверяем статус
            if isinstance(member, (ChatMemberAdministrator)):
                try:
                    e = db.add_bot(
                        token=data.get("token"),
                        name=username,
                        chat_id=chat_id,
                        channel_title=channel_title
                    )
                    await callback_query.message.delete()
                    await state.clear()
                    if not e:
                        await callback_query.message.answer("Отлично! Бот успешно добавлен", reply_markup=mainMenu)
                    else:
                        raise Exception(f"Бот {data.get('token')} уже присутствует в базе")
                except Exception as ex:
                    await state.clear()
                    await callback_query.message.answer(f"Ошибка добавления бота - {str(ex)}", reply_markup=mainMenu)
                    return
            else:
                await state.clear()
                await callback_query.message.answer(f"Ошибка добавления бота - {str(ex)}", reply_markup=mainMenu)
                return

    else:
        await callback_query.message.delete()
        await callback_query.message.answer("Что-то пошло не так повторите попытку", reply_markup=mainMenu)
        await state.clear()