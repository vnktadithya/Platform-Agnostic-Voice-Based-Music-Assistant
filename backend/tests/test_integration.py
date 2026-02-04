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

    def fake_call_llm(prompt_input, short_reply=True, action_keys=None):
        if calls["count"] == 0:
            calls["count"] += 1
            return {"actions": [{"action": "play_song", "parameters": {}}], "reply": "Need song name"}
        return {"actions": [{"action": "play_song", "parameters": {"song_name": "Halo"}}], "reply": "Playing Halo"}

    monkeypatch.setattr("backend.services.dialog_manager.call_llm_agent", fake_call_llm)

    # --- First request ---
    resp1 = client.post("/v1/chat/process_text?platform=spotify", json={"text": "play something", "session_id": "sess-integration", "platform_account_id": 1, "platform": "spotify"})
    data1 = resp1.json()
    assert data1["status"] == "PENDING_INPUT"
    ctx = SessionManager.get_pending_context("sess-integration")
    assert ctx["pending_action"] == "play_song"

    # --- Second request ---
    resp2 = client.post("/v1/chat/process_text?platform=spotify", json={"text": "play Halo", "session_id": "sess-integration", "platform_account_id": 1, "platform": "spotify"})
    data2 = resp2.json()
    # Should succeed after slot filling
    assert data2.get("status") != "PENDING_INPUT"
    assert "Halo" in data2.get("reply", "")


def test_session_isolation(monkeypatch):
    """
    Ensure multiple users do not share session state in Redis.
    """

    def fake_llm(prompt_input, short_reply=True, action_keys=None):
        return {"actions": [{"action": "play_song", "parameters": {"song_name": "Halo"}}], "reply": "Playing Halo"}

    monkeypatch.setattr("backend.services.dialog_manager.call_llm_agent", fake_llm)

    resp1 = client.post("/v1/chat/process_text?platform=spotify", json={"text": "play Halo", "session_id": "userA", "platform_account_id": 1, "platform": "spotify"})
    resp2 = client.post("/v1/chat/process_text?platform=spotify", json={"text": "play Shape of You", "session_id": "userB", "platform_account_id": 1, "platform": "spotify"})

    assert "Halo" in resp1.json()["reply"]
    # Session isolation means different inputs should not affect each other
    assert resp1.json()["session_id"] != resp2.json()["session_id"]


def test_graceful_failure_on_spotify(monkeypatch):
    """
    If Spotify API fails, the system should respond gracefully and not crash.
    """

    def fake_llm(prompt_input, short_reply=True, action_keys=None):
        return {"actions": [{"action": "pause_song", "parameters": {}}], "reply": "Pausing"}

    monkeypatch.setattr("backend.services.dialog_manager.call_llm_agent", fake_llm)

    # Mock MusicActionService to raise exception during action execution
    async def failing_action_handler(self, action, params):
        raise Exception("Spotify API is down")
    
    monkeypatch.setattr("backend.services.dialog_manager.DialogManager._handle_music_action", failing_action_handler)

    resp = client.post("/v1/chat/process_text?platform=spotify", json={"text": "pause", "session_id": "sess-fail", "platform_account_id": 1, "platform": "spotify"})
    data = resp.json()

    # Graceful failure: should return error outcome
    assert data["action_outcome"] == "ERROR" or "error" in data["reply"].lower()