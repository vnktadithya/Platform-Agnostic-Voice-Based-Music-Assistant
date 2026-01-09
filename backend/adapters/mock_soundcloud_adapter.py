from typing import List
from sqlalchemy.orm import Session
from backend.adapters.adapter_base import MusicPlatformAdapter

class MockSoundCloudAdapter(MusicPlatformAdapter):
    """
    Mock SoundCloud adapter.

    PURPOSE:
    --------
    This adapter is intentionally used when real SoundCloud API access
    is unavailable (e.g., missing credentials, pending approval, demo mode).

    It allows the system to:
    - Demonstrate platform-agnostic architecture
    - Exercise core sync logic without external dependencies
    - Support demos, tests, CI pipelines, and recruiter reviews
    - Avoid blocking development due to third-party limitations

    IMPORTANT:
    ----------
    This is NOT a fallback due to failure.
    This is a deliberate architectural choice.

    FUTURE BEHAVIOR:
    ----------------
    When real SoundCloud credentials are available and enabled:
    - This adapter should NOT be modified
    - Runtime switching should happen via adapter_factory.py
    - Core sync logic must remain unchanged

    This guarantees that enabling real SoundCloud support
    requires minimal effort and zero refactoring.
    """

    CAPABILITIES = {
        "search": True,
        "playlist_management": True,
        "library_management": True,
        "favorites_management": True,
        "playlist_creation": True,
        "playback_control": False,
    }

    def __init__(self, access_token: str = None, **kwargs):
        pass

    def fetch_liked_tracks(self, limit: int = 50) -> List[dict]:
        return [
            {
                "track_uri": "soundcloud:track:mock1",
                "meta_data": {
                    "title": "Mock SoundCloud Track",
                    "artist": "Mock Artist",
                    "duration_ms": 180000,
                }
            }
        ]

    def fetch_user_playlists(self) -> List[dict]:
        return [
            {
                "playlist_id": "mock_playlist_1",
                "name": "Mock SoundCloud Playlist",
                "meta_data": {
                    "track_count": 1
                }
            }
        ]

    def search_track_uris(
        self,
        db: Session,
        platform_account_id: int,
        query: str,
        limit: int = 1
    ) -> List[str]:
        return ["soundcloud:track:mock1"]
