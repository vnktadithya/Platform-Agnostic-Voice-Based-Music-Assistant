import datetime
from sqlalchemy.orm import Session
from backend.models.database_models import UserPlaylist, UserLikedSong, PlatformAccount
from backend.utils.normalize_text import normalize_query

def sync_user_library(db: Session, platform_account: PlatformAccount, adapter):

    # Sync liked songs
    liked_songs_data = adapter.fetch_liked_tracks(limit=50)
    new_songs = []
    
    # Get current user's liked songs to avoid duplicates
    existing_uris = {
        song.track_uri for song in 
        db.query(UserLikedSong.track_uri).filter_by(platform_account_id=platform_account.id).all()
    }

    for song_data in liked_songs_data:
        if song_data['uri'] in existing_uris:
            continue
            
        meta = song_data.get('meta_data', {}) or {}
        # FIX: SoundCloud adapter returns 'title', not 'album_name'
        track_name = meta.get("title") or meta.get("track_name", "Unknown Track")
        
        # Ensure metadata has normalized name for search
        meta["normalized_name"] = normalize_query(track_name)
        
        new_songs.append(UserLikedSong(
            platform_account_id=platform_account.id,
            track_uri=song_data['uri'],
            meta_data=meta
        ))
        existing_uris.add(song_data['uri']) # Prevent duplicates within same batch

    if new_songs:
        db.bulk_save_objects(new_songs)

    # Sync playlists
    playlists_data = adapter.fetch_user_playlists() or []
    new_playlists = []
    
    for playlist in playlists_data:
        # Check if exists
        existing = db.query(UserPlaylist).filter_by(
            platform_account_id=platform_account.id, 
            playlist_id=str(playlist['id'])
        ).first()
        
        name = playlist.get('name') or playlist.get('title', f"Playlist {playlist['id']}")
        normalized_name = normalize_query(name)
        
        # Extract owner name safely (SoundCloud adapter returns 'owner': {'display_name': ...})
        owner_name = "Unknown"
        owner_data = playlist.get("owner")
        if isinstance(owner_data, dict):
            owner_name = owner_data.get("display_name") or owner_data.get("username", "Unknown")
        elif isinstance(owner_data, str):
            owner_name = owner_data
            
        # Extract image safely
        image_url = None
        images = playlist.get("images")
        if images and isinstance(images, list) and len(images) > 0:
            image_url = images[0].get("url")
            
        meta_data = {
            "normalized_name": normalized_name,
            "description": playlist.get("description", ""),
            "owner": owner_name,
            "track_count": playlist.get("tracks", {}).get("total", 0) if isinstance(playlist.get("tracks"), dict) else 0,
            "image": image_url
        }

        if existing:
            existing.name = name
            existing.meta_data = meta_data
        else:
            new_playlists.append(UserPlaylist(
                platform_account_id=platform_account.id,
                playlist_id=str(playlist['id']),
                name=name,
                meta_data=meta_data
            ))
    if new_playlists:
        db.bulk_save_objects(new_playlists)

    platform_account.last_synced = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
