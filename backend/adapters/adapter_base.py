# backend/adapters/adapter_base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

class NotSupportedError(Exception):
    """Raised when an adapter does not support a particular action."""
    pass

class MusicPlatformAdapter(ABC):
    """
    Abstract adapter for all music services.
    Subclasses should implement methods for supported features.
    Unsupported methods should raise NotSupportedError.
    """

    # ----------- Initialization and Auth -----------

    @abstractmethod
    def __init__(self, access_token: Optional[str] = None, **kwargs):
        """
        Common constructor for all music adapters.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_auth_url() -> str:
        """Return login/OAuth URL for the platform."""
        raise NotSupportedError("OAuth not supported on this platform.")

    @staticmethod
    @abstractmethod
    def handle_auth_callback(code: str) -> dict:
        """Handle login/OAuth callback and issue access tokens/user data."""
        raise NotSupportedError("OAuth callback not supported on this platform.")

    # ----------- Playback Control -----------

    def play(self, uris: List[str]) -> Any:
        raise NotSupportedError("Direct playback is not supported on this platform.")

    def pause(self):
        raise NotSupportedError("Pause is not supported on this platform.")

    def resume(self):
        raise NotSupportedError("Resume is not supported on this platform.")

    def skip_current_track(self):
        raise NotSupportedError("Skip is not supported on this platform.")

    def previous_track(self):
        raise NotSupportedError("Previous track is not supported on this platform.")

    def restart_current_track(self):
        raise NotSupportedError("Restart track is not supported on this platform.")

    def seek_position(self, seconds: int):
        raise NotSupportedError("Seek is not supported on this platform.")

    def get_currently_playing_song(self) -> Optional[Dict]:
        """Returns {song_name, artist, uri}, or None if not available."""
        raise NotSupportedError("Current playback info not supported on this platform.")

    # ----------- Playlist Management -----------

    def create_playlist(self, db: Session, platform_account_id: int, user_id: str, name: str, description: str = ""):
        raise NotSupportedError("Playlist creation not supported on this platform.")

    def delete_user_playlist(self, db: Session, platform_account_id: int, playlist_name: str):
        raise NotSupportedError("Playlist deletion not supported on this platform.")

    def fetch_user_playlists(self) -> List[Dict]:
        raise NotSupportedError("Fetching playlists not supported on this platform.")

    def add_tracks_to_playlist(self, playlist_id: str, uris: List[str]):
        raise NotSupportedError("Adding tracks to playlist not supported.")

    def remove_tracks_from_playlist(self, playlist_id: str, uris: List[str]):
        raise NotSupportedError("Removing tracks from playlist not supported.")

    def reorder_playlist_tracks(self, playlist_id: str, range_start: int, insert_before: int):
        raise NotSupportedError("Reorder playlist not supported.")

    def play_playlist_by_name(self, db: Session, platform_account_id: int, playlist_name: str):
        raise NotSupportedError("Play playlist by name not supported on this platform.")

    # ----------- Music Search & Metadata -----------

    @abstractmethod
    def search_track_uris(self, db: Session, platform_account_id: int, query: str, limit: int = 1) -> List[str]:
        pass

    def play_by_query(self, db: Session, platform_account_id: int, query: str, limit: int = 5):
        raise NotSupportedError("Play by query not supported.")

    # ----------- Liked Songs / Library -----------

    def fetch_liked_tracks(self, limit: int = 50) -> List[Dict]:
        raise NotSupportedError("Fetching liked tracks not supported.")

    def add_current_to_favorites(self, db: Session, platform_account_id: int):
        raise NotSupportedError("Adding to favorites not supported.")

    def remove_current_from_favorites(self, db: Session, platform_account_id: int):
        raise NotSupportedError("Removing from favorites not supported.")

    # ----------- Platform Capability Reporting -----------

    @classmethod
    def get_capabilities(cls) -> Dict[str, bool]:
        """
        Return explicit dictionary of capabilities for the platform.
        Override this in subclasses to declare supported features.
        """
        # Default capabilities as False
        default_caps = {
            "playback_control": False,
            "playlist_management": False,
            "library_management": False,
            "search": False,
            "recommendations": False,
            "real_time_control": False,
            "favorites_management": False,
            "playlist_creation": False, 
            "voice_control": False,
        }
        
        # If subclass has defined CAPABILITIES dict, merge those values
        if hasattr(cls, "CAPABILITIES") and isinstance(cls.CAPABILITIES, dict):
            merged = default_caps.copy()
            merged.update(cls.CAPABILITIES)
            return merged
        return default_caps