import os
import tempfile
import numpy as np
import scipy.io.wavfile as wavfile
from backend.forensic.audio.processor import AudioForensicProcessor

def test_audio_signal_forensics():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # Generate 440 Hz pure tone with harmonics
    audio = (0.5 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 880 * t)).astype(np.float32)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wavfile.write(f.name, sr, (audio * 32767).astype(np.int16))
        wav_path = f.name

    try:
        proc = AudioForensicProcessor()
        res = proc.analyze_audio(wav_path)
        assert res["duration"] > 0.9
        assert res["sample_rate"] == 16000
        
        sig = res["signal_forensics"]
        assert "spectral_flatness" in sig
        assert "average_pitch_hz" in sig
        assert "spectral_rolloff_hz" in sig
        assert "signal_anomaly_indicator" in sig
        assert 0.0 <= sig["signal_anomaly_indicator"] <= 1.0

        # Layer B AI speech status check
        ai_speech = res["ai_speech_detector"]
        assert ai_speech["status"] == "UNAVAILABLE"
        assert ai_speech["score"] is None  # Must never fake score!
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
