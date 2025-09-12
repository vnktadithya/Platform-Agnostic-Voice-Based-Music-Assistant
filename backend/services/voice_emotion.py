import os
import torch
import tempfile
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
from pydub import AudioSegment
import librosa

class VoiceEmotionService:
    MODEL_NAME = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"

    def __init__(self):
        self.extractor = Wav2Vec2FeatureExtractor.from_pretrained(self.MODEL_NAME)
        self.model = Wav2Vec2ForSequenceClassification.from_pretrained(self.MODEL_NAME)

    def detect_emotion(self, file_path: str) -> str:
        # Convert to wav using pydub
        sound = AudioSegment.from_file(file_path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            clean = tmp.name
            sound.export(clean, format="wav")

        # Use librosa to load audio
        y, sr = librosa.load(clean, sr=16000, mono=True)
        os.remove(clean)

        # Prepare input for model
        input_tensor = self.extractor(y, sampling_rate=sr, return_tensors="pt").input_values
        with torch.no_grad():
            logits = self.model(input_tensor).logits
        
        pred = int(torch.argmax(logits, dim=-1)[0])
        return self.model.config.id2label[pred]
