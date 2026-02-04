ACTION_REQUIRED_PARAMS = {
    "play_song": ["song_name"],
    "add_to_playlist": ["song_name", "playlist_name"],
    "remove_from_playlist": ["song_name", "playlist_name"],
    "create_playlist": ["playlist_name"],
    "delete_playlist": ["playlist_name"],
    "play_song_by_artist": ["artist"],
    "play_song_by_movie": ["movie_name"],
    "skip_time": ["seconds"],
    "change_volume": ["volume?", "mode?"],
    "get_volume": [],

    "reorder_playlist": ["playlist_name", "range_start", "insert_before"]
}