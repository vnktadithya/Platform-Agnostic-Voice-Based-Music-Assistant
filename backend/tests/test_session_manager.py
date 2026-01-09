import sys
import os
from backend.services.session_manager import SessionManager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_save_and_get_pending_context():
    session_id = "test_session_1"
    action = "play_song"
    params = {"song_name": "Imagine"}

    # Save pending context
    SessionManager.save_pending_context(session_id, action, params)

    # Retrieve pending context
    context = SessionManager.get_pending_context(session_id)
    assert context is not None
    assert context["pending_action"] == action
    assert context["pending_parameters"] == params

    # Subsequent retrieval returns None (because Redis deletes after get)
    context2 = SessionManager.get_pending_context(session_id)
    assert context2 is None

def test_update_and_clear_session_state():
    session_id = "test_session_2"
    
    # Save arbitrary state
    SessionManager.save_session_state(session_id, {"step": 1})
    state = SessionManager.get_session_state(session_id)
    assert state == {"step": 1}
    
    # Update state
    SessionManager.update_session_state(session_id, {"step": 2, "extra": "data"})
    state_updated = SessionManager.get_session_state(session_id)
    assert state_updated == {"step": 2, "extra": "data"}
    
    # Clear state
    SessionManager.clear_session_state(session_id)
    state_cleared = SessionManager.get_session_state(session_id)
    assert state_cleared == {}

# ----- Testing the conversation history -----
def test_turn_history_append_and_get():
    sid = "hist1"
    SessionManager.add_turn_history(sid, "user", "hello")
    SessionManager.add_turn_history(sid, "assistant", "hi there")
    
    hist = SessionManager.get_turn_history(sid)
    assert len(hist) == 2
    assert hist[0]["role"] == "user"
    assert hist[1]["role"] == "assistant"
    assert hist[1]["text"] == "hi there"

def test_turn_history_trim_to_max(monkeypatch):
    sid = "hist2"
    # Force MAX_HISTORY_MESSAGES = 5 for test
    monkeypatch.setattr("backend.services.session_manager.MAX_HISTORY_MESSAGES", 5)
    for i in range(10):
        SessionManager.add_turn_history(sid, "user", f"msg{i}")

    hist = SessionManager.get_turn_history(sid)
    assert len(hist) == 5
    assert hist[0]["text"] == "msg5"   # oldest trimmed
    assert hist[-1]["text"] == "msg9"  # newest preserved

def test_clear_turn_history():
    sid = "hist3"
    SessionManager.add_turn_history(sid, "user", "something")
    SessionManager.clear_turn_history(sid)
    hist = SessionManager.get_turn_history(sid)
    assert hist == []

def test_history_ttl_expiry(monkeypatch):
    sid = "hist4"
    SessionManager.add_turn_history(sid, "user", "hi")
    
    # Simulate Redis TTL expiration by clearing manually
    SessionManager.clear_turn_history(sid)
    assert SessionManager.get_turn_history(sid) == []

