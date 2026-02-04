import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class TextToSpeechService:
    @staticmethod
    def synthesize_speech(text: str) -> bytes:
        """
        Synthesizes speech using Groq's high-speed TTS (OpenAI compatible API).
        Returns raw audio bytes (MP3/WAV) without writing to disk.
        """
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing. Please ensure it is set in your .env file.")

        # Groq TTS Endpoint (OpenAI compatible)
        url = "https://api.groq.com/openai/v1/audio/speech"
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        # Using 'canopylabs/orpheus-v1-english'
        body = {
            "model": "canopylabs/orpheus-v1-english",
            "voice": "troy", 
            "response_format": "wav",
            "input": text
        }

        try:
            response = requests.post(url, headers=headers, json=body, timeout=60)

            if response.status_code == 200:
                # Return audio bytes directly
                return response.content
            else:
                logger.error(f"Groq TTS failed: {response.text}")
                raise Exception(f"Groq TTS API Failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error("Text-to-speech synthesis failed", exc_info=True)
            # Re-raising is safer for the caller to handle.
            raise e

