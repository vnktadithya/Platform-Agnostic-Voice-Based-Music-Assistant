# This maps each executable action to a list of parameters the LLM MUST extract.
# We will use this to validate the LLM's output.
ACTION_REQUIRED_PARAMS = {
    "play_song": ["song_name"],
    "add_to_playlist": ["song_name", "playlist_name"],
    "remove_from_playlist": ["song_name", "playlist_name"],
    "create_playlist": ["playlist_name"],
    "delete_playlist": ["playlist_name"],
    "play_song_by_artist": ["artist"],
    "play_song_by_movie": ["movie_name"],
    "seek_time": ["seconds"],
    "recommend_by_mood": ["mood"]
}