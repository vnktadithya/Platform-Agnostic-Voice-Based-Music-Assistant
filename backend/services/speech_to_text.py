import requests
import os
from dotenv import load_dotenv

load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
class SpeechToTextService:
    @staticmethod
    def transcribe_audio(file_path: str) -> str:
        url = "https://api.elevenlabs.io/v1/speech-to-text"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY
        }

        data = {
            "model_id": "scribe_v1"  # Required field for ElevenLabs STT
        }

        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(url, headers=headers, data=data, files=files)

            print("Status code:", response.status_code)
            print("Response:", response.text)

            if response.status_code == 200:
                return response.json().get("text", "")
            else:
                raise Exception(f"STT API Error: {response.text}")

        except Exception as e:
            print("❌ Error during transcription:", str(e))
            raise