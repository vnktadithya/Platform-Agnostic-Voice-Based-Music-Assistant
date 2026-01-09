import os
import logging
import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyAuthBase
from spotipy.exceptions import SpotifyException
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from backend.adapters.adapter_base import MusicPlatformAdapter
from backend.models.database_models import UserPlaylist, UserLikedSong, SearchCache
from backend.utils.fuzzy_utils import fuzzy_db_match, fuzzy_search_cache
from backend.utils.normalize_text import normalize_query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class TokenAuthManager(SpotifyAuthBase):
    def __init__(self, token: str):
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))
        # The session must be passed to the parent constructor
        super().__init__(session) 
        self.token = token

    def get_access_token(self, as_dict=False):
        # The as_dict=False is important to match the base class signature
        return self.token

class NoActiveDeviceException(Exception):
    """Custom exception for when no active Spotify device is found."""
    pass

class SpotifyAdapter(MusicPlatformAdapter):

    CAPABILITIES = {
        "playback_control": True,
        "playlist_management": True,
        "library_management": True,
        "search": True,
        "recommendations": True,
        "real_time_control": True,
        "favorites_management": True,
        "playlist_creation": True,
        "voice_control": True,
    }

    def __init__(self, access_token: str):
        if not access_token:
            raise ValueError("SpotifyAdapter requires a valid user access_token.")
                
        auth_manager = TokenAuthManager(access_token)
        self.sp = Spotify(auth_manager=auth_manager, requests_timeout=15)
        logger.info("SpotifyAdapter initialized for ACTION")

    def _get_active_device_id(self) -> str:
        """Finds an active device; raises NoActiveDeviceException if none are available."""
        try:
            devices_info = self.sp.devices()
            devices = devices_info.get('devices', []) if devices_info else []
            if not devices:
                raise NoActiveDeviceException("No Spotify devices are connected to this account.")

            active_devices = [d for d in devices if d.get('is_active')]
            if active_devices:
                device = active_devices[0]
                logger.info(f"Found active device: {device['name']} (ID: {device['id']})")
                return device['id']
            
            # If no device is marked 'active', fall back to the first one available.
            device = devices[0]
            logger.warning(f"No active device found. Falling back to first available: {device['name']} (ID: {device['id']})")
            return device['id']
        except SpotifyException as e:
            logger.error(f"Could not retrieve devices from Spotify: {e}")
            raise NoActiveDeviceException("Failed to get device list from Spotify. The token may be invalid or expired.")


    # === Auth Flow ===
    @staticmethod
    def get_auth_manager():
        """Creates an OAuth manager for the login flow."""
        return SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri="http://127.0.0.1:8000/adapter/spotify/callback",
            scope=(
                    "user-read-private user-read-email "
                    "user-library-read user-library-modify "
                    "playlist-read-private playlist-read-collaborative "
                    "playlist-modify-public playlist-modify-private "
                    "user-read-playback-state user-modify-playback-state user-read-currently-playing "
                    "user-top-read user-read-recently-played user-follow-read user-follow-modify"
                ),
            cache_path=None
        )

    @staticmethod
    def get_auth_url() -> str:
        """Gets the URL for user authorization."""
        auth_manager = SpotifyAdapter.get_auth_manager()
        return auth_manager.get_authorize_url()
    
    @staticmethod
    def handle_auth_callback(code: str) -> dict:
        """Handles the OAuth callback to fetch user tokens and profile."""
        auth_manager = SpotifyAdapter.get_auth_manager()
        token_info = auth_manager.get_access_token(code, as_dict=True, check_cache=False)
        access_token = token_info["access_token"]
        refresh_token = token_info["refresh_token"]
        expires_in = token_info["expires_in"]
        expires_at = (
                datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            ).isoformat() if expires_in else None
        
        # Use a temporary adapter instance to fetch user details with the new token
        temp_adapter = SpotifyAdapter(access_token=access_token)
        user = temp_adapter.sp.current_user()
        
        return {
            "user": {"id": user["id"], "name": user.get("display_name", ""), "email": user.get("email")},
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at,
                "scope": token_info.get("scope"),
                "token_type": token_info.get("token_type", "Bearer")
            }
        }

    # === Playback Controls ===
    def play(self, uris: list[str]):
        device_id = self._get_active_device_id()
        logger.debug(f"Attempting to play URIs on device {device_id}")
        self.sp.start_playback(device_id=device_id, uris=uris)
        logger.debug("Spotify 'start_playback' command sent successfully.")

    def pause(self):
        device_id = self._get_active_device_id()
        logger.debug(f"Attempting to pause playback on device {device_id}")
        self.sp.pause_playback(device_id=device_id)
        logger.debug("Spotify 'pause_playback' command sent successfully.")

    def resume(self):
        device_id = self._get_active_device_id()
        logger.debug(f"Attempting to resume playback on device {device_id}")
        self.sp.start_playback(device_id=device_id)
        logger.debug("Spotify 'resume' command sent successfully.")

    def skip_current_track(self):
        device_id = self._get_active_device_id()
        logger.debug(f"Attempting to skip track on device {device_id}")
        self.sp.next_track(device_id=device_id)
        logger.debug("Spotify 'next_track' command sent successfully.")

    def previous_track(self):
        device_id = self._get_active_device_id()
        logger.debug(f"Attempting to go to previous track on device {device_id}")
        self.sp.previous_track(device_id=device_id)
        logger.debug("Spotify 'previous_track' command sent successfully.")

    def restart_current_track(self):
        device_id = self._get_active_device_id()
        logger.debug(f"Attempting to restart track on device {device_id}")
        self.sp.seek_track(0, device_id=device_id)
        logger.debug("Spotify 'seek_track' to 0ms command sent successfully.")

    def seek_position(self, seconds: int):
        device_id = self._get_active_device_id()
        logger.debug(f"Attempting to seek to {seconds}s on device {device_id}")
        self.sp.seek_track(seconds * 1000, device_id=device_id)
        logger.debug(f"Spotify 'seek_track' to {seconds * 1000}ms command sent successfully.")

    def get_currently_playing_song(self):
        try:
            playback = self.sp.current_playback()
            if playback and playback.get("item"):
                item = playback["item"]
                song_name = item.get("name")
                artist_names = ", ".join([artist["name"] for artist in item.get("artists", [])])
                return {
                    "song_name": song_name,
                    "artist": artist_names,
                    "uri": item.get("uri")
                }
            return None
        except Exception:
            logger.error(f"Error fetching current playback")
            return None


    # === Liked Songs ===
    def add_current_to_favorites(self, db: Session, platform_account_id: int):
        """Likes the current track on Spotify and stores its metadata in local cache."""
        current = self.sp.current_playback()
        if not current or not current.get("item"):
            logger.warning("No current playback track found.")
            return

        track = current["item"]
        track_id = track["id"]
        track_uri = track["uri"]

        logger.info(f"Liking track on Spotify: {track['name']}")
        self.sp.current_user_saved_tracks_add([track_id])

        # Ensure it's also stored in local DB
        existing = db.query(UserLikedSong).filter_by(
            platform_account_id=platform_account_id,
            track_uri=track_uri
        ).first()

        if existing:
            logger.info(f"Track already exists in DB cache: {track['name']}")
            return

        db.add(UserLikedSong(
            platform_account_id=platform_account_id,
            track_uri=track_uri,
            meta_data={
                "track_name": track["name"],
                "artist": track["artists"][0]["name"],
                "album_name": track["album"]["name"],
                "duration_ms": track.get("duration_ms", 0)
            }
        ))
        db.commit()
        logger.info(f"Cached liked song '{track['name']}' to DB.")


    def remove_current_from_favorites(self, db: Session, platform_account_id: int):
        """Unlikes current track and removes it from local DB."""
        current = self.sp.current_playback()
        if not current or not current.get("item"):
            logger.warning("No track currently playing.")
            return

        track = current["item"]
        track_id = track["id"]
        track_uri = track["uri"]

        # Remove from Spotify liked
        self.sp.current_user_saved_tracks_delete([track_id])
        logger.info(f"Unliked track '{track['name']}' on Spotify.")

        # Remove from DB cache
        existing = db.query(UserLikedSong).filter_by(
            platform_account_id=platform_account_id,
            track_uri=track_uri
        ).first()
        if existing:
            db.delete(existing)
            db.commit()
            logger.info(f"Removed '{track['name']}' from local cache.")


    def fetch_liked_tracks(self, limit: int = 50) -> list:
        logger.info("Fetching liked tracks and their audio features.")
        results = self.sp.current_user_saved_tracks(limit=limit)
        tracks = [item["track"] for item in results["items"] if item.get("track")]
        if not tracks:
            return []
        
        enriched_tracks = []
        for track in tracks:
            enriched_tracks.append({
                "id": track["id"],
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "uri": track["uri"],
                "meta_data": {
                    "duration_ms": track["duration_ms"],
                    "album_name": track["album"]["name"]
                }
            })
        return enriched_tracks
    
    def play_liked_songs(self, db: Session, platform_account_id: int):
        tracks = self.fetch_liked_tracks(limit=50)
        if not tracks:
            raise Exception("No liked songs found.")

        uris = [t["uri"] for t in tracks if t.get("uri")]
        self.play(uris)


    # === Playlist Management ===
    def create_playlist(self, db: Session, platform_account_id: int, user_id: str, name: str, description: str = ""):
        """Creates a playlist on Spotify and immediately caches it in the local DB."""
        logger.info(f"Creating playlist '{name}' on Spotify.")
        playlist_data = self.sp.user_playlist_create(user=user_id, name=name, description=description, public=True)
        
        # ✅ Layer 1 in action: Immediately write to the local database
        if playlist_data:
            new_playlist = UserPlaylist(
                platform_account_id=platform_account_id,
                playlist_id=playlist_data['id'],
                name=playlist_data['name']
            )
            db.add(new_playlist)
            db.commit()
            logger.info(f"Successfully cached new playlist '{name}' in the local database.")
        return playlist_data

    def delete_user_playlist(self, db: Session, platform_account_id: int, playlist_name: str):
        """Deletes a playlist by fuzzy matching its name, then unfollowing on Spotify and removing from DB."""

        if not playlist_name:
            raise ValueError("playlist_name is required and cannot be None or empty.")
        
        playlists = db.query(UserPlaylist).filter_by(platform_account_id=platform_account_id).all()

        matched_playlist, score = fuzzy_db_match(playlist_name, playlists, attr="name", threshold=80)
        if matched_playlist is None:
            raise ValueError(f"No playlist matching '{playlist_name}' found with sufficient confidence.")

        playlist_id = matched_playlist.playlist_id
        logger.info(f"Deleting playlist '{matched_playlist.name}' (score: {score}) with ID '{playlist_id}'.")

        self.sp.current_user_unfollow_playlist(playlist_id)

        playlist_to_delete = db.query(UserPlaylist).filter_by(
            platform_account_id=platform_account_id,
            playlist_id=playlist_id
        ).first()

        if playlist_to_delete:
            db.delete(playlist_to_delete)
            db.commit()
            logger.info(f"Successfully removed playlist '{matched_playlist.name}' from local cache.")

    def add_tracks_to_playlist(self, playlist_id: str, uris: list):
        self.sp.playlist_add_items(playlist_id, uris)

    def remove_tracks_from_playlist(self, playlist_id: str, uris: list):
        self.sp.playlist_remove_all_occurrences_of_items(playlist_id, uris)

    def reorder_playlist_tracks(self, playlist_id: str, range_start: int, insert_before: int):
        self.sp.playlist_reorder_items(playlist_id, range_start, insert_before)

    # === Music Search & Playback by Metadata ===
    def search_track_uris(
        self,
        db: Session,
        platform_account_id: int,
        query: str,
        limit: int = 1,
        song_name: str | None = None,
        artist_name: str | None = None,
        use_cache: bool = True,
    ) -> list:
        """
        Search tracks by user query.

        - If song_name and artist_name are provided, first try a strict cache
        lookup on both fields in the same SearchCache row.
        - Otherwise, fall back to existing fuzzy normalized_query + Spotify API.
        """
        norm_query = normalize_query(query)

        # ----- 1) Strict song+artist cache lookup (for precise cases) -----
        if use_cache and song_name and artist_name:
            norm_song = normalize_query(song_name)
            norm_artist = normalize_query(artist_name)

            cache_records = db.query(SearchCache).filter(
                SearchCache.platform_account_id == platform_account_id
            ).all()

            for rec in cache_records:
                meta = rec.meta_data or {}
                cached_song = normalize_query(meta.get("track_name", "")) if meta.get("track_name") else ""
                cached_artist = normalize_query(meta.get("artist", "")) if meta.get("artist") else ""
                if cached_song == norm_song and cached_artist == norm_artist:
                    logger.info("Strict SearchCache hit: song='%s', artist='%s' → %s", song_name, artist_name, rec.track_uri,)
                    return [rec.track_uri]

            logger.info("No strict cache hit for song='%s', artist='%s'; querying Spotify API directly", song_name, artist_name,)

        # ----- 2) Original fuzzy normalized_query cache path -----
        elif use_cache:
            cache_records = db.query(SearchCache).filter(
                SearchCache.platform_account_id == platform_account_id
            ).all()

            match, score = fuzzy_search_cache(norm_query, cache_records, threshold=75)
            if match:
                logger.info("Fuzzy SearchCache hit: '%s' (score: %s)", match.normalized_query, score)
                return [match.track_uri]

        # ----- 3) Spotify API search + cache top result -----
        logger.warning("No SearchCache match for '%s'. Querying Spotify API.", query)
        results = self.sp.search(q=query, type="track", limit=limit)
        tracks = results.get("tracks", {}).get("items", [])
        uris = [track["uri"] for track in tracks]

        if tracks:
            track = tracks[0]
            db.add(
                SearchCache(
                    platform_account_id=platform_account_id,
                    normalized_query=norm_query,
                    track_uri=track["uri"],
                    meta_data={
                        "track_name": track.get("name", ""),
                        "artist": track["artists"][0].get("name", "")
                        if track.get("artists")
                        else "",
                        "album_name": track["album"].get("name", "")
                        if track.get("album")
                        else "",
                        "duration_ms": track.get("duration_ms", 0),
                    },
                )
            )
            db.commit()
            logger.info("Cached search result '%s' → '%s' in SearchCache.", norm_query, track.get("name"),)

        return uris

    def play_by_query(
        self,
        db: Session,
        platform_account_id: int,
        query: str,
        limit: int = 5,
        song_name: str | None = None,
        artist_name: str | None = None,
        use_cache: bool = True,
    ):
        uris = self.search_track_uris(
            db,
            platform_account_id,
            query,
            limit=limit,
            song_name=song_name,
            artist_name=artist_name,
            use_cache=use_cache,
        )
        if uris:
            self.play(uris=uris)


    def fetch_user_playlists(self) -> list:
        # Fetches ALL of a user's playlists, paginating through results if necessary
        logger.info("Fetching all user playlists from Spotify API.")
        all_playlists = []
        results = self.sp.current_user_playlists()
        
        while results and results.get('items'):
            all_playlists.extend(results['items'])
            # Check if there is a next page of results
            if results['next']:
                results = self.sp.next(results)
            else:
                break
                
        return all_playlists
    
    def play_playlist_by_name(self, db: Session, platform_account_id: int, playlist_name: str):
        """
        Plays a playlist by name using fuzzy match in DB first,
        then falling back to Spotify API. Uses context_uri with playlist ID
        for correct playback via Spotify API.
        """
        norm_playlist_name = normalize_query(playlist_name)  # Normalizing user input

        playlists = db.query(UserPlaylist).filter(
            UserPlaylist.platform_account_id == platform_account_id
        ).all()

        # Define a temporary wrapper class to access normalized name fallback
        class PlaylistNormView:
            def __init__(self, original):
                self._original = original
                self.normalized_name = ""

                if original.meta_data and isinstance(original.meta_data, dict):
                    v = original.meta_data.get("normalized_name")
                    if v:
                        self.normalized_name = v

                # fallback normalization
                if not self.normalized_name and original.name:
                    self.normalized_name = normalize_query(original.name)

            def __getattr__(self, attr):
                return getattr(self._original, attr)

        wrapped_playlists = [PlaylistNormView(pl) for pl in playlists]
        match, score = fuzzy_db_match(norm_playlist_name, wrapped_playlists, attr="normalized_name", threshold=80)

        playlist_id = None
        playlist_display_name = playlist_name
        if match:
            playlist_id = match.playlist_id
            playlist_display_name = match.name
            logger.info(f"Found playlist via fuzzy match in DB: '{playlist_display_name}' (score: {score})")
        else:
            logger.warning(f"No DB match for '{playlist_name}'. Falling back to Spotify API search...")
            results = self.sp.search(q=playlist_name, type="playlist", limit=1)
            playlists_api = results.get("playlists", {}).get("items", [])
            if not playlists_api:
                raise Exception(f"Playlist '{playlist_name}' not found in DB or Spotify API.")
            playlist_data = playlists_api[0]
            playlist_id = playlist_data["id"]
            playlist_display_name = playlist_data.get("name", "")
            owner_id = playlist_data.get("owner", {}).get("id")

            current_user = self.sp.current_user()
            current_user_id = current_user.get("id")

            if owner_id == current_user_id:
                # Safe to cache — user owns this playlist
                normalized_name = normalize_query(playlist_display_name)

                # Cache new playlist in DB
                db.add(UserPlaylist(
                    platform_account_id=platform_account_id,
                    playlist_id=playlist_id,
                    name=playlist_display_name,
                    meta_data={
                        "normalized_name": normalized_name,
                        "description": playlist_data.get("description", ""),
                        "owner": playlist_data.get("owner", {}).get("display_name", ""),
                        "track_count": playlist_data.get("tracks", {}).get("total", 0),
                    }
                ))
                db.commit()
                logger.info(f"Cached new playlist '{playlist_display_name}' from Spotify API into DB.")

        # Use context_uri to play playlist by ID to avoid unsupported URI kind error
        device_id = self._get_active_device_id()
        context_uri = f"spotify:playlist:{playlist_id}"
        logger.info(f"Playing playlist '{playlist_display_name}' using context URI: {context_uri} on device {device_id}")
        self.sp.start_playback(device_id=device_id, context_uri=context_uri)


    
    def resolve_playlist_id(self, db: Session, platform_account_id: int, playlist_name: str) -> str:
        """Resolve a playlist_name into a Spotify playlist_id (DB first, fallback API)."""
        norm_name = normalize_query(playlist_name)
        playlists = db.query(UserPlaylist).filter_by(platform_account_id=platform_account_id).all()

        # fuzzy match
        match, score = fuzzy_db_match(norm_name, playlists, attr="name", threshold=80)
        if match:
            return match.playlist_id

        # fallback: Spotify API search
        results = self.sp.search(q=playlist_name, type="playlist", limit=1)
        items = results.get("playlists", {}).get("items", [])
        if items:
            playlist_data = items[0]
            return playlist_data["id"]

        raise ValueError(f"Playlist '{playlist_name}' not found")