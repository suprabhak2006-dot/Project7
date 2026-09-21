import os
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np

from backend.forensic.image.face_detector import YuNetFaceDetector
from backend.forensic.image.ai_detector import ViTDeepfakeDetector
from backend.forensic.temporal.analyzer import TemporalConsistencyAnalyzer

def compute_iou(boxA: List[int], boxB: List[int]) -> float:
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = boxA[2] * boxA[3]
    boxBArea = boxB[2] * boxB[3]
    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
    return iou

class VideoForensicProcessor:
    def __init__(
        self,
        face_detector: YuNetFaceDetector,
        ai_detector: ViTDeepfakeDetector,
        temporal_analyzer: Optional[TemporalConsistencyAnalyzer] = None
    ):
        self.face_detector = face_detector
        self.ai_detector = ai_detector
        self.temporal_analyzer = temporal_analyzer or TemporalConsistencyAnalyzer()

    def process_video(
        self,
        video_path: str,
        output_dir: str,
        mode: str = "BALANCED",
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes video forensic pipeline.
        mode: FAST (1 fps), BALANCED (3 fps), DEEP (10 fps)
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0.0

        sample_rate = 1  # in fps
        if mode == "FAST":
            sample_rate = 1
        elif mode == "BALANCED":
            sample_rate = 3
        elif mode == "DEEP":
            sample_rate = 8

        frame_step = max(1, int(fps / sample_rate))

        frames_dir = os.path.join(output_dir, "frames")
        faces_dir = os.path.join(output_dir, "faces")
        os.makedirs(frames_dir, exist_ok=True)
        os.makedirs(faces_dir, exist_ok=True)

        frame_idx = 0
        analyzed_records: List[Dict[str, Any]] = []
        tracks: Dict[int, List[Dict[str, Any]]] = {}
        next_track_id = 1

        active_track_boxes: Dict[int, List[int]] = {}

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_step == 0:
                timestamp = frame_idx / fps
                
                # Detect faces in frame
                faces = self.face_detector.detect_faces(frame)

                # Track assignment
                for f in faces:
                    bbox = f["bbox"]
                    assigned_track_id = None
                    best_iou = 0.25

                    for tid, prev_box in active_track_boxes.items():
                        iou = compute_iou(bbox, prev_box)
                        if iou > best_iou:
                            best_iou = iou
                            assigned_track_id = tid

                    if assigned_track_id is None:
                        assigned_track_id = next_track_id
                        next_track_id += 1

                    active_track_boxes[assigned_track_id] = bbox

                    # Run real AI inference on face crop
                    ai_result = self.ai_detector.predict(f["face_crop"])
                    
                    # Save face crop image
                    crop_filename = f"face_t{assigned_track_id}_f{frame_idx}.jpg"
                    crop_path = os.path.join(faces_dir, crop_filename)
                    cv2.imwrite(crop_path, f["face_crop"])

                    rec = {
                        "frame_number": frame_idx,
                        "timestamp": round(timestamp, 3),
                        "track_id": assigned_track_id,
                        "bbox": bbox,
                        "landmarks": f["landmarks"],
                        "face_crop_rel_path": os.path.join("faces", crop_filename),
                        "model_name": ai_result["model_name"],
                        "model_version": ai_result["model_version"],
                        "raw_logits": ai_result["raw_logits"],
                        "manipulation_score": ai_result["manipulation_score"],
                        "confidence": ai_result["confidence"]
                    }
                    analyzed_records.append(rec)
                    tracks.setdefault(assigned_track_id, []).append(rec)

                # Save sampled frame thumbnail
                if len(faces) > 0 or frame_idx % (frame_step * 5) == 0:
                    thumb_path = os.path.join(frames_dir, f"frame_{frame_idx:06d}.jpg")
                    cv2.imwrite(thumb_path, cv2.resize(frame, (640, 360)))

                if progress_callback:
                    pct = min(95.0, (frame_idx / max(1, total_frames)) * 100.0)
                    progress_callback(pct, f"Processed frame {frame_idx}/{total_frames}")

            frame_idx += 1

        cap.release()

        # Temporal analysis across primary face track
        temporal_results = {}
        if tracks:
            # Select track with most frames
            primary_tid = max(tracks.keys(), key=lambda k: len(tracks[k]))
            temporal_results = self.temporal_analyzer.analyze_track(tracks[primary_tid])
        else:
            temporal_results = {
                "temporal_anomaly_score": 0.0,
                "confidence": 0.5,
                "suspicious_spikes": [],
                "status": "No faces tracked in video"
            }

        # Aggregate frame predictions
        scores = [r["manipulation_score"] for r in analyzed_records]
        avg_video_score = float(np.mean(scores)) if scores else 0.0
        max_video_score = float(np.max(scores)) if scores else 0.0
        
        # Build timeline
        timeline = []
        for r in analyzed_records:
            timeline.append({
                "timestamp": r["timestamp"],
                "frame": r["frame_number"],
                "score": round(r["manipulation_score"], 4),
                "confidence": round(r["confidence"], 4),
                "track_id": r["track_id"],
                "is_spike": r["manipulation_score"] >= 0.75,
                "face_crop": r["face_crop_rel_path"]
            })

        return {
            "total_frames": total_frames,
            "fps": fps,
            "duration": round(duration, 2),
            "analyzed_frames_count": len(analyzed_records),
            "tracked_faces_count": len(tracks),
            "average_frame_score": round(avg_video_score, 4),
            "peak_frame_score": round(max_video_score, 4),
            "temporal_analysis": temporal_results,
            "timeline": timeline,
            "analyzed_records": analyzed_records
        }
