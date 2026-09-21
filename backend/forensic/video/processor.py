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

    @staticmethod
    def analyze_video_quality(video_path: str) -> Dict[str, Any]:
        """
        Calculates video quality metrics (Requirement 22):
        Resolution, FPS, Blur score, Motion blur indicator, Blockiness, Frame drop indications.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Unable to read video for quality analysis"}

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0.0

        blur_scores = []
        consecutive_diffs = []
        prev_gray = None
        frames_sampled = 0

        # Sample up to 30 frames evenly
        sample_step = max(1, total_frames // 30) if total_frames > 0 else 1
        frame_idx = 0

        while cap.isOpened() and frames_sampled < 30:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_step == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Blur score via Laplacian variance
                lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                blur_scores.append(lap_var)

                if prev_gray is not None and prev_gray.shape == gray.shape:
                    diff = float(np.mean(cv2.absdiff(gray, prev_gray)))
                    consecutive_diffs.append(diff)
                prev_gray = gray
                frames_sampled += 1
            frame_idx += 1

        cap.release()

        avg_blur = float(np.mean(blur_scores)) if blur_scores else 0.0
        avg_motion = float(np.mean(consecutive_diffs)) if consecutive_diffs else 0.0
        duplicate_frames_ratio = float(np.mean([1 if d < 1.0 else 0 for d in consecutive_diffs])) if consecutive_diffs else 0.0

        # Quality warnings
        warnings = []
        if avg_blur < 50.0:
            warnings.append("High blur detected (may degrade facial landmark precision)")
        if width < 640 or height < 480:
            warnings.append("Low resolution video input (< 480p)")
        if duplicate_frames_ratio > 0.20:
            warnings.append(f"High duplicate frame rate ({round(duplicate_frames_ratio * 100, 1)}%) detected")

        return {
            "resolution": f"{width}x{height}",
            "fps": round(fps, 2),
            "duration_sec": round(duration, 2),
            "blur_score": round(avg_blur, 2),
            "blur_assessment": "Crisp" if avg_blur > 200 else ("Moderate" if avg_blur > 80 else "Blurry"),
            "motion_intensity": round(avg_motion, 2),
            "duplicate_frames_pct": round(duplicate_frames_ratio * 100, 1),
            "quality_warnings": warnings
        }

    @staticmethod
    def detect_scenes(video_path: str, threshold: float = 0.60) -> List[Dict[str, Any]]:
        """
        Detects video scene cuts/transitions using color histogram cross-correlation (Requirement 21).
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, int(fps // 2))  # Sample every 0.5s

        scenes = []
        current_scene_start = 0.0
        prev_hist = None
        frame_idx = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % step == 0:
                t = frame_idx / fps
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
                cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

                if prev_hist is not None:
                    sim = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                    if sim < threshold:
                        # Scene boundary detected
                        scenes.append({
                            "scene_id": len(scenes) + 1,
                            "start_time": round(current_scene_start, 2),
                            "end_time": round(t, 2),
                            "duration": round(t - current_scene_start, 2),
                            "transition_confidence": round(float(1.0 - max(0.0, sim)), 3)
                        })
                        current_scene_start = t
                prev_hist = hist
            frame_idx += 1

        cap.release()

        final_duration = frame_idx / fps if fps > 0 else 0.0
        if final_duration > current_scene_start:
            scenes.append({
                "scene_id": len(scenes) + 1,
                "start_time": round(current_scene_start, 2),
                "end_time": round(final_duration, 2),
                "duration": round(final_duration - current_scene_start, 2),
                "transition_confidence": 1.0
            })

        return scenes

    @staticmethod
    def compute_temporal_consistency_matrix(frames: List[np.ndarray]) -> Dict[str, Any]:
        """
        Computes an N x N temporal consistency correlation matrix across frames (Requirement 24).
        """
        n = min(len(frames), 16)
        if n < 2:
            return {"matrix": [], "labels": [], "mean_consistency": 1.0}

        subsampled = [cv2.resize(f, (64, 64)) for f in frames[:n]]
        vectors = [f.flatten().astype(np.float32) for f in subsampled]
        for i in range(n):
            norm = np.linalg.norm(vectors[i])
            if norm > 1e-6:
                vectors[i] /= norm

        matrix = []
        for i in range(n):
            row = []
            for j in range(n):
                sim = float(np.dot(vectors[i], vectors[j]))
                row.append(round(max(0.0, min(1.0, sim)), 3))
            matrix.append(row)

        off_diag = [matrix[i][i+1] for i in range(n-1)]
        mean_cons = float(np.mean(off_diag)) if off_diag else 1.0

        return {
            "matrix": matrix,
            "labels": [f"F{i+1}" for i in range(n)],
            "mean_consecutive_consistency": round(mean_cons, 4),
            "interpretation": "High temporal consistency" if mean_cons > 0.85 else "Temporal jitter / abrupt discontinuities observed"
        }

    @staticmethod
    def compute_frame_difference(frame1_bgr: np.ndarray, frame2_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Frame difference lab: absolute difference, edge difference, and structural disparity (Requirement 12).
        """
        if frame1_bgr.shape != frame2_bgr.shape:
            frame2_bgr = cv2.resize(frame2_bgr, (frame1_bgr.shape[1], frame1_bgr.shape[0]))

        gray1 = cv2.cvtColor(frame1_bgr, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2_bgr, cv2.COLOR_BGR2GRAY)

        abs_diff = cv2.absdiff(gray1, gray2)
        mean_diff = float(np.mean(abs_diff))
        max_diff = float(np.max(abs_diff))

        # Edge difference
        edge1 = cv2.Canny(gray1, 50, 150)
        edge2 = cv2.Canny(gray2, 50, 150)
        edge_diff = cv2.absdiff(edge1, edge2)
        edge_diff_score = float(np.mean(edge_diff)) / 255.0

        return {
            "mean_pixel_diff": round(mean_diff, 2),
            "max_pixel_diff": round(max_diff, 2),
            "edge_disparity_score": round(edge_diff_score, 4),
            "structural_similarity_index": round(max(0.0, 1.0 - (mean_diff / 128.0)), 4)
        }

