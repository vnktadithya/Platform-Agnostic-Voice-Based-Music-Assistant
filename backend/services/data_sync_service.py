import os
import requests
import base64
import logging
from backend.services.sync_service import sync_user_library
from backend.services.cache_service import purge_old_cache_entries
from backend.celery_worker import celery_app
from backend.models.database_models import PlatformAccount
from backend.configurations.database import SessionLocal
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def get_new_access_token(refresh_token: str) -> str:
    """Uses a refresh_token to get a new access_token from Spotify."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    auth_str = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    token_url = "https://accounts.spotify.com/api/token"
    
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    headers = {
        "Authorization": f"Basic {auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(token_url, data=payload, headers=headers)
    response.raise_for_status() # Will raise an exception for bad status codes
    logger.info(response.json()["access_token"])
    return response.json()["access_token"]

@celery_app.task(name="sync_spotify_library")
def sync_spotify_library(platform_account_id: int):
    db = SessionLocal()
    try:
        account = db.query(PlatformAccount).filter_by(id=platform_account_id).first()
        if not (account and account.refresh_token):
            logger.error(f"No account or refresh_token found for ID {platform_account_id}. Aborting sync.")
            return
        access_token = get_new_access_token(account.refresh_token)
        sync_user_library(db, platform_account=account, access_token=access_token)
    except Exception as e:
        db.rollback()
        logger.error(f"Sync failed: {e}")
    finally:
        db.close()


@celery_app.task(name="refresh_all_spotify_libraries")
def refresh_all_spotify_libraries():
    """Periodic background task to trigger sync for ALL Spotify users."""
    db = SessionLocal()
    try:
        accounts = db.query(PlatformAccount).all()
        for account in accounts:
            sync_spotify_library.delay(account.id)
        logger.info(f"Triggered background sync for {len(accounts)} Spotify accounts.")
    finally:
        db.close()


@celery_app.task(name="purge_expired_search_cache")
def purge_expired_search_cache(days: int = 30):
    """Celery task to purge old search cache entries."""
    db = SessionLocal()
    try:
        purge_old_cache_entries(db, days=days)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()