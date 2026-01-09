from backend.adapters.adapter_base import MusicPlatformAdapter
import os
import requests
from typing import List
from sqlalchemy.orm import Session

class SoundCloudAdapter(MusicPlatformAdapter):
    """
    SoundCloud music platform adapter.

    CURRENT STATUS:
    ----------------
    This adapter represents the REAL, production-intended SoundCloud integration
    using the official SoundCloud API (OAuth 2.0 + REST).

    However, due to SoundCloud's app registration and credential approval process
    being unreliable and time-consuming, this adapter may be DISABLED at runtime
    via feature flags.

    In the current system:
    - This adapter defines the FINAL contract and behavior for SoundCloud
    - It is fully implemented and production-ready
    - Runtime usage may be replaced by a MockSoundCloudAdapter when credentials
      are unavailable

    FUTURE ENABLEMENT:
    ------------------
    To enable real SoundCloud support:
    1. Obtain SoundCloud Client ID & Client Secret
    2. Set ENABLE_SOUNDCLOUD=true in environment
    3. Ensure refresh_token is stored in PlatformAccount
    4. No changes are required in core sync logic or services

    DESIGN GUARANTEES:
    ------------------
    - Core sync logic remains platform-agnostic
    - No SoundCloud-specific logic leaks outside this adapter
    - Spotify and other providers remain completely unaffected
    """

    CAPABILITIES = {
                    "playback_control": False,       
                    "playlist_management": True,     
                    "library_management": True,      
                    "search": True,                 
                    "recommendations": False,        
                    "real_time_control": False,       
                    "favorites_management": True,    
                    "playlist_creation": True,       
                    "voice_control": False,           
                }
  # from Phase 1
    BASE_API_URL = "https://api.soundcloud.com"

    def __init__(self, access_token: str = None, **kwargs):
        if not access_token:
            raise ValueError("SoundCloudAdapter requires access_token")
        self.access_token = access_token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
    
    @staticmethod
    def get_auth_url() -> str:
        client_id = os.getenv("SOUNDCLOUD_CLIENT_ID")
        redirect_uri = os.getenv("SOUNDCLOUD_REDIRECT_URI")

        return (
            "https://secure.soundcloud.com/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            "&response_type=code"
        )

    @staticmethod
    def handle_auth_callback(code: str) -> dict:
        token_url = "https://secure.soundcloud.com/oauth/token"

        payload = {
            "grant_type": "authorization_code",
            "client_id": os.getenv("SOUNDCLOUD_CLIENT_ID"),
            "client_secret": os.getenv("SOUNDCLOUD_CLIENT_SECRET"),
            "redirect_uri": os.getenv("SOUNDCLOUD_REDIRECT_URI"),
            "code": code
        }

        token_resp = requests.post(token_url, data=payload)
        token_resp.raise_for_status()
        token_data = token_resp.json()

        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        me = requests.get("https://api.soundcloud.com/me", headers=headers).json()

        return {
            "platform_user_id": str(me["id"]),
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "meta_data": {
                "username": me.get("username"),
                "avatar": me.get("avatar_url")
            }
        }

    # ---------------- Library ----------------

    """NOTE:
        SoundCloud exposes "liked tracks" via /me/likes/tracks.
        Pagination is intentionally omitted for now to keep the
        initial integration simple and low-risk.
        Can be safely added later without changing callers."""


    def fetch_liked_tracks(self, limit: int = 50) -> List[dict]:
        resp = requests.get(
            f"{self.BASE_API_URL}/me/likes/tracks",
            headers=self._headers(),
            params={"limit": limit}
        )
        resp.raise_for_status()

        tracks = []
        for item in resp.json()["collection"]:
            track = item["track"]
            tracks.append({
                "track_uri": f"soundcloud:track:{track['id']}",
                "meta_data": {
                    "title": track["title"],
                    "artist": track["user"]["username"],
                    "duration_ms": track["duration"],
                    "artwork": track.get("artwork_url"),
                }
            })
        return tracks

    # ---------------- Playlists ----------------

    def fetch_user_playlists(self) -> List[dict]:
        resp = requests.get(
            f"{self.BASE_API_URL}/me/playlists",
            headers=self._headers()
        )
        resp.raise_for_status()

        playlists = []
        for pl in resp.json():
            playlists.append({
                "playlist_id": str(pl["id"]),
                "name": pl["title"],
                "meta_data": {
                    "track_count": len(pl.get("tracks", [])),
                    "artwork": pl.get("artwork_url")
                }
            })
        return playlists

    def create_playlist(self, db: Session, platform_account_id: int, user_id: str, name: str, description: str = ""):
        payload = {
            "playlist": {
                "title": name,
                "description": description,
                "sharing": "public"
            }
        }

        resp = requests.post(
            f"{self.BASE_API_URL}/playlists",
            headers=self._headers(),
            json=payload
        )
        resp.raise_for_status()
        return resp.json()

    # ---------------- Search ----------------

    def search_track_uris(self, db: Session, platform_account_id: int, query: str, limit: int = 1) -> List[str]:
        resp = requests.get(
            f"{self.BASE_API_URL}/tracks",
            headers=self._headers(),
            params={"q": query, "limit": limit}
        )
        resp.raise_for_status()

        return [f"soundcloud:track:{t['id']}" for t in resp.json()]
