from typing import List, Dict, Any, Optional
import numpy as np
from scipy import signal

class AVSynchronizationAnalyzer:
    """
    Measures cross-correlation between vertical facial mouth aperture and speech audio energy envelope.
    """
    def analyze_sync(
        self,
        frame_records: List[Dict[str, Any]],
        audio_signal: np.ndarray,
        sample_rate: int,
        fps: float
    ) -> Dict[str, Any]:
        """
        frame_records: frame detections containing 'landmarks' and 'timestamp'
        audio_signal: 1D mono audio samples
        sample_rate: audio sample rate (e.g. 16000)
        fps: video frames per second
        """
        if len(frame_records) < 10 or len(audio_signal) < (sample_rate // 4):
            return {
                "status": "INSUFFICIENT_DATA",
                "sync_anomaly_score": 0.0,
                "confidence": 0.4,
                "measured_correlation": 0.0,
                "estimated_lag_ms": 0.0,
                "affected_intervals": [],
                "methodology": "Requires minimum 10 frames with face and audio samples"
            }

        # 1. Extract mouth vertical aperture across frames
        # Landmark 3 is right mouth corner, Landmark 4 is left mouth corner
        # Landmark 2 is nose tip. Vertical distance from nose tip to mouth line measures jaw movement
        mouth_apertures = []
        timestamps = []
        for r in frame_records:
            lm = r.get("landmarks")
            if lm and len(lm) >= 5:
                nt = np.array(lm[2])
                mid_mouth = (np.array(lm[3]) + np.array(lm[4])) / 2.0
                aperture = float(np.linalg.norm(mid_mouth - nt))
                mouth_apertures.append(aperture)
                timestamps.append(r["timestamp"])

        if len(mouth_apertures) < 10:
            return {
                "status": "INSUFFICIENT_LANDMARKS",
                "sync_anomaly_score": 0.0,
                "confidence": 0.4,
                "measured_correlation": 0.0,
                "estimated_lag_ms": 0.0,
                "affected_intervals": [],
                "methodology": "Facial mouth landmarks not reliably tracked"
            }

        # Compute mouth velocity (derivative of aperture)
        mouth_series = np.array(mouth_apertures)
        mouth_velocity = np.abs(np.diff(mouth_series))

        # 2. Extract audio energy envelope aligned to frame intervals
        audio_energy = []
        for i in range(len(timestamps) - 1):
            t_start = timestamps[i]
            t_end = timestamps[i+1]
            idx_start = int(t_start * sample_rate)
            idx_end = int(t_end * sample_rate)
            if idx_end > idx_start and idx_end <= len(audio_signal):
                segment = audio_signal[idx_start:idx_end]
                energy = float(np.sqrt(np.mean(segment**2)))
            else:
                energy = 0.0
            audio_energy.append(energy)

        energy_series = np.array(audio_energy)

        # Normalize both series
        m_norm = (mouth_velocity - np.mean(mouth_velocity)) / (np.std(mouth_velocity) + 1e-6)
        e_norm = (energy_series - np.mean(energy_series)) / (np.std(energy_series) + 1e-6)

        # Cross-correlation
        cross_corr = signal.correlate(m_norm, e_norm, mode="full")
        lags = signal.correlation_lags(len(m_norm), len(e_norm), mode="full")
        
        # Max lag within search window of +/- 15 frames (~0.5 seconds)
        window = np.abs(lags) <= 15
        valid_lags = lags[window]
        valid_corr = cross_corr[window]

        if len(valid_corr) == 0:
            best_lag = 0
            max_corr = 0.0
        else:
            best_idx = np.argmax(valid_corr)
            best_lag = int(valid_lags[best_idx])
            norm_factor = np.sqrt(np.sum(m_norm**2) * np.sum(e_norm**2)) + 1e-6
            max_corr = float(valid_corr[best_idx] / norm_factor)

        # Convert lag to milliseconds
        lag_ms = float((best_lag / fps) * 1000.0)

        # Identify anomalous intervals where audio energy is high but mouth is stationary
        affected_intervals = []
        for i in range(len(m_norm)):
            if e_norm[i] > 1.2 and m_norm[i] < -0.5:
                t_curr = timestamps[i]
                affected_intervals.append({
                    "start_time": round(t_curr, 2),
                    "end_time": round(t_curr + (1.0 / fps), 2),
                    "description": f"Speech energy detected without corresponding lip movement at {t_curr:.2f}s"
                })

        # Calculate sync anomaly score
        anomaly_score = 0.0
        if abs(lag_ms) > 120.0:
            anomaly_score += 0.4
        if max_corr < 0.15 and np.mean(energy_series) > 0.02:
            anomaly_score += 0.35
        if len(affected_intervals) > 3:
            anomaly_score += 0.25

        return {
            "status": "COMPLETED",
            "sync_anomaly_score": round(min(1.0, anomaly_score), 4),
            "confidence": 0.76,
            "measured_correlation": round(max_corr, 4),
            "estimated_lag_ms": round(lag_ms, 1),
            "affected_intervals": affected_intervals[:10],
            "methodology": "Cross-correlation between facial mouth aperture velocity and audio speech energy envelope"
        }
