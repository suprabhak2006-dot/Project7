import os
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np

class YuNetFaceDetector:
    def __init__(self, model_path: str, score_threshold: float = 0.6, nms_threshold: float = 0.3):
        self.model_path = model_path
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.detector = None
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"YuNet model checkpoint not found at: {self.model_path}")
        self.detector = cv2.FaceDetectorYN_create(
            self.model_path,
            "",
            (320, 320),
            score_threshold=self.score_threshold,
            nms_threshold=self.nms_threshold,
            top_k=5000
        )

    def detect_faces(self, image_bgr: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect faces in image.
        Returns list of dicts:
        {
            'bbox': [x, y, w, h],
            'confidence': float,
            'landmarks': [[x1, y1], [x2, y2], [x3, y3], [x4, y4], [x5, y5]],
            'face_crop': np.ndarray (BGR)
        }
        """
        if self.detector is None or image_bgr is None:
            return []

        h, w, _ = image_bgr.shape
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(image_bgr)

        results = []
        if faces is None or len(faces) == 0:
            return results

        for face in faces:
            # face: [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rcm, y_rcm, x_lcm, y_lcm, score]
            x, y, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
            score = float(face[-1])
            landmarks = [
                [float(face[4]), float(face[5])],    # Right eye
                [float(face[6]), float(face[7])],    # Left eye
                [float(face[8]), float(face[9])],    # Nose tip
                [float(face[10]), float(face[11])],  # Right mouth corner
                [float(face[12]), float(face[13])],  # Left mouth corner
            ]

            # Clip bounding box
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(w, x + fw)
            y2 = min(h, y + fh)

            if x2 <= x1 or y2 <= y1:
                continue

            face_crop = image_bgr[y1:y2, x1:x2].copy()

            results.append({
                "bbox": [x1, y1, x2 - x1, y2 - y1],
                "confidence": score,
                "landmarks": landmarks,
                "face_crop": face_crop
            })

        return results

    def align_face(self, image_bgr: np.ndarray, landmarks: List[List[float]], desired_size: int = 224) -> np.ndarray:
        """
        Aligns face based on eye landmarks.
        """
        right_eye = np.array(landmarks[0])
        left_eye = np.array(landmarks[1])
        d_y = left_eye[1] - right_eye[1]
        d_x = left_eye[0] - right_eye[0]
        angle = np.degrees(np.arctan2(d_y, d_x))
        
        eyes_center = ((right_eye[0] + left_eye[0]) // 2, (right_eye[1] + left_eye[1]) // 2)
        m = cv2.getRotationMatrix2D(tuple(eyes_center), angle, 1.0)
        h, w = image_bgr.shape[:2]
        aligned = cv2.warpAffine(image_bgr, m, (w, h), flags=cv2.INTER_CUBIC)
        return aligned
