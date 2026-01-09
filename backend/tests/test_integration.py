import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.session_manager import SessionManager

client = TestClient(app)


# --- Spotify adapter mock helpers ---
class MockSpotifyAdapter:
    def __init__(self, access_token):
        self.access_token = access_token

    def fetch_liked_tracks(self, access_token, limit=50):
        return [{"name": "Halo"}]


@pytest.fixture(autouse=True)
def patch_spotify(monkeypatch):
    monkeypatch.setattr("backend.adapters.spotify_adapter.SpotifyAdapter", MockSpotifyAdapter)
    yield


# --- Integration Tests ---

def test_multi_turn_slot_filling(monkeypatch):
    """
    Simulate a user asking 'play something', LLM requests song name,
    then user replies 'play Halo', and execution succeeds.
    """

    # Stub LLM agent: first call missing params, second call has them
    calls = {"count": 0}

    def fake_call_mistral(prompt_input, voice_emotion=None, action_keys=None):
        if calls["count"] == 0:
            calls["count"] += 1
            return {"action": "play_song", "parameters": {}, "reply": "Need song name"}
        return {"action": "play_song", "parameters": {"song_name": "Halo"}, "reply": "Playing Halo"}

    monkeypatch.setattr("backend.services.dialog_manager.call_mistral_agent", fake_call_mistral)

    # --- First request ---
    resp1 = client.post("/v1/chat/process_text", json={"text": "play something", "session_id": "sess-integration"})
    data1 = resp1.json()
    assert data1["status"] == "PENDING_INPUT"
    ctx = SessionManager.get_pending_context("sess-integration")
    assert ctx["pending_action"] == "play_song"

    # --- Second request ---
    resp2 = client.post("/v1/chat/process_text", json={"text": "play Halo", "session_id": "sess-integration"})
    data2 = resp2.json()
    assert data2["executed"] is True
    assert data2["result"]["executed_action"] == "play_song"
    assert data2["result"]["parameters"]["song_name"] == "Halo"


def test_session_isolation(monkeypatch):
    """
    Ensure multiple users do not share session state in Redis.
    """

    def fake_llm(prompt_input, voice_emotion=None, action_keys=None):
        return {"action": "play_song", "parameters": {"song_name": "Halo"}, "reply": "Playing Halo"}

    monkeypatch.setattr("backend.services.dialog_manager.call_mistral_agent", fake_llm)

    resp1 = client.post("/v1/chat/process_text", json={"text": "play Halo", "session_id": "userA"})
    resp2 = client.post("/v1/chat/process_text", json={"text": "play Shape of You", "session_id": "userB"})

    assert "Halo" in resp1.json()["reply"]
    assert "Shape of You" in resp2.json()["reply"]
    assert resp1.json() != resp2.json()


def test_graceful_failure_on_spotify(monkeypatch):
    """
    If Spotify API fails, the system should respond gracefully and not crash.
    """

    class FailingSpotifyAdapter:
        def __init__(self, access_token): pass
        def fetch_liked_tracks(self, access_token, limit=50):
            raise Exception("Spotify down")

    monkeypatch.setattr("backend.adapters.spotify_adapter.SpotifyAdapter", FailingSpotifyAdapter)

    def fake_llm(prompt_input, voice_emotion=None, action_keys=None):
        return {"action": "recommend_by_mood", "parameters": {"mood": "happy"}, "reply": "Recommending"}

    monkeypatch.setattr("backend.services.dialog_manager.call_mistral_agent", fake_llm)

    resp = client.post("/v1/chat/process_text", json={"text": "recommend happy songs", "session_id": "sess-fail"})
    data = resp.json()

    assert data["executed"] is False
    assert "failed" in data["reply"].lower() or "error" in data["reply"].lower()