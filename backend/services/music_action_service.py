import logging
from typing import Dict
from backend.adapters.spotify_adapter import SpotifyAdapter, NoActiveDeviceException
from spotipy.exceptions import SpotifyException

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
    def get_action_map(platform: str, parameters: Dict = {}) -> Dict[str, callable]:
        if platform == "spotify":

            def build_artist_query() -> tuple[str, str | None, str | None]:
                song = parameters.get("song_name", "")
                artist = parameters.get("artist", "") or parameters.get("artist_name", "")
                if song and artist:
                    query = f'track:"{song}" artist:"{artist}"'
                    return query, song, artist
                
                return artist or song, song or None, artist or None

            query_qa, q_song, q_artist = build_artist_query()


            return {
                "play_song": lambda: MusicActionService._get_spotify_adapter(parameters).play_by_query(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    parameters.get("song_name", "")
                ),
                "play_song_by_artist": lambda: MusicActionService._get_spotify_adapter(parameters).play_by_query(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    query_qa,
                    song_name = q_song,
                    artist_name = q_artist,
                    use_cache = True
                ),
                "play_song_by_movie": lambda: MusicActionService._get_spotify_adapter(parameters).play_by_query(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    parameters.get("movie_name", "")
                ),
                "play_playlist_by_name": lambda: MusicActionService._get_spotify_adapter(parameters).play_playlist_by_name(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    parameters.get("playlist_name", "")
                ),
                "get_current_song": lambda: MusicActionService._get_spotify_adapter(parameters).get_currently_playing_song(),

                # === Playback controls ===
                "pause_song": lambda: MusicActionService._get_spotify_adapter(parameters).pause(),
                "resume_song": lambda: MusicActionService._get_spotify_adapter(parameters).resume(),
                "skip_song": lambda: MusicActionService._get_spotify_adapter(parameters).skip_current_track(),
                "previous_song": lambda: MusicActionService._get_spotify_adapter(parameters).previous_track(),
                "restart_song": lambda: MusicActionService._get_spotify_adapter(parameters).restart_current_track(),
                "skip_time": lambda: MusicActionService._get_spotify_adapter(parameters).seek_position(parameters.get("seconds", 0)),

                # === Liked songs ===
                "like_song": lambda: MusicActionService._get_spotify_adapter(parameters).add_current_to_favorites(
                    parameters["db_session"],
                    parameters["platform_account_id"]
                ),
                "remove_from_liked_songs": lambda: MusicActionService._get_spotify_adapter(parameters).remove_current_from_favorites(
                    parameters["db_session"],
                    parameters["platform_account_id"]
                ),
                "play_liked_songs": lambda: MusicActionService._get_spotify_adapter(parameters).play_liked_songs(
                    parameters["db_session"],
                    parameters["platform_account_id"]
                ),

                # === Playlist management ===
                "create_playlist": lambda: MusicActionService._get_spotify_adapter(parameters).create_playlist(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    parameters.get("user_id"),
                    parameters.get("playlist_name")
                ),
                "delete_playlist": lambda: MusicActionService._get_spotify_adapter(parameters).delete_user_playlist(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    parameters.get("playlist_name")
                ),

                "add_to_playlist": lambda: MusicActionService._get_spotify_adapter(parameters).add_tracks_to_playlist(
                    MusicActionService._get_spotify_adapter(parameters).resolve_playlist_id(
                        parameters["db_session"], 
                        parameters["platform_account_id"], 
                        parameters.get("playlist_name", "")
                    ),
                    MusicActionService._get_spotify_adapter(parameters).search_track_uris(
                        parameters["db_session"],
                        parameters["platform_account_id"],
                        parameters.get("song_name", ""),
                        limit=5)
                    ),

                "remove_from_playlist": lambda: MusicActionService._get_spotify_adapter(parameters).remove_tracks_from_playlist(
                    MusicActionService._get_spotify_adapter(parameters).resolve_playlist_id(
                        parameters["db_session"],
                        parameters["platform_account_id"],
                        parameters.get("playlist_name", "")
                    ),
                    MusicActionService._get_spotify_adapter(parameters).search_track_uris(
                        parameters["db_session"],
                        parameters["platform_account_id"],
                        parameters.get("song_name", ""),
                        limit=5
                    )
                ),

                "reorder_playlist": lambda: MusicActionService._get_spotify_adapter(parameters).reorder_playlist_tracks(
                    parameters.get("playlist_id"),
                    parameters.get("range_start", 0),
                    parameters.get("insert_before", 0)
                )
            }

        return {
            "fallback": lambda: "Platform not yet supported."
        }

    @staticmethod
    def get_action_keys(platform: str) -> list:
        return list(MusicActionService.get_action_map(platform).keys())

    @staticmethod
    def perform_music_action(action: str, platform: str, parameters: Dict = {}) -> str:
        try:
            action_map = MusicActionService.get_action_map(platform, parameters)
            if action in action_map:
                logger.info("Executing action '%s' on platform '%s'", action, platform)
                return action_map[action]()
            else:
                # This case is handled by the DialogManager, but we keep a log here for safety.
                logger.warning(f"Action '{action}' is not defined in the action map for platform '{platform}'.")
                return None
            
        except NoActiveDeviceException:
            logger.warning("Action failed: No active Spotify device found.")
            raise NoActiveDeviceException("To do that, please open Spotify on one of your devices and play a song first.")
        
        except SpotifyException as e:
            logger.error(f"A Spotify API error occurred for action '{action}': {e}")
            raise Exception(f"There was a problem with Spotify: {e.reason}")
        
        except Exception as e:
            logger.error(f"An unexpected error occurred for action '{action}': {e}", exc_info=True)
            raise Exception(f"An unexpected error occurred while performing '{action}'.")