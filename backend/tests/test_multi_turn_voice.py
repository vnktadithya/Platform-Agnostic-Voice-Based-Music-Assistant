# backend/tests/test_voice_flow.py
from backend.services.session_manager import SessionManager

def test_multi_turn_voice_to_music_flow(monkeypatch, client, test_db, platform_account_fixture):
    """
    Simulates:
      - User says "play Imagine"
      - Then "skip this"
      - Then "add to playlist Road Trip"
    """

    # Patch STT and TTS services
    monkeypatch.setattr("backend.services.speech_to_text.SpeechToTextService.transcribe_audio", lambda audio: "play imagine")
    monkeypatch.setattr("backend.services.text_to_speech.TextToSpeechService.synthesize_speech", lambda text: "/path/to/fake_audio.wav")

    # Patch SpotifyAdapter methods
    monkeypatch.setattr("backend.adapters.spotify_adapter.SpotifyAdapter.play_track", lambda self, track_uri: True)
    monkeypatch.setattr("backend.adapters.spotify_adapter.SpotifyAdapter.skip_track", lambda self, track_uri: True)
    monkeypatch.setattr("backend.adapters.spotify_adapter.SpotifyAdapter.add_track_to_playlist", lambda self, playlist_id, track_uri: True)

    session_id = "test_voice_flow"

    # Step 1: User request "play imagine"
    resp1 = client.post("/v1/chat/process_voice", files={"audio": ("fake.wav", b"fake-bytes", "audio/wav")}, params={"session_id": session_id, "platform": "spotify", "platform_account_id": 1})
    assert resp1.status_code == 200
    assert SessionManager.get_session_state(session_id)  # should save some context

    # Step 2: Next turn "skip this"
    monkeypatch.setattr("backend.services.speech_to_text.SpeechToTextService.transcribe_audio", lambda audio: "skip this")
    resp2 = client.post("/v1/chat/process_voice", files={"audio": ("fake.wav", b"fake-bytes", "audio/wav")}, params={"session_id": session_id, "platform": "spotify", "platform_account_id": 1})
    assert resp2.status_code == 200

    # Step 3: Next turn "add to playlist Road Trip"
    monkeypatch.setattr("backend.services.speech_to_text.SpeechToTextService.transcribe_audio", lambda audio: "add to playlist Road Trip")
    resp3 = client.post("/v1/chat/process_voice", files={"audio": ("fake.wav", b"fake-bytes", "audio/wav")}, params={"session_id": session_id, "platform": "spotify", "platform_account_id": 1})
    assert resp3.status_code == 200
