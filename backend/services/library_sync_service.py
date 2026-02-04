import datetime
from sqlalchemy.orm import Session
from backend.models.database_models import UserPlaylist, UserLikedSong, PlatformAccount
from backend.utils.normalize_text import normalize_query

def sync_user_library(db: Session, platform_account: PlatformAccount, adapter):

    # Sync liked songs
    liked_songs_data = adapter.fetch_liked_tracks(limit=50)
    new_songs = []
    for song_data in liked_songs_data:
        existing = db.query(UserLikedSong).filter_by(track_uri=song_data['uri']).first()
        if not existing:
            meta = song_data.get('meta_data', {}) or {}
            track_name = meta.get("album_name", "")
            meta["normalized_name"] = normalize_query(track_name) if track_name else ""
            new_songs.append(UserLikedSong(
                platform_account_id=platform_account.id,
                track_uri=song_data['uri'],
                meta_data=meta
            ))
    if new_songs:
        db.bulk_save_objects(new_songs)

    # Sync playlists
    playlists_data = adapter.fetch_user_playlists() or []
    new_playlists = []
    for playlist in playlists_data:
        existing = db.query(UserPlaylist).filter_by(playlist_id=playlist['id']).first()
        normalized_name = normalize_query(playlist['name']) if playlist.get('name') else ""
        if existing:
            existing.name = playlist['name']
            existing.meta_data = existing.meta_data or {}
            existing.meta_data['normalized_name'] = normalized_name
        else:
            new_playlists.append(UserPlaylist(
                platform_account_id=platform_account.id,
                playlist_id=playlist['id'],
                name=playlist['name'],
                meta_data={
                    "normalized_name": normalized_name,
                    "description": playlist.get("description", ""),
                    "owner": playlist.get("owner", {}).get("display_name", ""),
                    "track_count": playlist.get("tracks", {}).get("total", 0),
                    "image": playlist.get("images")[0]["url"] if playlist.get("images") else None
                }
            ))
    if new_playlists:
        db.bulk_save_objects(new_playlists)

    platform_account.last_synced = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
