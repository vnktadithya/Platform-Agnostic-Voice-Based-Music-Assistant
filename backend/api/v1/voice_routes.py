from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.speech_to_text import SpeechToTextService
from backend.services.text_to_speech import TextToSpeechService
import os
import shutil
import uuid

router = APIRouter(prefix="/voice", tags=["Voice I/O"])

stt_service = SpeechToTextService()
tts_service = TextToSpeechService()


@router.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    try:
        temp_filename = f"temp_audio_{uuid.uuid4().hex}_{audio.filename}"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        text = stt_service.transcribe_audio(temp_filename)
        os.remove(temp_filename)

        return {"transcription": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {str(e)}")


@router.post("/tts")
async def text_to_speech(text: str):
    try:
        output_audio_path = tts_service.synthesize_speech(text)
        return {"audio_path": output_audio_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")
