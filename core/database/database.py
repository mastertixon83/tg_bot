import psycopg2
from datetime import datetime, timedelta
from psycopg2 import sql
from loguru import logger
import pytz


class Database:
    def __init__(self, config):
        self.connection = None
        self.config = config

    def connect(self):
        """Создание подключения к базе данных"""
        try:
            self.connection = psycopg2.connect(**self.config)
            logger.info("Успешное подключение к базе данных")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")

    def close(self):
        """Закрытие подключения к базе данных"""
        if self.connection:
            self.connection.close()
            logger.info("Подключение к базе данных закрыто")

    def test_query(self, id):
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql.SQL("SELECT message_id FROM public.main_post WHERE id = %s"), [id])
            posts = cursor.fetchone()
            return posts
        except Exception as ex:
            pass
        finally:
            cursor.close()

    def add_bot(self, token, name, chat_id, channel_title):
        """Добавление нового бота в базу данных"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql.SQL("SELECT id FROM public.main_channel WHERE title = %s"), [channel_title])
            channel_id = cursor.fetchone()

            if channel_id is None:
                logger.error("Канал с таким названием не найден.")
                return

            # Извлекаем id канала из результата
            id_channel = channel_id[0]

            query = sql.SQL("INSERT INTO public.main_bottoken (token, name, channel_id, chat_id) VALUES (%s, %s, %s, %s)")
            cursor.execute(query, (token, name, id_channel, chat_id))
            self.connection.commit()  # Подтверждаем транзакцию

        except Exception as e:
            logger.error(f"Ошибка при добавлении бота в базу данных: {e}")
            return e
        finally:
            cursor.close()

    def get_yesterday_ads_post(self):
        """Возращает вчерашние рекламные объявления"""
        now = datetime.now()
        yesterday = now.date() - timedelta(days=1)  # Вчерашняя дата

        cursor = self.connection.cursor()
        query = """
                    SELECT * 
                    FROM public.main_post 
                    WHERE status = true
                      AND ads_status = true
                      AND post_type = 'A'   
                      AND post_data = %s;
                """
        # Параметры передаются как кортеж
        params = (yesterday.strftime("%Y-%m-%d"),)
        cursor.execute(query, params)

        # Получаем все посты
        posts = cursor.fetchall()
        cursor.close()
        return posts

    def get_posts_to_send(self):
        """Выбирает посты которые нужно опубликовать"""
        tz = pytz.timezone('Asia/Yekaterinburg')
        now = datetime.now(tz)
        current_date = now.date()  # Текущая дата
        current_time = now.time()  # Текущее время

        cursor = self.connection.cursor()
        query = """
            SELECT * 
            FROM public.main_post 
            WHERE status = false 
              AND post_data = %s 
              AND post_time <= %s;
        """
        # Параметры передаются как кортеж
        params = (current_date.strftime("%Y-%m-%d"), current_time.strftime("%H:%M:%S"))
        cursor.execute(query, params)

        # Получаем все посты
        posts = cursor.fetchall()
        cursor.close()
        return posts

    def get_buttons_links(self, post_id):
        """Возвращает кнопки-ссылки"""
        cursor = self.connection.cursor()
        query = """
                   SELECT * 
                   FROM public.main_button
                   WHERE post_id = %s
               """
        cursor.execute(query, (post_id,))
        buttons = cursor.fetchall()
        cursor.close()
        return buttons

    def get_media(self, post_id):
        """Возвращает медиа файлы к посту"""
        cursor = self.connection.cursor()
        query = """
            SELECT * 
            FROM public.main_media
            WHERE post_id = %s
        """
        cursor.execute(query, (post_id,))
        media = cursor.fetchall()
        cursor.close()
        return media

    def change_ads_status(self, post_id):
        """Изменения статуса рекламного объявления"""
        cursor = self.connection.cursor()
        now = datetime.now()

        date_time_publication = now.replace(microsecond=0)

        query = """
                                UPDATE public.main_post 
                                SET ads_status = false
                                WHERE id = %s;
                            """

        cursor.execute(query, (post_id,))
        self.connection.commit()  # Не забудьте зафиксировать изменения
        cursor.close()

    def mark_post_as_sent(self, post_id, message_id):
        """Обновляет статус поста на опубликован"""
        # Обновляем статус поста в базе данных как отправленный
        try:
            cursor = self.connection.cursor()
            now = datetime.now()

            date_time_publication = now.replace(microsecond=0)

            query = """
                        UPDATE public.main_post 
                        SET status = true, message_id = %s, date_time_publication = %s
                        WHERE id = %s;
                    """

            cursor.execute(query, (message_id, str(date_time_publication), post_id,))
            self.connection.commit()  # Не забудьте зафиксировать изменения
            cursor.close()
        except Exception as ex:
            logger.error(f"[DATABASE] - {str(ex)}")
        finally:
            cursor.close()

    def get_token_bot(self, channel_id):
        """Вернуть бота по id канала"""
        cursor = self.connection.cursor()
        cursor.execute(sql.SQL("SELECT * FROM public.main_bottoken WHERE channel_id = %s"), [channel_id])
        bot_data = cursor.fetchone()
        cursor.close()
        return bot_data

    def save_ads_to_db(self, html_text):
        """Конвертирует и сохраняет рекламный пост в БД"""
        cursor = self.connection.cursor()
        query = sql.SQL("INSERT INTO public.main_post (post_type, text, created_at, updated_at, status, ads_status) VALUES (%s, %s, NOW(), NOW(), false, true) RETURNING id, post_type, text, created_at, updated_at, status, ads_status")
        cursor.execute(query, ("A", html_text))

        post = cursor.fetchone()

        self.connection.commit()
        cursor.close()
        return post

    def add_btn_link_to_post(self, post_id, button_text, button_link):
        """Добавление кнопки-ссылки к посту"""
        cursor = self.connection.cursor()
        query = sql.SQL(
            "INSERT INTO public.main_button (post_id, text, link) VALUES (%s, %s, %s)")
        cursor.execute(query, (post_id, button_text, button_link))
        self.connection.commit()
        cursor.close()
