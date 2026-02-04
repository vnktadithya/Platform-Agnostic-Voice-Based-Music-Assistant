import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class SpeechToTextService:
    @staticmethod
    def transcribe_audio(file_obj) -> str:
        """
        Transcribes audio using Groq's Whisper-large-v3.
        Accepts a file-like object (bytesIO or UploadFile.file) directly.
        """
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing. Please get a free key from https://console.groq.com/keys and add it to your .env file.")

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        
        # English-only prompt enforcement
        prompt_text = (
            "The transcript is in English alphabets only. "
            "Even foreign words (like Telugu, Tamil, Hindi) are written strictly in English script (transliterated). "
            "Example: Play nuvvu nenantu, play manasu palike. No native scripts."
        )

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }

        try:
            # Check if file_obj is bytes, wrap it if so
            if isinstance(file_obj, bytes):
                import io
                file_obj = io.BytesIO(file_obj)

            files = {
                "file": ("audio.wav", file_obj, "audio/wav")
            }
            data = {
                "model": "whisper-large-v3",
                "temperature": "0",
                "response_format": "json",
                "language": "en",
                "prompt": prompt_text
            }
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Groq STT Error: {response.text}")
                raise Exception(f"Groq STT API Failed: {response.status_code} - {response.text}")

            result = response.json()
            transcript = result.get("text", "").strip()
            
            logger.info(f"Groq Transcription: {transcript}")
            return transcript

        except Exception as e:
            logger.error("Groq STT failed", exc_info=True)
            raise e
