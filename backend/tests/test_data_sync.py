import datetime
import pytest
from unittest.mock import MagicMock
from backend.services.sync_service import sync_user_library
from backend.models.database_models import PlatformAccount, UserLikedSong, UserPlaylist

@pytest.fixture
def mock_platform_account():
    return PlatformAccount(
        id=1,
        refresh_token="fake_token",
        last_synced=None
    )

@pytest.fixture
def mock_spotify_adapter(monkeypatch):
    mock_instance = MagicMock()
    mock_instance.fetch_liked_tracks.return_value = [
        {"uri": "spotify:track:123", "meta_data": {"track_name": "Song A"}},
        {"uri": "spotify:track:456", "meta_data": {"track_name": "Song B"}},
    ]
    mock_instance.fetch_user_playlists.return_value = [
        {"id": "playlist_1", "name": "My Playlist", "description": "Test Desc", "owner": {"display_name": "User1"}, "tracks": {"total": 5}},
        {"id": "playlist_2", "name": "Road Trip", "description": "Another Desc", "owner": {"display_name": "User2"}, "tracks": {"total": 10}},
    ]
    monkeypatch.setattr("backend.services.sync_service.SpotifyAdapter", lambda access_token: mock_instance)
    return mock_instance

def test_sync_user_library_inserts_only_new_data(test_db, mock_platform_account, mock_spotify_adapter):
    # Pre-insert one liked song and one playlist so they should be skipped
    existing_song = UserLikedSong(
        platform_account_id=1,
        track_uri="spotify:track:123",
        meta_data={"track_name": "Song A"}
    )
    existing_playlist = UserPlaylist(
        platform_account_id=1,
        playlist_id="playlist_1",
        name="My Playlist",
        meta_data={"normalized_name": "my playlist"}
    )
    test_db.add_all([existing_song, existing_playlist])
    test_db.commit()

    sync_user_library(test_db, mock_platform_account, access_token="dummy")

    new_liked_songs = test_db.query(UserLikedSong).filter(UserLikedSong.track_uri == "spotify:track:456").all()
    new_playlists = test_db.query(UserPlaylist).filter(UserPlaylist.playlist_id == "playlist_2").all()

    assert len(new_liked_songs) == 1
    assert len(new_playlists) == 1
    assert mock_platform_account.last_synced is not None
