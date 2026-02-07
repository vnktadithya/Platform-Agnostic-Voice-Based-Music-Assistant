from celery import Celery
from celery.schedules import crontab
import os
from backend.configurations.database import engine
from backend.models import database_models
import logging

logger = logging.getLogger(__name__)
# database_models.Base.metadata.create_all(bind=engine)
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    redis_url = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/1"

# Fix for Upstash/Rediss: Ensure ssl_cert_reqs is set in the URL
if redis_url.startswith("rediss://") and "ssl_cert_reqs" not in redis_url:
    if "?" in redis_url:
        redis_url += "&ssl_cert_reqs=CERT_NONE"
    else:
        redis_url += "?ssl_cert_reqs=CERT_NONE"

celery_app = Celery(
    "tasks",
    broker=redis_url,
    backend=redis_url,
    include=["backend.services.data_sync_service"] # Point to the file where tasks will be defined
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
