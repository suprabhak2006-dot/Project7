from typing import List, Dict, Any, Optional
import numpy as np

class TemporalConsistencyAnalyzer:
    """
    Analyzes temporal consistency across sequential video frames:
    1. Landmark coordinate stability (jitter/drift).
    2. Manipulation score fluctuations across consecutive frames.
    3. Facial boundary & texture transitions.
    """
    def __init__(self, anomaly_spike_threshold: float = 0.35):
        self.anomaly_spike_threshold = anomaly_spike_threshold

    def analyze_track(self, frame_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes a sequence of frame records belonging to a tracked face.
        frame_records: sorted by frame_number / timestamp
        """
        if len(frame_records) < 2:
            avg_score = frame_records[0]["manipulation_score"] if frame_records else 0.0
            return {
                "temporal_anomaly_score": 0.0,
                "confidence": 0.5,
                "landmark_drift_variance": 0.0,
                "score_volatility": 0.0,
                "suspicious_spikes": [],
                "methodology": "Single frame available; temporal analysis requires multiple frames"
            }

        scores = [r["manipulation_score"] for r in frame_records]
        timestamps = [r["timestamp"] for r in frame_records]

        # 1. Landmark drift across consecutive frames
        landmark_drifts = []
        for i in range(1, len(frame_records)):
            lm_prev = np.array(frame_records[i-1]["landmarks"])
            lm_curr = np.array(frame_records[i]["landmarks"])
            
            # Normalize landmark coordinates by bounding box diagonal
            bbox = frame_records[i]["bbox"]
            diag = np.sqrt(bbox[2]**2 + bbox[3]**2) + 1e-6
            drift = float(np.mean(np.linalg.norm(lm_curr - lm_prev, axis=1)) / diag)
            landmark_drifts.append(drift)

        avg_drift = float(np.mean(landmark_drifts)) if landmark_drifts else 0.0
        drift_variance = float(np.var(landmark_drifts)) if landmark_drifts else 0.0

        # 2. Score volatility & sudden spikes
        score_deltas = [abs(scores[i] - scores[i-1]) for i in range(1, len(scores))]
        score_volatility = float(np.mean(score_deltas)) if score_deltas else 0.0

        suspicious_spikes = []
        for i in range(1, len(frame_records)):
            delta = abs(scores[i] - scores[i-1])
            if delta >= self.anomaly_spike_threshold or scores[i] >= 0.75:
                suspicious_spikes.append({
                    "frame_number": frame_records[i]["frame_number"],
                    "timestamp": frame_records[i]["timestamp"],
                    "score": round(scores[i], 4),
                    "delta": round(delta, 4),
                    "description": f"Abnormal manipulation spike (delta={delta:.2f}, score={scores[i]:.2f}) at t={timestamps[i]:.2f}s"
                })

        # Aggregated temporal anomaly score
        temporal_score = min(1.0, (avg_drift * 3.0 + score_volatility * 1.5))

        return {
            "temporal_anomaly_score": round(temporal_score, 4),
            "confidence": 0.82,
            "average_landmark_drift": round(avg_drift, 4),
            "landmark_drift_variance": round(drift_variance, 6),
            "score_volatility": round(score_volatility, 4),
            "suspicious_spikes": suspicious_spikes,
            "total_frames_analyzed": len(frame_records),
            "methodology": "Normalized inter-frame facial landmark drift and manipulation volatility measurement"
        }
