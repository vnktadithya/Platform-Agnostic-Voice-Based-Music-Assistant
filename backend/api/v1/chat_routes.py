import uuid
import os
import base64
import wave
import io
import logging
import asyncio
import requests
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.configurations.database import get_db
from backend.services.speech_to_text import SpeechToTextService
from backend.services.text_to_speech import TextToSpeechService
from backend.services.dialog_manager import DialogManager
from backend.utils.custom_exceptions import DeviceNotFoundException, ExternalAPIError, AuthenticationError

router = APIRouter(prefix="/chat", tags=["Chat NLP"])
logger = logging.getLogger(__name__)

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

class TextInput(BaseModel):
    text: str
    session_id: str | None = None
    platform_account_id: int | None = None
    

class ActionPayload(BaseModel):
    action: str
    parameters: dict
    platform: str
    session_id: str | None = None
    platform_account_id: int

@router.post("/execute")
async def execute_action(
    payload: ActionPayload,
    db: Session = Depends(get_db)
):
    """Endpoint for Client to trigger an action (e.g. after TTS ends)."""
    logger.info(f"Client triggering action: {payload.action}")
    
    session_id = resolve_session_id(payload.session_id)
    dm = DialogManager(db, session_id, payload.platform, platform_account_id=payload.platform_account_id)
    
    try:
        result = await dm.execute_action(payload.action, payload.parameters)
        return {"status": "success", "result": result}
    except (DeviceNotFoundException, ExternalAPIError, AuthenticationError):
        # Let these bubble up to the global handler in main.py
        raise 
    except Exception as e:
        logger.error(f"Failed to execute triggered action {payload.action}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def resolve_session_id(provided: str | None) -> str:
    return provided or str(uuid.uuid4())



@router.post("/process_text")
async def process_chat_text(
    request: Request,
    text_input: TextInput,
    platform: str = Query(..., description="Platform name (spotify, soundcloud, etc.)"),
    db: Session = Depends(get_db)
):
    
    platform = platform.strip().lower()

    # SECURE SESSION CHECK
    secure_account_id = request.session.get(f"{platform}_account_id")
    if secure_account_id:
        text_input.platform_account_id = secure_account_id
        logger.info(f"Using secure session account_id: {secure_account_id}")

    if not text_input.platform_account_id:
        raise HTTPException(
            status_code=400,
            detail="platform_account_id is required (please login first)"
        )
    
    logger.info(
        "Incoming chat request | platform=%s | platform_account_id=%s",
        platform,
        text_input.platform_account_id
    )

    try:
        session_id = resolve_session_id(text_input.session_id) 
        dialog_manager = DialogManager(db, session_id, platform, platform_account_id=text_input.platform_account_id)
        
        result = await dialog_manager.process_request(text_input.text)

        response = {
            "session_id": session_id,
            **result
        }
        return JSONResponse(content=response)

    except ValueError as e:
        logger.error("DialogManager error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except (DeviceNotFoundException, ExternalAPIError, AuthenticationError):
        raise
    except Exception as e:
        logger.exception("Unexpected error in /process_text")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/process_voice")
async def process_chat_voice(
    request: Request,
    audio: UploadFile = File(...),
    session_id: str | None = Query(None, description="Session ID for multi-turn conversation"),
    platform: str = Query(..., description="Platform name (spotify, soundcloud, etc.)"),
    platform_account_id: int | None = Query(None, description="PlatformAccount ID"),
    db: Session = Depends(get_db)
):
    
    platform = platform.strip().lower()
    session_id = resolve_session_id(session_id)

    # SECURE SESSION CHECK
    secure_account_id = request.session.get(f"{platform}_account_id")
    if secure_account_id:
        platform_account_id = secure_account_id
        logger.info(f"Using secure session account_id: {secure_account_id}")

    if not platform_account_id:
        raise HTTPException(
            status_code=400,
            detail="platform_account_id is required (please login first)"
        )

    logger.info(
        "Incoming voice chat request | platform=%s | platform_account_id=%s",
        platform,
        platform_account_id
    )

    try:
        loop = asyncio.get_running_loop()
        transcribed_text = await loop.run_in_executor(None, SpeechToTextService.transcribe_audio, audio.file)
        
        logger.info(f"\n\n🎤 STT OUTPUT: {transcribed_text}\n") 
        
        dialog_manager = DialogManager(db, session_id, platform, platform_account_id=platform_account_id)
        result = await dialog_manager.process_request(transcribed_text)

        response = {
            "session_id": session_id,
            "input_text": transcribed_text, 
            **result
        }

        return JSONResponse(content=response)

    except requests.exceptions.RequestException as e:
        logger.error(f"Voice service connection failed: {e}")
        raise HTTPException(
            status_code=504, 
            detail="Voice service connection timed out. Please check your internet connection and try again."
        )
    except (DeviceNotFoundException, ExternalAPIError, AuthenticationError):
        raise
    except Exception as e:
        logger.error(f"Voice processing invalid error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
