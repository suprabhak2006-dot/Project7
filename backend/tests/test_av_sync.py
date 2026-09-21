import numpy as np
from backend.forensic.fusion.av_sync import AVSynchronizationAnalyzer

def test_av_synchronization():
    analyzer = AVSynchronizationAnalyzer()
    
    # 20 simulated frame records
    frame_records = []
    fps = 30.0
    for i in range(25):
        t = i / fps
        aperture_delta = 10.0 * np.sin(2 * np.pi * 2 * t)
        frame_records.append({
            "timestamp": t,
            "landmarks": [
                [100.0, 100.0],
                [200.0, 100.0],
                [150.0, 150.0],
                [120.0, 200.0 + aperture_delta],
                [180.0, 200.0 + aperture_delta]
            ]
        })

    sr = 16000
    total_audio_samples = int((25 / fps) * sr)
    audio_signal = 0.5 * np.sin(2 * np.pi * 200 * np.linspace(0, 25/fps, total_audio_samples))

    res = analyzer.analyze_sync(frame_records, audio_signal, sr, fps)
    assert res["status"] == "COMPLETED"
    assert "sync_anomaly_score" in res
    assert 0.0 <= res["sync_anomaly_score"] <= 1.0
    assert "estimated_lag_ms" in res
    assert "measured_correlation" in res
