import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.session_manager import SessionManager
import json

client = TestClient(app)

# Use existing spotify patch if needed, or define local one
@pytest.fixture(autouse=True)
def patch_spotify(monkeypatch):
    class MockSpotifyAdapter:
        def __init__(self, access_token): pass
        def fetch_liked_tracks(self, *args, **kwargs): return []
    monkeypatch.setattr("backend.adapters.spotify_adapter.SpotifyAdapter", MockSpotifyAdapter)
    yield

def test_sequencing_logic(monkeypatch):
    """
    Ensures that music commands return deferred actions with 'AFTER_TTS' timing,
    not immediate server-side execution.
    """
    
    # Mock LLM to return a play command
    def fake_llm(prompt_input, voice_emotion=None, action_keys=None):
        return {
            "action": "play_song",
            "parameters": {"song_name": "Blinding Lights"},
            "reply": "Playing Blinding Lights now."
        }
    monkeypatch.setattr("backend.services.LLM_service.call_llm_agent", fake_llm)

    payload = {
        "text": "Play Blinding Lights",
        "platform": "spotify", 
        "session_id": "test-sequencing-sess",
        "platform_account_id": 1 
    }

    # Simulate request with valid payload
    
    response = client.post("/v1/chat/process_text?platform=spotify", json=payload)
    
    assert response.status_code == 200, f"Response text: {response.text}"
    res_json = response.json()
    
    # Validate payload structure for client-side sequencing
    command = res_json.get("command", {})
    
    # Validate timing and execution state
    assert command.get("timing") == "AFTER_TTS", f"Expected AFTER_TTS, got {command.get('timing')}"
    assert "deferred_actions" not in res_json, "Refactored API should not have 'deferred_actions' key."
    assert res_json.get("executed") is False, "Should be deferred, not executed server-side."
    
    # Verify action details
    assert command.get("action") == "play_song"
    assert command.get("parameters", {}).get("song_name") == "Blinding Lights"
