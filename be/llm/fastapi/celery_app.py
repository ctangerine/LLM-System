import sys
from celery import Celery
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from core.config import settings

# Windows-specific configuration for Celery
if os.name == 'nt':  # Windows
    os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

celery_app = Celery(
    'chatbot_worker',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BROKER_URL,
    include=['celery_worker.task'] 
)

# Windows-specific configuration
celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Windows-specific pool configuration
if os.name == 'nt':
    celery_app.conf.update(
        worker_pool='solo',  # Use solo pool for Windows
        worker_concurrency=1,
        worker_prefetch_multiplier=1,
    )