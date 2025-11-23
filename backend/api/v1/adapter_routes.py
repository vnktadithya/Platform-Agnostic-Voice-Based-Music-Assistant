from fastapi import APIRouter, Query, HTTPException, File, UploadFile, Depends
from backend.adapters.spotify_adapter import SpotifyAdapter
from sqlalchemy.orm import Session
import json
from backend.models.database_models import PlatformAccount
from backend.configurations.database import get_db

router = APIRouter(prefix="/adapter/spotify", tags=["Adapter"])

@router.get("/login")
def spotify_login():
    """Returns the Spotify OAuth URL for user sign-in."""
    try:
        auth_url = SpotifyAdapter.get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate auth URL: {e}")

@router.get("/callback")
def spotify_callback(code: str = Query(...)):
    """Handles the OAuth callback, gets tokens, and returns basic user info."""
    try:
        user_data = SpotifyAdapter.handle_auth_callback(code)
        return user_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling callback: {e}")
    
from fastapi import APIRouter, HTTPException


router = APIRouter()

@router.post("/adapter/youtube_music/headers")
async def upload_youtube_headers(
    headers_file: UploadFile = File(...),
    system_user_id: int = ...,  # Replace with your auth/user identification logic
    db: Session = Depends(get_db)
):
    headers_content = await headers_file.read()
    try:
        headers_json = json.loads(headers_content)
    except Exception:
        headers_text = headers_content.decode('utf-8')
        headers_json = headers_text  # fallback if not actual JSON

    platform_account = db.query(PlatformAccount).filter_by(
        system_user_id=system_user_id,
        platform_name="youtube_music"
    ).first()
    if not platform_account:
        platform_account = PlatformAccount(
            system_user_id=system_user_id,
            platform_name="youtube_music"
        )
        db.add(platform_account)

    # Store in meta_data JSON
    if platform_account.meta_data is None:
        platform_account.meta_data = {}
    platform_account.meta_data["yt_headers"] = headers_json
    db.commit()

    return {"status": "YouTube Music headers uploaded successfully"}
