import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

class SpeechToTextService:
    @staticmethod
    def transcribe_audio(file_path: str) -> str:
        url = "https://api.elevenlabs.io/v1/speech-to-text"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY
        }

        data = {
            "model_id": "scribe_v1"
        }

        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(url, headers=headers, data=data, files=files)

            logger.debug("STT response status code: %s", response.status_code)

            if response.status_code == 200:
                return response.json().get("text", "")
            else:
                logger.error("STT API error | status=%s", response.status_code)
                raise Exception(f"STT API Error: {response.text}")

        except Exception:
            logger.error("Speech-to-text transcription failed", exc_info=True)
            raise