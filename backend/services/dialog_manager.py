import logging
from sqlalchemy.orm import Session
from backend.services.LLM_service import call_mistral_agent
from backend.services.music_action_service import MusicActionService
from backend.services.session_manager import SessionManager
from backend.utils.action_params import ACTION_REQUIRED_PARAMS
from backend.adapters.spotify_adapter import SpotifyAdapter
from backend.utils.dev_token_manager import DevSpotifyTokenManager
from backend.services.data_sync_service import get_new_access_token
from backend.models.database_models import PlatformAccount

logger = logging.getLogger(__name__)

class DialogManager:
    def __init__(self, db: Session, session_id: str, platform: str = "spotify", platform_account_id: int = None):
        self.db = db
        self.session_id = session_id
        self.platform = platform
        self.platform_account_id = platform_account_id
        self.session_manager = SessionManager()

    def _get_access_token(self):
        if self.platform_account_id:
            account = self.db.query(PlatformAccount).filter_by(id=self.platform_account_id).first()
            if not account:
                raise ValueError("Platform account not found")
            if not account.refresh_token:
                raise ValueError("No refresh token available for this account")
            
            access_token = get_new_access_token(account.refresh_token)
            if not access_token:
                raise ValueError("Failed to obtain access token from refresh token")
            return access_token
        else:
            # fallback for dev / testing
            dev_token = DevSpotifyTokenManager.get_access_token()
            if not dev_token:
                raise ValueError("No platform_account_id provided and no dev token available")
            return dev_token

    def _check_missing_params(self, action: str, parameters: dict) -> list:
        required_params = ACTION_REQUIRED_PARAMS.get(action, [])
        return [p for p in required_params if p not in parameters or not parameters[p]]

    def _handle_music_action(self, action: str, parameters: dict):
        complete_params = dict(parameters)
        complete_params["db_session"] = self.db
        complete_params["access_token"] = self._get_access_token()
        complete_params["platform_account_id"] = self.platform_account_id
        logger.debug("Using access_token ending with: %s", complete_params["access_token"][-5:])
        adapter = SpotifyAdapter(access_token=complete_params["access_token"])

        if action == "recommend_by_mood":
            liked_tracks = adapter.fetch_liked_tracks(limit=50)
            complete_params["tracks"] = liked_tracks

        return MusicActionService.perform_music_action(action, complete_params, self.platform)

    def process_request(self, user_input: str, voice_emotion: str = None):
        action_keys = MusicActionService.get_action_keys(platform=self.platform)

        # get pending context (this clears pending state by design)
        pending_context = self.session_manager.get_pending_context(self.session_id)

        # build an LLM prompt that includes recent history
        turns = self.session_manager.get_turn_history(self.session_id)
        if turns:
            history_text = " | ".join([f"{m['role']}: {m['text']}" for m in turns])
            prompt_input = f"Conversation so far: {history_text}\nUser now: {user_input}"
        else:
            prompt_input = user_input

        merged_parameters = {}
        if pending_context:
            # merge parameters that were collected earlier
            merged_parameters = {**pending_context["pending_parameters"]}
            original_action = pending_context["pending_action"]
            prompt_input += (
                f"\nPreviously, the user wanted '{original_action}' with partial details {merged_parameters}. "
                f"Use the new message to complete any missing details."
            )

        nlp_result = call_mistral_agent(prompt_input, voice_emotion, action_keys=action_keys)

        action = nlp_result.get("action")
        parameters = {**merged_parameters, **nlp_result.get("parameters", {})}
        reply = nlp_result.get("reply", "Sorry, I'm not sure how to help with that.")

        # record turns in history (after we compute reply for symmetry)
        self.session_manager.add_turn_history(self.session_id, role="user", text=user_input)
        self.session_manager.add_turn_history(self.session_id, role="assistant", text=reply)

        # unknown/invalid action -> chit-chat
        if not action or action not in action_keys:
            logger.warning(f"LLM returned an invalid or null action: '{action}'. Treating as chit-chat.")
            return {"reply": reply, "executed": False}

        # validate required parameters (slot filling)
        missing_params = self._check_missing_params(action, parameters)
        if missing_params:
            logger.info(f"Action '{action}' pending; missing parameters: {missing_params}")
            # save pending with merged parameters + explicitly store missing list
            self.session_manager.save_pending_context(self.session_id, action, parameters, missing_params)
            return {"reply": reply, "executed": False, "status": "PENDING_INPUT"}

        # execute action
        try:
            result = self._handle_music_action(action, parameters)
            # clear only the structured state; keep history for continuity (will expire via TTL)
            self.session_manager.clear_session_state(self.session_id)
            return {"reply": reply, "executed": True, "result": result}
        except Exception as e:
            logger.error(f"Execution of action '{action}' failed: {e}")
            return {"reply": str(e), "executed": False}
