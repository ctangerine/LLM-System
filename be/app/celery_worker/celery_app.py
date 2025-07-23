from celery import Celery
from app.core.config import settings

celery_app = Celery(
    'chatbot_worker',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BROKER_URL,
    include=['app.celery_worker.task'] 
)

celery_app.conf.update(task_track_started=True)