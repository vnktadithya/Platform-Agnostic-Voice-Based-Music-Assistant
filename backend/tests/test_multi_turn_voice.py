# backend/tests/test_voice_flow.py
from backend.services.session_manager import SessionManager

def test_multi_turn_voice_to_music_flow(monkeypatch, client, test_db, platform_account_fixture):
    """
    Simulates:
      - User says "play Imagine"
      - Then "skip this"
      - Then "add to playlist Road Trip"
    """

    # 🧩 Patch STT + TTS to avoid real API calls
    monkeypatch.setattr("backend.services.speech_to_text_service.SpeechToTextService.transcribe", lambda audio: "play imagine")
    monkeypatch.setattr("backend.services.text_to_speech_service.TextToSpeechService.speak", lambda text: b"fake-audio")

    # 🧩 Patch SpotifyAdapter to avoid real Spotify
    monkeypatch.setattr("backend.adapters.spotify_adapter.SpotifyAdapter.play_track", lambda self, track_uri: True)
    monkeypatch.setattr("backend.adapters.spotify_adapter.SpotifyAdapter.skip_track", lambda self: True)
    monkeypatch.setattr("backend.adapters.spotify_adapter.SpotifyAdapter.add_track_to_playlist", lambda self, playlist_id, track_uri: True)

    session_id = "test_voice_flow"

    # 1️⃣ User says "play imagine"
    resp1 = client.post("/voice/command", json={"session_id": session_id, "audio": "fake-bytes"})
    assert resp1.status_code == 200
    assert SessionManager.get_session_state(session_id)  # should save some context

    # 2️⃣ Next turn: "skip this"
    monkeypatch.setattr("backend.services.speech_to_text_service.SpeechToTextService.transcribe", lambda audio: "skip this")
    resp2 = client.post("/voice/command", json={"session_id": session_id, "audio": "fake-bytes"})
    assert resp2.status_code == 200

    # 3️⃣ Next turn: "add to playlist Road Trip"
    monkeypatch.setattr("backend.services.speech_to_text_service.SpeechToTextService.transcribe", lambda audio: "add to playlist Road Trip")
    resp3 = client.post("/voice/command", json={"session_id": session_id, "audio": "fake-bytes"})
    assert resp3.status_code == 200
