from celery import Celery
from celery.schedules import crontab
import os
from backend.configurations.database import engine
from backend.models import database_models
import logging
import ssl

logger = logging.getLogger(__name__)
# database_models.Base.metadata.create_all(bind=engine)
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    redis_url = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/1"

celery_app = Celery(
    "tasks",
    broker=redis_url,
    backend=redis_url,
    include=["backend.services.data_sync_service"] # Point to the file where tasks will be defined
)

if redis_url and redis_url.startswith("rediss://"):
    ssl_conf = {
        'ssl_cert_reqs': ssl.CERT_NONE,
        'ssl_ca_certs': None,
        'ssl_keyfile': None,
        'ssl_certfile': None
    }
    celery_app.conf.update(
        broker_use_ssl=ssl_conf,
        redis_backend_use_ssl=ssl_conf
    )

logger.info("Celery worker initialized with Redis broker")

celery_app.conf.update(
    task_track_started=True,
    beat_schedule_filename="tmp/celerybeat-schedule"
)

celery_app.conf.beat_schedule = {
    'periodic-spotify-refresh-every-6h': {
        'task': 'refresh_all_spotify_libraries',
        'schedule': 21600,  # 6 hours (in seconds)
    },
    'periodic-soundcloud-refresh-every-6h': {
        'task': 'refresh_all_soundcloud_libraries',
        'schedule': 21600,  # 6 hours (in seconds)
    },
    'purge-search-cache-daily': {
        'task': 'purge_expired_search_cache',  # <-- use the registered task name
        'schedule': crontab(hour=2, minute=0),  # every day at 2 AM UTC
        'args': (30,),  # expire entries older than 30 days
    },
}

logger.info("Celery beat schedule registered: Spotify refresh + cache purge")
