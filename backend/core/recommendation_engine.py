from typing import List, Dict, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# === Mood-to-Audio Feature Ranges ===
MOOD_AUDIO_FEATURES = {
    "happy": {"valence": (0.6, 1.0), "energy": (0.6, 1.0)},
    "sad": {"valence": (0.0, 0.4), "energy": (0.0, 0.5)},
    "calm": {"valence": (0.4, 0.7), "energy": (0.2, 0.5)},
    "angry": {"valence": (0.0, 0.4), "energy": (0.7, 1.0)},
    "romantic": {"valence": (0.6, 1.0), "energy": (0.3, 0.6)},
    "energetic": {"valence": (0.5, 1.0), "energy": (0.7, 1.0)}
}

def filter_by_mood(tracks: List[Dict], mood: str) -> List[Dict]:
    """
    Filter tracks based on audio features that match the user's mood.
    """
    if mood not in MOOD_AUDIO_FEATURES:
        return tracks  # fallback: return all if mood unknown

    valence_range = MOOD_AUDIO_FEATURES[mood].get("valence", (0.0, 1.0))
    energy_range = MOOD_AUDIO_FEATURES[mood].get("energy", (0.0, 1.0))

    filtered = []
    for track in tracks:
        valence = track.get("valence", 0.5)
        energy = track.get("energy", 0.5)

        if valence_range[0] <= valence <= valence_range[1] and \
           energy_range[0] <= energy <= energy_range[1]:
            filtered.append(track)
    return filtered

def score_track(track: Dict, mood: str) -> float:
    """
    Calculate a relevance score for a track based on its similarity to mood features.
    """
    mood_vec = np.array([
        np.mean(MOOD_AUDIO_FEATURES[mood].get("valence", [0.5])),
        np.mean(MOOD_AUDIO_FEATURES[mood].get("energy", [0.5]))
    ]).reshape(1, -1)

    track_vec = np.array([
        track.get("valence", 0.5),
        track.get("energy", 0.5)
    ]).reshape(1, -1)

    return cosine_similarity(mood_vec, track_vec)[0][0]

def recommend_tracks(mood: str, tracks: List[Dict], limit: int = 10) -> List[Dict]:
    """
    Main recommendation function: filters + scores + sorts + returns top N.
    """
    if not tracks:
        return []

    mood_filtered = filter_by_mood(tracks, mood)
    
    if not mood_filtered:
        mood_filtered = tracks  # fallback if filtering removes everything

    for track in mood_filtered:
        track["score"] = score_track(track, mood)

    ranked = sorted(mood_filtered, key=lambda x: x["score"], reverse=True)
    return ranked[:limit]
