from core.celery.services import *
from datetime import datetime
import asyncio
from celery import shared_task

#celery -A core.celery.celery_app.celery_app worker --loglevel=info
#celery -A core.celery.celery_app beat --loglevel=info

def check_time(date_var, time_var):
    """Проверка времени"""
    # Ваша дата и время
    # date_var = "2024-10-08"  # Пример: 'ГГГГ-ММ-ДД'
    # time_var = "09:39:00"  # Пример: 'ЧЧ:ММ:СС'

    # Объединяем дату и время в один объект datetime
    datetime_var = datetime.strptime(f"{date_var} {time_var}", "%Y-%m-%d %H:%M:%S")

    # Текущее время
    now = datetime.now()

    # Вычисляем разницу во времени
    time_difference = now - datetime_var

    # Преобразуем разницу в часы
    hours_difference = round(time_difference.total_seconds() / 3600, 2)
    return hours_difference


def parse_value(data):
    if "{" in data:
        tmp = data.strip("{}")
        return tmp.split(',')
    else:
        return str(data)


async def delete_ads(db):
    """Удаление рекламного поста с прошедшим сроком"""
    try:
        ads_posts = db.get_yesterday_ads_post()
        for ads_post in ads_posts:
            post_id = ads_post[0]
            message_id = ads_post[10]
            channel_id = ads_post[8]
            date_var = ads_post[4]
            time_var = ads_post[5]
            variance = check_time(date_var=date_var, time_var=time_var)

            if variance > 24:
                bot = db.get_token_bot(channel_id=channel_id)
                bot_token = bot[1]
                chat_id = bot[4]
                try:
                    db.change_ads_status(post_id=post_id)
                    message_ids = parse_value(message_id)

                    async with Bot(token=bot_token) as second_bot:
                        if type(message_ids) == list:
                            for item in message_ids:
                                await second_bot.delete_message(chat_id=chat_id, message_id=int(item))
                        else:
                            await second_bot.delete_message(chat_id=chat_id, message_id=int(message_ids))

                except Exception as ex:
                    pass
                logger.debug("Рекламный пост удален")
    except Exception as ex:
        logger.error(str(ex))


@shared_task
def send_periodic_message():
    """Отправка сообщения в канал"""
    db = Database(DB_CONFIG)
    db.connect()

    asyncio.run(delete_ads(db=db))

    posts = db.get_posts_to_send()

    db.close()
    if posts:
        # Если посты найдены, вызываем функцию отправки сообщений
        return asyncio.run(send_message_to_channel())
    else:
        return {"status": "Нет постов для публикации"}
    # return asyncio.run(send_message_to_channel())
