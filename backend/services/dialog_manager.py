import logging
import asyncio
import base64
from sqlalchemy.orm import Session
from backend.services.LLM_service import call_llm_agent
from backend.services.music_action_service import MusicActionService
from backend.services.text_to_speech import TextToSpeechService
from backend.services.session_manager import SessionManager
from backend.utils.action_params import ACTION_REQUIRED_PARAMS
from backend.adapters.spotify_adapter import SpotifyAdapter
from backend.services.data_sync_service import get_valid_spotify_access_token, get_valid_soundcloud_access_token
from backend.models.database_models import PlatformAccount, InteractionLog
from backend.utils.action_fallbacks import ACTION_FALLBACK_MAP
from backend.socket_manager import emit_state 
from backend.utils.custom_exceptions import ExternalAPIError, DeviceNotFoundException 
from backend.utils.error_translator import get_user_friendly_error_message

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
            
            if self.platform == "soundcloud":
                access_token = get_valid_soundcloud_access_token(self.db, account)
                return {"platform": "soundcloud", "credentials" : {"access_token": access_token}}

            raise ValueError(f"Unsupported platform: {self.platform}")

        raise ValueError(
            f"Unsupported or invalid platform '{self.platform}'. "
            "Expected 'spotify'."
        )


    def _check_missing_params(self, action: str, parameters: dict) -> list:
        required_params = ACTION_REQUIRED_PARAMS.get(action, [])
        missing = []
        for p in required_params:
            # Check for optional param marker '?'
            is_optional = p.endswith("?")
            clean_p = p.rstrip("?")
            
            if not is_optional:
                # Value must be present and truthy (or at least not None/empty)
                if clean_p not in parameters or parameters[clean_p] is None:
                    missing.append(clean_p)
        
        return missing

    async def _handle_music_action(self, action: str, parameters: dict):
        """
        Executes a music action via the music service.
        """
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
            complete_params["user_display_name"] = current_user.get("display_name")

        elif platform == "soundcloud":
             complete_params["access_token"] = access_token
             # SoundCloud adapter handles user resolution internally
             pass

        else:
            raise ValueError(f"Unsupported platform: {platform}")

        # Execute in thread executor to prevent blocking the async loop as adapter calls are synchronous 'requests'
        loop = asyncio.get_running_loop()
        
        logger.debug(f"Action: {action}, Parameters sent to MusicActionService: {complete_params}")
        
        return await loop.run_in_executor(
            None, 
            MusicActionService.perform_music_action, 
            action, 
            platform, 
            complete_params
        )
    
    def _log_interaction(self, user_input: str, llm_response: dict, final_action: str | None):
        """
        Persist a single user ↔ LLM interaction for future analysis / fine-tuning.
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


    async def execute_action(self, action: str, params: dict):
        """Public wrapper to execute a specific action (used for deferred playback)."""
        logger.info(f"Executing deferred action: {action}")
        return await self._handle_music_action(action, params)

    async def process_request(self, user_input: str):
        # Notify Frontend: Thinking
        await emit_state("THINKING", "Processing intent...")

        action_keys = MusicActionService.get_action_keys(platform=self.platform)

        # Get pending context
        pending_context = self.session_manager.get_pending_context(self.session_id)

        # Build Prompt
        turns = self.session_manager.get_turn_history(self.session_id)
        if turns:
            history_parts = []
            for i, m in enumerate(turns):
                if not isinstance(m, dict):
                    continue
                role = m.get('role')
                text = m.get('text')
                if role and text:
                    history_parts.append(f"{role}: {text}")
            
            history_text = " | ".join(history_parts)
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

        loop = asyncio.get_running_loop()
        
        # Step 1: Intent Recognition (LLM)
        nlp_result = await loop.run_in_executor(None, call_llm_agent, prompt_input, True, action_keys)
        
        logger.debug(f"LLM returned: {nlp_result}")
        logger.debug(f"LLM Response: {nlp_result}")

        actions = nlp_result.get("actions", [])
        final_reply = nlp_result.get("reply", "Sorry, I'm not sure how to help with that.")

        # Update History
        self.session_manager.add_turn_history(self.session_id, role="user", text=user_input)
        self.session_manager.add_turn_history(self.session_id, role="assistant", text=final_reply)

        if not actions:
            logger.info("LLM returned no actions. Proceeding with conversation only.")
            
            # Generate TTS for simple reply
            try:
                audio_bytes = await loop.run_in_executor(None, TextToSpeechService.synthesize_speech, final_reply)
                if audio_bytes:
                    return {"reply": final_reply, "audio_base64": base64.b64encode(audio_bytes).decode('utf-8'), "executed": False}
            except Exception as e:
                logger.error(f"TTS Failed: {e}")
            
            return {"reply": final_reply, "executed": False}

        # Task A: Generate TTS (Optimistic)
        async def generate_tts(text):
            try:
                if not text: return None
                return await loop.run_in_executor(None, TextToSpeechService.synthesize_speech, text)
            except Exception as e:
                logger.error(f"TTS Generation failed: {e}")
                return None

        tts_task = asyncio.create_task(generate_tts(final_reply))

        # Task B: Process Actions
        # ... logic extraction ...
        IMMEDIATE_ACTIONS = [
            'pause_song', 'skip_song', 'previous_song', 'skip_time', 
            'like_song', 'remove_from_liked_songs', 'delete_playlist', 
            'remove_from_playlist', 'reorder_playlist', 'add_to_playlist', 
            'create_playlist', 'get_current_song', 'set_volume',
            'increase_volume', 'decrease_volume'
        ]

        overall_results = []
        pending_action_info = None 
        final_action_executed = None
        command_payload = None 
        
        error_occurred = False
        error_msg = ""

        # Processing Actions
        for act_entry in actions:
            raw_action = act_entry.get("action")
            action = self.normalize_action(raw_action, action_keys)
            params = {**merged_parameters, **act_entry.get("parameters", {})}
            
            if not action: continue

            # Validate slot filling
            missing_params = self._check_missing_params(action, params)
            if missing_params:
                pending_action_info = {
                    "pending_action": action,
                    "pending_parameters": params,
                    "missing_params": missing_params
                }
                # If missing some parameters, change the reply to ask for them.
                final_reply = f"Please provide: {missing_params[0]} for action {action}."
                error_occurred = True
                break

            try:
                if action in IMMEDIATE_ACTIONS:
                    await emit_state("SPEAKING", f"Executing {action}...") 
                    result = await self._handle_music_action(action, params)
                    overall_results.append(result)
                    final_action_executed = action
                    
                    # If the action returned a user-facing string (e.g., error message or confirmation),
                    # let it override the LLM's optimistic reply.
                    if isinstance(result, str) and result:
                        final_reply = result
                        error_occurred = True 

                    command_payload = {
                        "type": action,
                        "params": params,
                        "timing": "IMMEDIATE"
                    }
                    self.session_manager.clear_session_state(self.session_id)
                
                else:
                    meta_params = dict(params)
                    meta_params["resolve_only"] = True
                    try:
                        meta_result = await self._handle_music_action(action, meta_params)
                        if meta_result: overall_results.append(meta_result)
                    except Exception as e:
                        logger.warning(f"Metadata resolution warning: {e}")

                    command_payload = {
                        "type": action,
                        "params": params,
                        "timing": "AFTER_TTS" 
                    }
                    final_action_executed = action 


            except DeviceNotFoundException as e:
                # Handle device not found with user-friendly message
                logger.error(f"Device not found during action execution: {e.message}")
                user_friendly_msg = get_user_friendly_error_message(
                    error_code="no_device",
                    platform=self.platform,
                    action=action,
                    original_message=str(e)
                )
                final_reply = user_friendly_msg
                error_occurred = True
                error_msg = user_friendly_msg
            
            except ExternalAPIError as e:
                # Handle API errors with user-friendly messages
                logger.error(f"API error during action execution: {e.message}")
                user_friendly_msg = e.user_friendly_message()
                final_reply = user_friendly_msg
                error_occurred = True
                error_msg = user_friendly_msg
            
            except Exception as e:
                logger.error(f"Action execution failed: {e}", exc_info=True)
                final_reply = f"I encountered an error: {str(e)}"
                error_occurred = True
                error_msg = str(e)

        # --- SYNC POINT ---
        # Wait for TTS to finish
        audio_bytes = None
        
        if not error_occurred and not pending_action_info:
            # Optimistic case: All good.
            audio_bytes = await tts_task
        else:
            # Failure/Change case: Cancel old TTS, generate new one.
            tts_task.cancel()
            try:
                audio_bytes = await generate_tts(final_reply)
            except Exception: pass

        # Prepare Response
        response_data = {
            "reply": final_reply,
            "action_outcome": "SUCCESS" if not pending_action_info and not error_occurred else ("PENDING" if pending_action_info else "ERROR"),
            "command": command_payload,
            "action_data": overall_results
        }
        
        if audio_bytes:
            response_data["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")

        # Handle Pending Context Save
        if pending_action_info:
            self.session_manager.save_pending_context(
                self.session_id,
                pending_action_info['pending_action'],
                pending_action_info['pending_parameters'],
                pending_action_info['missing_params']
            )
            response_data["status"] = "PENDING_INPUT"
        else:
             self._log_interaction(user_input, nlp_result, final_action_executed)

        return response_data

