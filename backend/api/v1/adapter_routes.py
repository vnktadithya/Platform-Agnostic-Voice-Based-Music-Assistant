from fastapi import APIRouter, Query, HTTPException, Depends
from backend.adapters.spotify_adapter import SpotifyAdapter
from backend.adapters.soundcloud_adapter import SoundCloudAdapter
from backend.models.database_models import PlatformAccount, SystemUser
from backend.services.data_sync_service import sync_spotify_library
from backend.configurations.database import get_db
from backend.utils.feature_flags import is_soundcloud_enabled
from sqlalchemy.orm import Session


router = APIRouter(tags=["Adapter"])

#------------------------------------------------- SPOTIFY -------------------------------------------------------

@router.get("/adapter/spotify/login")
def spotify_login():
    """Returns the Spotify OAuth URL for user sign-in."""
    try:
        auth_url = SpotifyAdapter.get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate auth URL: {e}")

@router.get("/adapter/spotify/callback")
def spotify_callback(code: str = Query(...), db: Session = Depends(get_db)):
    data = SpotifyAdapter.handle_auth_callback(code)

    user_data = data["user"]
    tokens = data["tokens"]

    platform_user_id = user_data["id"]
    email = user_data.get("email")
    display_name = user_data.get("name")

    # 1️⃣ Create / fetch SystemUser
    system_user = None
    if email:
        system_user = db.query(SystemUser).filter_by(email=email).first()

    if not system_user:
        system_user = SystemUser()
        db.add(system_user)
        db.flush()

    # 2️⃣ Create / update PlatformAccount
    account = (
        db.query(PlatformAccount)
        .filter_by(
            platform_name="spotify",
            platform_user_id=platform_user_id
        )
        .first()
    )

    meta = {
        "access_token": tokens["access_token"],
        "expires_at": tokens["expires_at"],
        "scope": tokens.get("scope"),
        "token_type": tokens.get("token_type"),
        "display_name": display_name,
        "email": email
    }

    if not account:
        account = PlatformAccount(
            system_user_id=system_user.id,
            platform_name="spotify",
            platform_user_id=platform_user_id,
            refresh_token=tokens["refresh_token"],
            meta_data=meta
        )
        db.add(account)
    else:
        account.refresh_token = tokens["refresh_token"] or account.refresh_token
        account.meta_data = meta

    db.commit()
    db.refresh(account)

    # 3️⃣ Trigger background sync immediately
    sync_spotify_library.delay(account.id)

    return {
        "status": "success",
        "platform_account_id": account.id,
        "message": "Spotify connected successfully. Sync started."
    }

    
#------------------------------------------------- SOUNDCLOUD ----------------------------------------------------

@router.get("/adapter/soundcloud/login")
def soundcloud_login():
    if not is_soundcloud_enabled():
        raise HTTPException(
            status_code=503,
            detail="SoundCloud integration implemented but awaiting API credentials"
        )
    return {"auth_url": SoundCloudAdapter.get_auth_url()}

@router.get("/adapter/soundcloud/callback")
def soundcloud_callback(
    code: str = Query(...),
    db: Session = Depends(get_db)
):
    data = SoundCloudAdapter.handle_auth_callback(code)

    account = PlatformAccount(
        platform_name="soundcloud",
        platform_user_id=data["platform_user_id"],
        refresh_token=data.get("refresh_token"),
        meta_data={
            "access_token": data["access_token"],
            **data["meta_data"]
        }
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return {"status": "connected", "account_id": account.id}
