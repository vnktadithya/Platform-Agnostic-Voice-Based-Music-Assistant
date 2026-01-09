import requests
import os
from dotenv import load_dotenv
from uuid import uuid4
import logging


load_dotenv()
logger = logging.getLogger(__name__)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Default voice

TEMP_AUDIO_DIR = "temp_audio"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

class TextToSpeechService:
    @staticmethod
    def synthesize_speech(text: str, output_path: str = None) -> str:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

        body = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(url, headers=headers, json=body)

        if response.status_code == 200:
            filename = f"tts_{uuid4().hex}.mp3"
            file_path = os.path.join(TEMP_AUDIO_DIR, filename)
            audio_bytes = response.content

            with open(file_path, "wb") as f:
                f.write(audio_bytes)

            return audio_bytes
        else:
            logger.error("Text-to-speech failed | status=%s", response.status_code)
            raise Exception("TTS failed")
