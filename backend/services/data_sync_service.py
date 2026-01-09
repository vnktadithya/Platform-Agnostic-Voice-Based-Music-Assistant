import os
import requests
import base64
import logging
from backend.adapters.spotify_adapter import SpotifyAdapter
from backend.adapters.adapter_factory import get_soundcloud_adapter
from backend.utils.feature_flags import is_soundcloud_enabled
from backend.services.library_sync_service import sync_user_library
from backend.services.cache_service import purge_old_cache_entries
from backend.celery_worker import celery_app
from backend.models.database_models import PlatformAccount
from backend.configurations.database import SessionLocal
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone


load_dotenv()
logger = logging.getLogger(__name__)

# --------------------------------------------------- SPOTIFY ---------------------------------------------------

def refresh_spotify_access_token(refresh_token: str) -> str:
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
    data = response.json()
    return {
        "access_token": data["access_token"],
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])).isoformat(),
        "scope": data.get("scope"),
        "token_type": data.get("token_type")
    }


def get_valid_spotify_access_token(db, account: PlatformAccount) -> str:
    logger.debug("get_valid_spotify_access_token START")
    logger.debug("Account ID: %s", account.id)
    logger.debug("Refresh token present: %s", bool(account.refresh_token))
    logger.debug("Meta data raw: %s", account.meta_data)

    meta = account.meta_data or {}
    access_token = meta.get("access_token")
    expires_at = meta.get("expires_at")

    # If token exists and is still valid → reuse
    if access_token and expires_at:
        try:
            expires_dt = datetime.fromisoformat(expires_at)

            # ✅ CRITICAL: normalize legacy naive datetimes to UTC
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) < expires_dt:
                logger.debug("Reusing valid Spotify token for platform_account_id=%s (…%s)", account.id, access_token[-6:])
                return access_token

        except Exception as e:
            logger.warning("Invalid expires_at for platform_account_id=%s: %s", account.id, e)

    # 2️⃣ Refresh token
    logger.info("Spotify token expired or missing for platform_account_id=%s. Refreshing…", account.id)

    # Otherwise refresh
    try:
        token_data = refresh_spotify_access_token(account.refresh_token)
    except Exception as e:
        logger.error(
            "Spotify token refresh failed for platform_account_id=%s: %s", account.id, e)
        
        # 🚨 IMPORTANT: Explicit failure (frontend will redirect to login later)
        raise ValueError("Spotify authentication expired. Re-login required.")

    account.meta_data = {
        **meta,
        "access_token": token_data["access_token"],
        "expires_at": token_data["expires_at"],
        "scope": token_data.get("scope"),
        "token_type": token_data.get("token_type", "Bearer")
    }

    db.commit()
    logger.info("Returning refreshed Spotify access token for platform_account_id=%s", account.id)
    return token_data["access_token"]


@celery_app.task(name="sync_spotify_library")
def sync_spotify_library(platform_account_id: int):
    db = SessionLocal()
    try:
        account = db.query(PlatformAccount).filter_by(id=platform_account_id).first()
        if not (account and account.refresh_token):
            logger.error(f"No account or refresh_token found for ID {platform_account_id}. Aborting sync.")
            return
        access_token = get_valid_spotify_access_token(db, account)
        spotify_adapter = SpotifyAdapter(access_token=access_token)
        sync_user_library(db, platform_account=account, adapter=spotify_adapter)
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


# ------------------------------------------------ SOUNDCLOUD ------------------------------------------------

def refresh_soundcloud_access_token(refresh_token: str) -> str:

    """NOTE:
        This function is only used when real SoundCloud integration
        is enabled via feature flag and valid credentials exist."""

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": os.getenv("SOUNDCLOUD_CLIENT_ID"),
        "client_secret": os.getenv("SOUNDCLOUD_CLIENT_SECRET"),
    }

    resp = requests.post("https://secure.soundcloud.com/oauth/token", data=payload)
    resp.raise_for_status()
    return resp.json()["access_token"]

@celery_app.task(name="sync_soundcloud_library")
def sync_soundcloud_library(platform_account_id: int):
    """
    Background task to sync a user's SoundCloud library.

    ARCHITECTURAL GUARANTEES:
    ------------------------
    - Core sync logic is platform-agnostic
    - Runtime adapter selection is centralized
    - SoundCloud can be enabled/disabled without refactoring
    - Mock adapter is used intentionally when real API access is unavailable

    This task MUST NOT contain SoundCloud-specific branching logic.
    """

    db = SessionLocal()
    try:
        # ---------------------------------------------------------
        # Step 1: Load platform account
        # ---------------------------------------------------------
        account = (
            db.query(PlatformAccount)
            .filter_by(id=platform_account_id)
            .first()
        )

        if not account:
            # Account might have been deleted or is invalid
            return

        # ---------------------------------------------------------
        # Step 2: Resolve access token (only if real SoundCloud enabled)
        # ---------------------------------------------------------
        access_token = None

        if is_soundcloud_enabled():
            # Real SoundCloud mode
            # refresh_token MUST exist in this mode
            if not account.refresh_token:
                # Misconfiguration: SoundCloud enabled but no refresh token
                logger.warning(f"SoundCloud enabled but no refresh_token for account {platform_account_id}")
                return

            access_token = refresh_soundcloud_access_token(
                account.refresh_token
            )

        # ---------------------------------------------------------
        # Step 3: Adapter instantiation 
        # ---------------------------------------------------------
        adapter = get_soundcloud_adapter(access_token=access_token)

        # ---------------------------------------------------------
        # Step 4: Platform-agnostic sync
        # ---------------------------------------------------------
        sync_user_library(
            db,
            platform_account=account,
            adapter=adapter
        )

    except Exception as e:
        # Any exception here should NEVER break the worker
        db.rollback()
        logger.error(f"SoundCloud sync failed: {e}")

    finally:
        db.close()



# ---------------------------- DELETE OLD ENTRIES ------------------------------

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