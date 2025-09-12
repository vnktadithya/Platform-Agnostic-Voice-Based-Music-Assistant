#new chat_routes.py:

import uuid
import os
import base64
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from ...configurations.database import get_db
from ...services.speech_to_text import SpeechToTextService
from ...services.text_to_speech import TextToSpeechService
from ...services.voice_emotion import VoiceEmotionService
from ...services.dialog_manager import DialogManager
import logging

router = APIRouter(prefix="/chat", tags=["Chat NLP"])
logger = logging.getLogger(__name__)

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

class TextInput(BaseModel):
    text: str
    session_id: str | None = None  # Optional session_id from client
    platform_account_id: int | None = None


def attach_tts(reply_text: str) -> str:
    """Convert reply to speech and return as base64 string."""
    try:
        audio_bytes = TextToSpeechService.synthesize_speech(reply_text)
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception:
        return None


@router.post("/process_text")
def process_chat_text(
    text_input: TextInput,
    platform: str = Query("spotify", description="Platform name"),
    db: Session = Depends(get_db)
):
    try:
        session_id = text_input.session_id or str(uuid.uuid4()) 
        dialog_manager = DialogManager(db, session_id, platform, platform_account_id=text_input.platform_account_id)
        result = dialog_manager.process_request(text_input.text)

        reply_text = result.get("reply", "I'm not sure how to respond.")
        audio_b64 = attach_tts(reply_text)

        response = {
            "session_id": session_id,
            "reply": reply_text,
            **result
        }
        if audio_b64:
            response["audio_base64"] = audio_b64

        return JSONResponse(content=response)
    except ValueError as e:
        logger.error("DialogManager error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error in /process_text")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/process_voice")
def process_chat_voice(
    audio: UploadFile = File(...),
    session_id: str | None = Query(None, description="Session ID for multi-turn conversation"),
    platform: str = Query("spotify", description="Platform name"),
    db: Session = Depends(get_db)
):
    session_id = session_id or str(uuid.uuid4())
    temp_filepath = os.path.join(TEMP_DIR, f"{session_id}.wav")
    try:
        with open(temp_filepath, "wb") as f:
            f.write(audio.file.read())

        transcribed_text = SpeechToTextService.transcribe_audio(temp_filepath)
        voice_emotion = VoiceEmotionService().detect_emotion(temp_filepath)
        
        dialog_manager = DialogManager(db, session_id, platform)
        result = dialog_manager.process_request(transcribed_text, voice_emotion)

        reply_text = result.get("reply", "I'm not sure how to respond.")
        audio_b64 = attach_tts(reply_text)

        response = {
            "session_id": session_id,
            "reply": reply_text,
            "input_text": transcribed_text, 
            **result
        }
        if audio_b64:
            response["audio_base64"] = audio_b64

        return JSONResponse(content=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
