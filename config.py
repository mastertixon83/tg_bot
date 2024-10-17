import os
from dotenv import load_dotenv

load_dotenv()

MAIN_BOT_TOKEN = str(os.getenv("MAIN_BOT_TOKEN"))
ADMINS = [
    str(os.getenv("ADMIN_ID")),
]

DB_CONFIG = {
            'dbname': 'telega_db',
            'user': 'root',
            'password': 'root',
            'host': 'localhost',  # или IP-адрес вашего сервера
            'port': '5432',  # По умолчанию для PostgreSQL
}

MEDIA = "/mnt/96375fe5-6a39-4e72-b221-433152ae3028/u4eba/Python/bots/telega/telega_main/telegram/media/"
