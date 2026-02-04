import pytest
from backend.services.dialog_manager import DialogManager
from backend.services.session_manager import SessionManager

@pytest.fixture
def fake_db():
    class DummyDB:
        def rollback(self):
            pass
        def commit(self):
            pass
        def add(self, obj):
            pass
    return DummyDB()

@pytest.fixture
def dialog(fake_db):
    return DialogManager(fake_db, session_id="sess1", platform="spotify", platform_account_id=1)

# Stub MusicActionService for testing logic without unexpected calls
class FakeMusicActionService:
    ACTION_TO_CAPABILITY = {"play_song": "playback_control"}
    @staticmethod
    def get_action_map(platform, parameters=None):
        # Simulate a minimal action map
        return {
            "play_song": lambda: {
                "executed": True,
                "executed_action": "play_song",
                "parameters": parameters
            }
        }

    @staticmethod
    def get_action_keys(platform="spotify"):
        return ["play_song"]

    @staticmethod
    def perform_music_action(action, platform, complete_params):
        # Simulate how the real service would look up and run the action
        action_map = FakeMusicActionService.get_action_map(platform, complete_params)
        if action not in action_map:
            raise ValueError(f"Unknown action: {action}")
        return action_map[action]()


@pytest.mark.asyncio
async def test_chitchat_when_llm_returns_no_action(monkeypatch, dialog):
    monkeypatch.setattr("backend.services.dialog_manager.call_llm_agent",
                        lambda *a, **k: {"actions": [], "reply": "Just chatting"})
    monkeypatch.setattr("backend.services.dialog_manager.MusicActionService", FakeMusicActionService)

    resp = await dialog.process_request("Hello")
    # No actions means no execution
    assert "reply" in resp
    assert "Just chatting" in resp["reply"]

@pytest.mark.asyncio
async def test_missing_params_triggers_pending(monkeypatch, dialog):
    monkeypatch.setattr("backend.services.dialog_manager.call_llm_agent",
                        lambda *a, **k: {"actions": [{"action": "play_song", "parameters": {}}], "reply": "Which song?"})
    monkeypatch.setattr("backend.services.dialog_manager.MusicActionService", FakeMusicActionService)

    resp = await dialog.process_request("play something")
    assert resp["status"] == "PENDING_INPUT"
    ctx = SessionManager.get_pending_context("sess1")
    assert ctx["pending_action"] == "play_song"

@pytest.mark.asyncio
async def test_merges_context_and_executes(monkeypatch, dialog):
    # First turn: incomplete
    monkeypatch.setattr("backend.services.dialog_manager.call_llm_agent",
                        lambda *a, **k: {"actions": [{"action": "play_song", "parameters": {}}], "reply": "Need song name"})
    monkeypatch.setattr("backend.services.dialog_manager.MusicActionService", FakeMusicActionService)
    await dialog.process_request("play something")

    # Second turn: provide missing param
    def fake_llm(*a, **k):
        return {"actions": [{"action": "play_song", "parameters": {"song_name": "Halo"}}], "reply": "Playing Halo"}
    monkeypatch.setattr("backend.services.dialog_manager.call_llm_agent", fake_llm)

    resp = await dialog.process_request("play Halo")
    # After slot filling completes, action should succeed
    assert "Halo" in resp.get("reply", "")

@pytest.mark.asyncio
async def test_history_is_logged(monkeypatch, dialog):
    monkeypatch.setattr("backend.services.dialog_manager.call_llm_agent",
                        lambda *a, **k: {"actions": [], "reply": "Okay"})
    monkeypatch.setattr("backend.services.dialog_manager.MusicActionService", FakeMusicActionService)

    await dialog.process_request("Hello again")
    hist = SessionManager.get_turn_history("sess1")
    assert hist[-1]["role"] == "assistant"
    assert "Okay" in hist[-1]["text"]
