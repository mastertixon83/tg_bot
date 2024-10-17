from celery import Celery
from celery.schedules import crontab


# Настройка подключения к Redis
REDIS_URL = 'redis://localhost:6379/0'  # Уберите двоеточие перед паролем

# Инициализация Celery
celery_app = Celery('bot_tasks', broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.timezone = 'UTC'

celery_app.autodiscover_tasks(['core.celery']) # автопоиск задачь в заданных модулях

# Настройка периодических задач
# celery_app.conf.task_result_expires = 3600
celery_app.conf.task_result_expires = 500

celery_app.conf.beat_schedule = {
    'execute_your_function_every_2_minutes': {
        'task': 'core.celery.tasks.send_periodic_message',
        'schedule': crontab(minute='*/1'),  # Запуск каждые 2 минуты
        'args': (),  # Аргументы задачи
    },
}
