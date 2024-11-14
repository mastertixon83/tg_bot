from celery import Celery
from celery.schedules import crontab

# Настройка подключения к Redis
REDIS_URL = 'redis://localhost:6379/0'

# Инициализация Celery
celery_app = Celery('bot_tasks', broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.timezone = 'UTC'
celery_app.autodiscover_tasks(['core.celery'])

# Настройка использования redbeat для периодических задач
celery_app.conf.beat_scheduler = 'redbeat.RedBeatScheduler'
celery_app.conf.redbeat_redis_url = REDIS_URL

# Настройка периодических задач
celery_app.conf.task_result_expires = 500
celery_app.conf.beat_schedule = {
    'execute_your_function_every_1_minutes': {
        'task': 'core.celery.tasks.send_periodic_message',
        'schedule': crontab(minute='*/1'),
        'args': (),
    },
}
