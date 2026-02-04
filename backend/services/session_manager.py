import json
from backend.configurations.redis_client import redis_client

SESSION_TTL_SECONDS = 3600 # 1 hour
MAX_HISTORY_MESSAGES = 10  # keep last 10 messages (≈ 5 user/bot turns)

class SessionManager:
    @staticmethod
    def save_session_state(session_id: str, state: dict):
        """Saves session ephemeral state as a dict."""
        key = f"session:{session_id}"
        redis_client.setex(key, SESSION_TTL_SECONDS, json.dumps(state))

    @staticmethod
    def update_session_state(session_id: str, updates: dict):
        """Updates part of the session state, preserving the rest."""
        state = SessionManager.get_session_state(session_id) or {}
        state.update(updates)
        SessionManager.save_session_state(session_id, state)

    @staticmethod
    def get_session_state(session_id: str, clear: bool = False):
        """Retrieves (optionally clears) the session state dict."""
        key = f"session:{session_id}"
        value = redis_client.get(key)
        if value:
            if clear:
                redis_client.delete(key)
            return json.loads(value)
        return {}

    @staticmethod
    def clear_session_state(session_id: str):
        key = f"session:{session_id}"
        redis_client.delete(key)

    # ---------- Pending context (unchanged behavior: clears after read) ----------
    @staticmethod
    def save_pending_context(session_id: str, action: str, parameters: dict, missing: list = None):
        state = {"pending_action": action, "pending_parameters": parameters, "missing_params": missing or []}
        SessionManager.save_session_state(session_id, state)

    @staticmethod
    def get_pending_context(session_id: str):
        state = SessionManager.get_session_state(session_id, clear=True)
        if "pending_action" in state and "pending_parameters" in state:
            return {"pending_action": state["pending_action"], "pending_parameters": state["pending_parameters"], "missing_params": state.get("missing_params", [])}
        return None
    
    # ---------- Conversation history (separate Redis key) ----------
    @staticmethod
    def _history_key(session_id: str) -> str:
        return f"session:{session_id}:history"

    @staticmethod
    def add_turn_history(session_id: str, role: str, text: str):
        """
        Append a new message to conversation history.
        role: "user" or "assistant"
        """
        hk = SessionManager._history_key(session_id)
        entry = json.dumps({"role": role, "text": text})
        redis_client.rpush(hk, entry)
        # keep only the last N messages
        redis_client.ltrim(hk, -MAX_HISTORY_MESSAGES, -1)
        # refresh TTL so the history expires like the state
        redis_client.expire(hk, SESSION_TTL_SECONDS)

    @staticmethod
    def get_turn_history(session_id: str, limit: int = MAX_HISTORY_MESSAGES):
        """
        Return the last `limit` messages as a list of dicts: [{"role": "...", "text": "..."}]
        """
        hk = SessionManager._history_key(session_id)
        raw = redis_client.lrange(hk, -limit, -1) or []
        history = []
        for item in raw:
            try:
                s = item.decode("utf-8") if isinstance(item, (bytes, bytearray)) else item
                history.append(json.loads(s))
            except Exception:
                pass
        return history

    @staticmethod
    def clear_turn_history(session_id: str):
        hk = SessionManager._history_key(session_id)
        redis_client.delete(hk)