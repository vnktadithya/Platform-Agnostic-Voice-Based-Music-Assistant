from fastapi import APIRouter, Query, HTTPException
from backend.adapters.spotify_adapter import SpotifyAdapter

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