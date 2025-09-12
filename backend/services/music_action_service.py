import logging
from typing import Dict
from backend.adapters.spotify_adapter import SpotifyAdapter, NoActiveDeviceException
from backend.core.recommendation_engine import recommend_tracks
from spotipy.exceptions import SpotifyException

logger = logging.getLogger(__name__)

class MusicActionService:
    @staticmethod
    def get_action_map(platform: str = "spotify", parameters: Dict = {}) -> Dict[str, callable]:
        if platform == "spotify":
            spotify = SpotifyAdapter(parameters.get("access_token"))

            return {
                # === Playback by metadata (needs db + account id) ===
                "play_song": lambda: spotify.play_by_query(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    parameters.get("song_name", "")
                ),
                "play_song_by_artist": lambda: spotify.play_by_query(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    parameters.get("artist", "")
                ),
                "play_song_by_movie": lambda: spotify.play_by_query(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    parameters.get("movie_name", "")
                ),
                "play_playlist_by_name": lambda: spotify.play_playlist_by_name(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    parameters.get("playlist_name", "")
                ),

                # === Playback controls ===
                "pause_song": spotify.pause,
                "resume_song": spotify.resume,
                "skip_song": spotify.skip_current_track,
                "previous_song": spotify.previous_track,
                "restart_song": spotify.restart_current_track,
                "skip_time": lambda: spotify.seek_position(parameters.get("seconds", 0)),

                # === Liked songs ===
                "like_song": lambda: spotify.add_current_to_favorites(
                    parameters["db_session"],
                    parameters["platform_account_id"]
                ),
                "remove_from_liked_songs": lambda: spotify.remove_current_from_favorites(
                    parameters["db_session"],
                    parameters["platform_account_id"]
                ),

                # === Playlist management ===
                "create_playlist": lambda: spotify.create_playlist(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    parameters.get("user_id"),
                    parameters.get("playlist_name")
                ),
                "delete_playlist": lambda: spotify.delete_user_playlist(
                    parameters["db_session"],
                    parameters["platform_account_id"],
                    parameters.get("playlist_id")
                ),
                "add_to_playlist": lambda: spotify.add_tracks_to_playlist(
                    spotify.resolve_playlist_id(
                        parameters["db_session"], 
                        parameters["platform_account_id"], 
                        parameters.get("playlist_name", "")
                    ),
                    parameters.get("uris", [])
                ),
                "remove_from_playlist": lambda: spotify.remove_tracks_from_playlist(
                    parameters.get("playlist_id"),
                    parameters.get("uris", [])
                ),
                "reorder_playlist": lambda: spotify.reorder_playlist_tracks(
                    parameters.get("playlist_id"),
                    parameters.get("range_start", 0),
                    parameters.get("insert_before", 0)
                ),

                # === Recommendations ===
                "recommend_by_mood": lambda: recommend_tracks(
                    parameters.get("mood"),
                    parameters.get("tracks", []),
                    parameters.get("limit", 10)
                )
            }

        return {
            "fallback": lambda: "Platform not yet supported."
        }

    @staticmethod
    def get_action_keys(platform: str = "spotify") -> list:
        return list(MusicActionService.get_action_map(platform).keys())

    @staticmethod
    def perform_music_action(action: str, parameters: Dict = {}, platform: str = "spotify") -> str:
        try:
            action_map = MusicActionService.get_action_map(platform, parameters)
            if action in action_map:
                logger.info(f"Executing action: '{action}' with params: {list(parameters.keys())}")
                return action_map[action]()
            else:
                # This case is now handled by the DialogManager, but we keep a log here for safety.
                logger.warning(f"Action '{action}' is not defined in the action map for platform '{platform}'.")
                return None
        except NoActiveDeviceException:
            logger.error("Action failed: No active Spotify device found.")
            raise NoActiveDeviceException("To do that, please open Spotify on one of your devices and play a song first.")
        except SpotifyException as e:
            logger.error(f"A Spotify API error occurred for action '{action}': {e}")
            raise Exception(f"There was a problem with Spotify: {e.reason}")
        except Exception as e:
            logger.error(f"An unexpected error occurred for action '{action}': {e}", exc_info=True)
            raise Exception(f"An unexpected error occurred while performing '{action}'.")