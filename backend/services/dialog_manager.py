import logging
from sqlalchemy.orm import Session
from backend.services.LLM_service import call_gemini_agent
from backend.services.music_action_service import MusicActionService
from backend.services.session_manager import SessionManager
from backend.utils.action_params import ACTION_REQUIRED_PARAMS
from backend.adapters.spotify_adapter import SpotifyAdapter
from backend.services.data_sync_service import get_valid_spotify_access_token
from backend.models.database_models import PlatformAccount, InteractionLog
from backend.utils.action_fallbacks import ACTION_FALLBACK_MAP

logger = logging.getLogger(__name__)

class DialogManager:
    def __init__(self, db: Session, session_id: str, platform: str = "spotify", platform_account_id: int = None):
        self.db = db
        self.session_id = session_id
        self.platform = platform.strip().lower()
        self.platform_account_id = platform_account_id
        self.session_manager = SessionManager()

    def normalize_action(self, raw_action: str, action_keys: list) -> str | None:
        if not raw_action:
            return None
        raw_action_lower = raw_action.lower()
        if raw_action_lower in action_keys:
            return raw_action_lower
        
        # fallback check only if not in action keys
        for canonical, alternatives in ACTION_FALLBACK_MAP.items():
            if raw_action_lower == canonical or raw_action_lower in alternatives:
                return canonical
        return None

    def _get_platform_credentials(self) -> dict:
        """
        Return credentials needed by the platform adapter, based on self.platform
        and self.platform_account_id.

        For spotify:
          { "platform": "spotify", "access_token": "<...>" }
        """
        
        if self.platform_account_id is not None:
            account = (
                self.db.query(PlatformAccount)
                .filter_by(id=self.platform_account_id)
                .first()
            )
            if not account:
                raise ValueError("Platform account not found")

            if self.platform == "spotify":
                access_token = get_valid_spotify_access_token(self.db, account)
                return {"platform": "spotify", "credentials" : {"access_token": access_token}}

            raise ValueError(f"Unsupported platform: {self.platform}")

        raise ValueError(
            f"Unsupported or invalid platform '{self.platform}'. "
            "Expected 'spotify'."
        )


    def _check_missing_params(self, action: str, parameters: dict) -> list:
        required_params = ACTION_REQUIRED_PARAMS.get(action, [])
        return [p for p in required_params if p not in parameters or not parameters[p]]

    def _handle_music_action(self, action: str, parameters: dict):
        complete_params = dict(parameters)
        complete_params["db_session"] = self.db
        complete_params["platform_account_id"] = self.platform_account_id

        logger.debug("_handle_music_action | platform=%s | platform_account_id=%s", self.platform, self.platform_account_id)

        creds = self._get_platform_credentials()

        if (
            not creds
            or "credentials" not in creds
            or "access_token" not in creds["credentials"]
        ):
            raise RuntimeError(
                f"Credential resolution failed for platform={self.platform}, "
                f"platform_account_id={self.platform_account_id}"
            )

        platform = creds.get("platform")
        access_token = creds["credentials"].get("access_token")

        if not access_token:
            raise RuntimeError("Resolved access_token is None — refusing to init adapter")


        # ---------- Spotify path ----------
        if platform == "spotify":
            complete_params["access_token"] = access_token
            adapter = SpotifyAdapter(access_token=access_token)
            current_user = adapter.sp.current_user()
            complete_params["user_id"] = current_user["id"]

        else:
            raise ValueError(f"Unsupported platform: {platform}")

        logger.debug(f"Action: {action}, Parameters sent to MusicActionService: {complete_params}")
        return MusicActionService.perform_music_action(action, platform, complete_params)
    
    def _log_interaction(self, user_input: str, llm_response: dict, final_action: str | None):
        """
        Persist a single user ↔ LLM interaction for future analysis / fine-tuning.
        Logging must NEVER break the user flow.
        """
        try:
            log = InteractionLog(
                platform_account_id=self.platform_account_id,
                session_id=self.session_id,
                user_input=user_input,
                llm_response=llm_response,
                final_action=final_action
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to log interaction: {e}")


    def process_request(self, user_input: str):
        action_keys = MusicActionService.get_action_keys(platform=self.platform)

        # Get pending context (this clears pending state by design)
        pending_context = self.session_manager.get_pending_context(self.session_id)

        # Build an LLM prompt that includes recent history
        turns = self.session_manager.get_turn_history(self.session_id)
        if turns:
            history_text = " | ".join([f"{m['role']}: {m['text']}" for m in turns])
            prompt_input = f"Conversation so far: {history_text}\nUser now: {user_input}"
        else:
            prompt_input = user_input

        merged_parameters = {}
        if pending_context:
            merged_parameters = {**pending_context["pending_parameters"]}
            original_action = pending_context["pending_action"]
            prompt_input += (
                f"\nPreviously, the user wanted '{original_action}' with partial details {merged_parameters}. "
                f"Use the new message to complete any missing details."
            )

        nlp_result = call_gemini_agent(prompt_input, action_keys=action_keys)
        logger.debug(f"LLM returned: {nlp_result}")

        actions = nlp_result.get("actions", [])
        final_reply = nlp_result.get("reply", "Sorry, I'm not sure how to help with that.")

        # Record turns in history (after computing reply for symmetry)
        self.session_manager.add_turn_history(self.session_id, role="user", text=user_input)
        self.session_manager.add_turn_history(self.session_id, role="assistant", text=final_reply)

        if not actions:
            logger.warning("LLM returned no actions. Treating as chit-chat/slot-filling.")
            return {"reply": final_reply, "executed": False}

        overall_results = []
        pending_action_info = None  # To save all context if we hit missing params in any action
        final_action_executed = None

        for i, act_entry in enumerate(actions):
            # Normalize action key and merge parameters with any pending/fallback as needed
            raw_action = act_entry.get("action")
            action = self.normalize_action(raw_action, action_keys)
            params = {**merged_parameters, **act_entry.get("parameters", {})}
            logger.info("Executing action '%s' for platform_account_id=%s", action, self.platform_account_id)

            if not action:
                logger.warning(f"LLM returned an invalid or null action: '{raw_action}'. Skipping.")
                continue

            # Validate required parameters (slot filling)
            missing_params = self._check_missing_params(action, params)
            if missing_params:
                logger.info(f"Action '{action}' missing parameters: {missing_params}")
                # Save pending with merged parameters + explicitly store missing list for resumption
                pending_action_info = {
                    "pending_action": action,
                    "pending_parameters": params,
                    "missing_params": missing_params
                }
                break  # Stop further action execution on slot fill

            try:
                result = self._handle_music_action(action, params)
                overall_results.append(result)

                # Optionally clear just the slot-filling context, not turn history
                final_action_executed = action
                self.session_manager.clear_session_state(self.session_id)
            except Exception as e:
                logger.error(f"Execution of action '{action}' failed: {e}")
                overall_results.append({"error": str(e), "action": action})

        # If missing parameters were found in any action, save state and exit early
        if pending_action_info:
            self.session_manager.save_pending_context(
                self.session_id,
                pending_action_info['pending_action'],
                pending_action_info['pending_parameters'],
                pending_action_info['missing_params']
            )
            response = {
                "reply": f"Please provide: {pending_action_info['missing_params'][0]} for action {pending_action_info['pending_action']}.",
                "executed": False,
                "status": "PENDING_INPUT"
            }

            self._log_interaction(
                user_input=user_input,
                llm_response=response,
                final_action=pending_action_info["pending_action"]
            )

            return response

        self._log_interaction(
            user_input=user_input,
            llm_response=nlp_result,
            final_action=final_action_executed
        )

        return nlp_result
