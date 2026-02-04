import logging
import requests
from typing import Dict
from backend.adapters.spotify_adapter import SpotifyAdapter, NoActiveDeviceException
from backend.adapters.soundcloud_adapter import SoundCloudAdapter
from spotipy.exceptions import SpotifyException
from backend.models.database_models import UserPlaylist, UserLikedSong, SearchCache, InteractionLog, PlatformAccount
from backend.configurations.redis_client import redis_client
import json
from sqlalchemy import desc
from backend.utils.custom_exceptions import DeviceNotFoundException, ExternalAPIError, AuthenticationError

logger = logging.getLogger(__name__)

class MusicActionService:
    @staticmethod
    def _get_spotify_adapter(parameters: Dict) -> SpotifyAdapter:
        token = parameters.get("access_token")

        if not token:
            raise RuntimeError(
                "Spotify access_token missing at execution time. "
                "Credential resolution failed earlier in the pipeline."
            )

        return SpotifyAdapter(token)

    @staticmethod
    def _get_soundcloud_adapter(parameters: Dict) -> SoundCloudAdapter:
        token = parameters.get("access_token")
        if not token:
             raise RuntimeError("SoundCloud access_token missing.")
        return SoundCloudAdapter(token)
    
    # ========================== SPOTIFY ACTIONS ==========================

    @staticmethod
    def _spotify_play_song(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).play_by_query(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("song_name", ""),
            resolve_only=parameters.get("resolve_only", False)
        )

    @staticmethod
    def _spotify_play_song_by_artist(parameters: Dict):
        song = parameters.get("song_name", "")
        artist = parameters.get("artist", "") or parameters.get("artist_name", "")
        if song and artist:
            query = f'track:"{song}" artist:"{artist}"'
        else:
            query = artist or song
        
        return MusicActionService._get_spotify_adapter(parameters).play_by_query(
            parameters["db_session"],
            parameters["platform_account_id"],
            query,
            song_name=song or None,
            artist_name=artist or None,
            use_cache=True,
            resolve_only=parameters.get("resolve_only", False)
        )

    @staticmethod
    def _spotify_play_song_by_movie(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).play_by_query(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("movie_name", ""),
            resolve_only=parameters.get("resolve_only", False)
        )

    @staticmethod
    def _spotify_play_playlist_by_name(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).play_playlist_by_name(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("playlist_name", ""),
            resolve_only=parameters.get("resolve_only", False)
        )

    @staticmethod
    def _spotify_get_current_song(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).get_currently_playing_song()

    @staticmethod
    def _spotify_pause_song(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).pause()

    @staticmethod
    def _spotify_resume_song(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).resume()

    @staticmethod
    def _spotify_skip_song(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).skip_current_track()

    @staticmethod
    def _spotify_previous_song(parameters: Dict):
        return MusicActionService._handle_spotify_previous_song(parameters)

    @staticmethod
    def _spotify_restart_song(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).restart_current_track()

    @staticmethod
    def _spotify_skip_time(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).seek_position(int(parameters.get("seconds", 0)))



    @staticmethod
    def _spotify_get_volume(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).get_volume()

    @staticmethod
    def _spotify_change_volume(parameters: Dict):
        vol = parameters.get("volume")
        # Ensure volume is an int or None
        if vol is not None:
            try:
                vol = int(vol)
            except (ValueError, TypeError):
                vol = None

        return MusicActionService._get_spotify_adapter(parameters).change_volume(
            volume_change=vol,
            mode=parameters.get("mode", "increase")
        )


    @staticmethod
    def _spotify_like_song(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).add_current_to_favorites(
            parameters["db_session"],
            parameters["platform_account_id"]
        )

    @staticmethod
    def _spotify_remove_from_liked_songs(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).remove_current_from_favorites(
            parameters["db_session"],
            parameters["platform_account_id"]
        )

    @staticmethod
    def _spotify_play_liked_songs(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).play_liked_songs(
            parameters["db_session"],
            parameters["platform_account_id"]
        )

    @staticmethod
    def _spotify_create_playlist(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).create_playlist(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("user_id"),
            parameters.get("playlist_name"),
            user_display_name=parameters.get("user_display_name")
        )

    @staticmethod
    def _spotify_delete_playlist(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).delete_user_playlist(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("playlist_name")
        )

    @staticmethod
    def _spotify_add_to_playlist(parameters: Dict):
        adapter = MusicActionService._get_spotify_adapter(parameters)
        return adapter.add_tracks_to_playlist(
            parameters["db_session"],
            parameters["platform_account_id"],
            adapter.resolve_playlist_id(
                parameters["db_session"], 
                parameters["platform_account_id"], 
                parameters.get("playlist_name", "")
            ),
            adapter.search_track_uris(
                parameters["db_session"],
                parameters["platform_account_id"],
                parameters.get("song_name", ""),
                limit=1)
            )

    @staticmethod
    def _spotify_remove_from_playlist(parameters: Dict):
        adapter = MusicActionService._get_spotify_adapter(parameters)
        return adapter.remove_tracks_from_playlist(
            parameters["db_session"],
            parameters["platform_account_id"],
            adapter.resolve_playlist_id(
                parameters["db_session"],
                parameters["platform_account_id"],
                parameters.get("playlist_name", "")
            ),
            adapter.search_track_uris(
                parameters["db_session"],
                parameters["platform_account_id"],
                parameters.get("song_name", ""),
                limit=1
            )
        )

    @staticmethod
    def _spotify_reorder_playlist(parameters: Dict):
        return MusicActionService._get_spotify_adapter(parameters).reorder_playlist_tracks(
            parameters.get("playlist_id"),
            parameters.get("range_start", 0),
            parameters.get("insert_before", 0)
        )

    # ========================== SOUNDCLOUD ACTIONS ==========================

    @staticmethod
    def _soundcloud_play_song(parameters: Dict):
        return MusicActionService._get_soundcloud_adapter(parameters).play_by_query(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("song_name", "")
        )

    @staticmethod
    def _soundcloud_play_song_by_artist(parameters: Dict):
        return MusicActionService._get_soundcloud_adapter(parameters).play_by_query(
            parameters["db_session"],
            parameters["platform_account_id"],
            f"{parameters.get('song_name', '')} {parameters.get('artist', '')}"
        )

    @staticmethod
    def _soundcloud_play_song_by_movie(parameters: Dict):
        return MusicActionService._get_soundcloud_adapter(parameters).play_by_query(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("movie_name", "")
        )

    @staticmethod
    def _soundcloud_play_playlist_by_name(parameters: Dict):
        return MusicActionService._get_soundcloud_adapter(parameters).play_playlist_by_name(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("playlist_name", "")
        )

    @staticmethod
    def _soundcloud_create_playlist(parameters: Dict):
        return MusicActionService._get_soundcloud_adapter(parameters).create_playlist(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("user_id"),
            parameters.get("playlist_name")
        )

    @staticmethod
    def _soundcloud_delete_playlist(parameters: Dict):
        return MusicActionService._get_soundcloud_adapter(parameters).delete_user_playlist(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("playlist_name")
        )

    @staticmethod
    def _soundcloud_add_to_playlist(parameters: Dict):
        adapter = MusicActionService._get_soundcloud_adapter(parameters)
        return adapter.add_tracks_to_playlist(
            parameters["db_session"],
            parameters["platform_account_id"],
            adapter.resolve_playlist_id(
                parameters["db_session"], 
                parameters["platform_account_id"], 
                parameters.get("playlist_name", "")
            ),
            adapter.search_track_uris(
                parameters["db_session"],
                parameters["platform_account_id"],
                parameters.get("song_name", ""),
                limit=1)
            )

    @staticmethod
    def _soundcloud_remove_from_playlist(parameters: Dict):
        adapter = MusicActionService._get_soundcloud_adapter(parameters)
        return adapter.remove_tracks_from_playlist(
            parameters["db_session"],
            parameters["platform_account_id"],
            adapter.resolve_playlist_id(
                parameters["db_session"],
                parameters["platform_account_id"],
                parameters.get("playlist_name", "")
            ),
            adapter.search_track_uris(
                parameters["db_session"],
                parameters["platform_account_id"],
                parameters.get("song_name", ""),
                limit=1)
        )

    @staticmethod
    def _soundcloud_like_song(parameters: Dict):
        if not parameters.get("song_name"):
            return "Please specify the song name to like on SoundCloud."
        
        adapter = MusicActionService._get_soundcloud_adapter(parameters)
        uris = adapter.search_track_uris(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("song_name", ""),
            limit=1
        )
        return adapter.add_track_to_favorites(
            parameters["db_session"],
            parameters["platform_account_id"],
            uris[0].split(":")[-1]
        )

    @staticmethod
    def _soundcloud_remove_from_liked_songs(parameters: Dict):
        if not parameters.get("song_name"):
             return "Please specify the song name to unlike on SoundCloud."
        
        adapter = MusicActionService._get_soundcloud_adapter(parameters)
        uris = adapter.search_track_uris(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("song_name", ""),
            limit=1
        )
        return adapter.remove_track_from_favorites(
            parameters["db_session"],
            parameters["platform_account_id"],
            uris[0].split(":")[-1]
        )

    @staticmethod
    def _soundcloud_pause_song(parameters: Dict): return "SoundCloud does not support remote pause."
    @staticmethod
    def _soundcloud_resume_song(parameters: Dict): return "SoundCloud does not support remote resume."
    @staticmethod
    def _soundcloud_skip_song(parameters: Dict): return "SoundCloud does not support remote skip."
    @staticmethod
    def _soundcloud_set_volume(parameters: Dict): return "SoundCloud does not support remote volume control."

    @staticmethod
    def _spotify_set_volume(parameters: Dict):
        """
        Sets absolute volume for Spotify.
        """
        vol = parameters.get("volume")
        if vol is None:
             return "Please specify a volume level."
        
        try:
            vol = int(vol)
        except (ValueError, TypeError):
             return "Invalid volume level."

        MusicActionService._get_spotify_adapter(parameters).set_volume(vol)
        return f"Volume set to {vol}%"
    
    @staticmethod
    def _soundcloud_change_volume(parameters: Dict): return "SoundCloud does not support remote volume control."
    
    @staticmethod
    def _soundcloud_previous_song(parameters: Dict): return "SoundCloud does not support previous song."
    
    @staticmethod
    def _soundcloud_restart_song(parameters: Dict): return "SoundCloud does not support restarting songs."
    
    @staticmethod
    def _soundcloud_skip_time(parameters: Dict): return "SoundCloud does not support seeking."
    
    @staticmethod
    def _soundcloud_get_current_song(parameters: Dict): return "SoundCloud does not support real-time playback info."

    @staticmethod
    def _soundcloud_reorder_playlist(parameters: Dict):
        return "SoundCloud playlist reordering is not yet implemented in this adapter."

    @staticmethod
    def _soundcloud_play_liked_songs(parameters: Dict):
        return MusicActionService._get_soundcloud_adapter(parameters).play_liked_songs(
            parameters["db_session"],
            parameters["platform_account_id"]
        )


    @staticmethod
    def _handle_spotify_previous_song(parameters: Dict):
        """
        Redis-based Previous Song Implementation.
        Strictly toggles between Current and Previous song in history.
        """
        adapter = MusicActionService._get_spotify_adapter(parameters)
        p_id = parameters.get("platform_account_id")

        if not p_id:
            return adapter.previous_track()

        key = f"spotify:history:{p_id}"
        history = redis_client.lrange(key, 0, -1) # Returns list [current, previous]

        logger.info(f"Handling previous_song. History: {history}")

        if len(history) < 2:
            # Case 1: No previous history. Restart current.
            logger.info("No previous history found. Restarting current track.")
            adapter.restart_current_track()
            return "Restarting the song."
        
        # Case 2: We have history [Current, Previous]
        # We want to play Previous.
        previous_uri = history[1]
        
        # Play it
        adapter.play(uris=[previous_uri])
        
        # Swap in Redis to support toggling
        redis_client.delete(key)
        redis_client.lpush(key, history[0]) 
        redis_client.lpush(key, previous_uri)
        
        logger.info(f"Toggled previous song. New History: {redis_client.lrange(key, 0, -1)}")
        
        return "Playing previous song."

    @staticmethod
    def get_action_keys(platform: str) -> list:
        """
        Returns a list of supported action keys for the given platform.
        """
        return list(MusicActionService.ACTION_TO_CAPABILITY.keys())

    ACTION_TO_CAPABILITY = {
        # Playback
        "pause_song": "playback_control",
        "resume_song": "playback_control",
        "skip_song": "playback_control",
        "previous_song": "playback_control",
        "restart_song": "playback_control",
        "skip_time": "playback_control",
        "change_volume": "playback_control",
        "get_volume": "playback_control",

        
        # Playlist
        "create_playlist": "playlist_creation",
        "delete_playlist": "playlist_management",
        "add_to_playlist": "playlist_management",
        "remove_from_playlist": "playlist_management",
        "reorder_playlist": "playlist_management",
        
        # Library
        "like_song": "favorites_management",
        "remove_from_liked_songs": "favorites_management",
        "play_liked_songs": "favorites_management",

        # Search / Play
        "play_song": "search",
        "play_song_by_artist": "search",
        "play_song_by_movie": "search",
        "play_playlist_by_name": "search",
        
        # Meta
        "get_current_song": "real_time_control"
    }

    @staticmethod
    def perform_music_action(action: str, platform: str, parameters: Dict = {}) -> str:
        try:
            # --- CAPABILITY CHECK ---
            required_cap = MusicActionService.ACTION_TO_CAPABILITY.get(action)
            if required_cap:
                # Resolve capabilities
                caps = {}
                if platform == "spotify":
                    caps = SpotifyAdapter.get_capabilities()
                elif platform == "soundcloud":
                    caps = SoundCloudAdapter.get_capabilities()
                
                if not caps.get(required_cap, False):
                    # Capability missing!
                    formatted_platform = "SoundCloud" if platform == "soundcloud" else "Spotify"
                    return f"I'm sorry, but {formatted_platform} does not support {action.replace('_', ' ')}."

            # --- DYNAMIC DISPATCH ---
            # Construct method name: _spotify_play_song, _soundcloud_pause_song
            method_name = f"_{platform}_{action}"
            
            if hasattr(MusicActionService, method_name):
                method = getattr(MusicActionService, method_name)
                logger.info("Executing action '%s' on platform '%s' via %s", action, platform, method_name)
                return method(parameters)
            else:
                # Fallback or Error
                logger.warning(f"Action '{action}' (method: {method_name}) is not implemented for platform '{platform}'.")
                return "Platform not yet supported."
            
        except NoActiveDeviceException:
            logger.warning("Action failed: No active Spotify device found.")
            raise DeviceNotFoundException("No active Spotify device found. Please open Spotify on a device and play a song.")
        
        except SpotifyException as e:
            logger.error(f"A Spotify API error occurred for action '{action}': {e}")
            
            # Extract HTTP status code
            from backend.utils.error_translator import extract_spotify_error_code
            error_code = extract_spotify_error_code(e)

            # FIX: Invalidate token if 401 (Unauthorized)
            if error_code == 401:
                db = parameters.get("db_session")
                account_id = parameters.get("platform_account_id")
                if db and account_id:
                    logger.warning(f"Spotify 401 Unauthorized. Invalidating token for account {account_id}.")
                    account = db.query(PlatformAccount).filter_by(id=account_id).first()
                    if account:
                        account.refresh_token = None
                        db.commit()
                # Raise Auth Error to redirect user
                raise AuthenticationError("Spotify authentication expired. Re-login required.")
            
            raise ExternalAPIError(
                message=f"Spotify API Error: {e.reason or str(e)}",
                error_code=error_code,
                platform="spotify",
                action=action
            )

        except requests.exceptions.HTTPError as e:
            # FIX: Handle SoundCloud 401 Unauthorized
            if e.response.status_code == 401:
                logger.error(f"SoundCloud 401 Unauthorized for action '{action}'. Invalidating token.")
                
                db = parameters.get("db_session")
                account_id = parameters.get("platform_account_id")
                if db and account_id:
                     account = db.query(PlatformAccount).filter_by(id=account_id).first()
                     if account:
                         account.refresh_token = None
                         db.commit()
                
                raise AuthenticationError("SoundCloud authentication expired. Re-login required.")
            
            # Re-raise other HTTP errors
            logger.error(f"HTTP Error for action '{action}': {e}")
            raise e
        
        except Exception as e:
            logger.error(f"An unexpected error occurred for action '{action}': {e}", exc_info=True)
            raise e