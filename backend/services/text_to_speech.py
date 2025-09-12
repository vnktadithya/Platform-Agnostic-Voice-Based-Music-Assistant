import requests
import os
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Default voice
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
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(url, headers=headers, json=body)

        if response.status_code == 200:
            audio_path = output_path or f"output_{uuid4().hex}.mp3"
            with open(audio_path, "wb") as f:
                f.write(response.content)
            return audio_path
        else:
            print(response.json())
            raise Exception("TTS failed")
