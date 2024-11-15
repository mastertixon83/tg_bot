from aiogram.utils.media_group import MediaGroupBuilder
from aiogram import Bot
from aiogram.types import FSInputFile
from datetime import datetime
from loguru import logger
from ..database import Database
from config import DB_CONFIG, MEDIA
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def send_photo_with_caption(bot: Bot, chat_id: int, photo_path: str, has_spoiler: bool, caption: str, builder: InlineKeyboardBuilder = None):
    """Отправка изображения с подписью"""
    logger.debug("Зашли")
    try:
        if builder is not None:
            reply_markup = builder.as_markup() if builder else None
            return await bot.send_photo(
                chat_id=chat_id,
                photo=open(photo_path, "rb"),
                # photo=FSInputFile(photo_path),
                caption=caption,
                has_spoiler=has_spoiler,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        else:
            logger.debug(chat_id)
            logger.debug(caption)
            return await bot.send_photo(
                chat_id=chat_id,
                photo=FSInputFile(photo_path),
                caption=caption,
                parse_mode='HTML'
            )
    except Exception as ex:
        logger.error(f"Не прошло сенд фото - {ex}")


async def send_message_to_channel():
    """Отправка сообщения в канал"""
    db = Database(DB_CONFIG)
    db.connect()
    try:
        posts = db.get_posts_to_send()
        if not posts:
            logger.info("Нет постов для отправки")
            return {"Status": "Нет постов для отправки"}
        for post_info in posts:
            post_id = post_info[0]
            created_at = post_info[1]
            updated_at = post_info[2]
            text = post_info[3]
            data_publication = post_info[4]
            time_publication = post_info[5]
            status = post_info[6]
            type_post = post_info[7]
            channel_id = post_info[14]
            article = post_info[9]
            # Проверяем наличие кнопок-ссылок под постом
            buttons = db.get_buttons_links(post_id=post_id)
            if buttons:
                builder = InlineKeyboardBuilder()
                for item in buttons:
                    builder.row(
                        InlineKeyboardButton(
                            text=item[1],
                            url=item[2]
                        )
                    )
            else:
                builder = None

            media = db.get_media(post_id=post_id)

            bot_data = db.get_token_bot(channel_id=channel_id)

            if len(media) > 1:
                media_group = MediaGroupBuilder(caption=text)

                for item in media:
                    filename = MEDIA + item[1]
                    media_group.add(
                        type="photo",
                        media=FSInputFile(filename),
                        parse_mode="HTML"
                    )

                async with Bot(token=bot_data[1]) as second_bot:
                    send_message = await second_bot.send_media_group(
                        chat_id=bot_data[3],
                        media=media_group.build()
                    )
                message_id = [msg.message_id for msg in send_message]
            elif len(media) == 1:

                async with Bot(token=bot_data[1]) as second_bot:
                    if builder:
                        send_message = await send_photo_with_caption(
                            bot=second_bot,
                            chat_id=bot_data[3],
                            photo_path=MEDIA + media[0][1],
                            caption=text,
                            has_spoiler=media[0][4],
                            builder=builder
                        )
                    else:
                        send_message = await send_photo_with_caption(
                            bot=second_bot,
                            chat_id=bot_data[3],
                            photo_path=MEDIA + media[0][1],
                            has_spoiler=media[0][4],
                            caption=text
                        )

                message_id = send_message.message_id
            elif len(media) == 0:
                async with Bot(token=bot_data[1]) as second_bot:
                    if builder is not None:
                        send_message = await second_bot.send_message(
                            chat_id=bot_data[3],
                            text=text,
                            parse_mode="HTML",
                            disable_web_page_preview=True,
                            reply_markup=builder.as_markup()
                        )
                    else:
                        send_message = await second_bot.send_message(
                            chat_id=bot_data[3],
                            text=text,
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )

                    message_id = send_message.message_id
            db.mark_post_as_sent(post_id=post_id, message_id=message_id)
    except Exception as ex:
        return {"Error": str(ex)}
    finally:
        db.close()
    return {"Status": "Посты опубликованы"}


