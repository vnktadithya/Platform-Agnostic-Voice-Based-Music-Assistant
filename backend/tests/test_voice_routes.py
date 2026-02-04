import pytest
from fastapi.testclient import TestClient
from backend.main import app
import builtins
import os

client = TestClient(app)

def test_tts_endpoint(monkeypatch):
    """Test Text-to-Speech endpoint with mocked service."""
    def mock_synthesize(self, text):
        return "/path/to/fake_audio.wav"
        
    monkeypatch.setattr("backend.services.text_to_speech.TextToSpeechService.synthesize_speech", mock_synthesize)
    
    response = client.post("/v1/voice/tts", params={"text": "Hello world"})
    assert response.status_code == 200
    assert response.json()["audio_path"] == "/path/to/fake_audio.wav"

def test_stt_endpoint(monkeypatch):
    """Test Speech-to-Text endpoint with mocked service and file handling."""
    
    # Mock STT service
    def mock_transcribe(self, filename):
        return "Transcribed text"
    monkeypatch.setattr("backend.services.speech_to_text.SpeechToTextService.transcribe_audio", mock_transcribe)
    
    # Mock UUID to have predictable filename if needed, or just let it run since we mock transcribe
    
    # Mock file cleanup (os.remove) to avoid erroring on non-existent temp file
    monkeypatch.setattr(os, "remove", lambda x: None)
    
    # Mock internal open/shutil copy if necessary, but FastAPIs TestClient handles file uploads well.
    # We might need to mock shutil.copyfileobj if we don't want real file IO.
    # For simplicity, let's provide a real dummy file content.
    
    files = {'audio': ('test.wav', b'fake audio data', 'audio/wav')}
    response = client.post("/v1/voice/stt", files=files)
    
    assert response.status_code == 200
    assert response.json()["transcription"] == "Transcribed text"
