import os
import datetime
from typing import Dict, Any, List, Optional
import torch

from backend.app.core.config import settings
from backend.forensic.image.face_detector import YuNetFaceDetector
from backend.forensic.image.ai_detector import ViTDeepfakeDetector
from backend.forensic.temporal.analyzer import TemporalConsistencyAnalyzer
from backend.forensic.video.processor import VideoForensicProcessor
from backend.forensic.audio.processor import AudioForensicProcessor
from backend.forensic.fusion.av_sync import AVSynchronizationAnalyzer
from backend.forensic.fusion.engine import EvidenceFusionEngine

class ModelRegistry:
    """
    Central Model Registry orchestrating all computer vision, audio, temporal,
    and forensic models and analyzers.
    """
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return

        print("[*] Initializing DeepTrace Model Registry...")
        # 1. Face Detector
        try:
            face_detector = YuNetFaceDetector(model_path=settings.YUNET_MODEL_PATH)
            self._models["face_detector"] = face_detector
            print("    [+] YuNet face detector registered.")
        except Exception as e:
            print(f"    [!] Error registering face detector: {e}")
            self._models["face_detector"] = None

        # 2. Vision Deepfake AI Detector
        try:
            ai_detector = ViTDeepfakeDetector(
                model_id=settings.VIT_DEEPFAKE_MODEL_ID,
                enable_gpu=settings.ENABLE_GPU
            )
            self._models["image_ai_detector"] = ai_detector
            print("    [+] ViT image deepfake detector registered.")
        except Exception as e:
            print(f"    [!] Error registering image deepfake detector: {e}")
            self._models["image_ai_detector"] = None

        # 3. Temporal Consistency Analyzer
        temporal_analyzer = TemporalConsistencyAnalyzer()
        self._models["temporal_analyzer"] = temporal_analyzer

        # 4. Video Processor
        if self._models["face_detector"] and self._models["image_ai_detector"]:
            video_processor = VideoForensicProcessor(
                face_detector=self._models["face_detector"],
                ai_detector=self._models["image_ai_detector"],
                temporal_analyzer=temporal_analyzer
            )
            self._models["video_processor"] = video_processor
        else:
            self._models["video_processor"] = None

        # 5. Audio Processor
        audio_processor = AudioForensicProcessor()
        self._models["audio_processor"] = audio_processor

        # 6. AV Sync Analyzer
        av_sync_analyzer = AVSynchronizationAnalyzer()
        self._models["av_sync_analyzer"] = av_sync_analyzer

        # 7. Fusion Engine
        fusion_engine = EvidenceFusionEngine()
        self._models["fusion_engine"] = fusion_engine

        self._initialized = True
        print("[+] Model Registry initialization complete.")

    def get_face_detector(self) -> Optional[YuNetFaceDetector]:
        self.initialize()
        return self._models.get("face_detector")

    def get_image_ai_detector(self) -> Optional[ViTDeepfakeDetector]:
        self.initialize()
        return self._models.get("image_ai_detector")

    def get_temporal_analyzer(self) -> TemporalConsistencyAnalyzer:
        self.initialize()
        return self._models.get("temporal_analyzer")

    def get_video_processor(self) -> Optional[VideoForensicProcessor]:
        self.initialize()
        return self._models.get("video_processor")

    def get_audio_processor(self) -> AudioForensicProcessor:
        self.initialize()
        return self._models.get("audio_processor")

    def get_av_sync_analyzer(self) -> AVSynchronizationAnalyzer:
        self.initialize()
        return self._models.get("av_sync_analyzer")

    def get_fusion_engine(self) -> EvidenceFusionEngine:
        self.initialize()
        return self._models.get("fusion_engine")

    def get_status(self) -> List[Dict[str, Any]]:
        self.initialize()
        device_str = "CUDA" if (settings.ENABLE_GPU and torch.cuda.is_available()) else "CPU"

        face_det = self._models.get("face_detector")
        img_ai = self._models.get("image_ai_detector")
        audio_proc = self._models.get("audio_processor")

        status_list = [
            {
                "name": "yunet_face_detector",
                "version": "2023mar",
                "task": "FACE_DETECTION",
                "framework": "OPENCV",
                "loaded": face_det is not None,
                "checkpoint_verified": os.path.exists(settings.YUNET_MODEL_PATH),
                "device": "CPU",
                "status": "READY" if (face_det is not None) else "UNAVAILABLE",
                "limitations": "May degrade on extreme occlusions (>70%) or faces smaller than 16x16 px.",
                "last_health_check": datetime.datetime.utcnow().isoformat()
            },
            {
                "name": "vit_deepfake_detector",
                "version": "1.0",
                "task": "IMAGE_DEEPFAKE",
                "framework": "PYTORCH",
                "loaded": img_ai is not None and img_ai.is_available(),
                "checkpoint_verified": True,
                "device": img_ai.device if img_ai else device_str,
                "status": "READY" if (img_ai is not None and img_ai.is_available()) else "UNAVAILABLE",
                "limitations": "Binary classifier trained on facial crops. Performance may vary on heavy lossy compression.",
                "last_health_check": datetime.datetime.utcnow().isoformat()
            },
            {
                "name": "temporal_consistency_analyzer",
                "version": "1.0",
                "task": "VIDEO_TEMPORAL",
                "framework": "OPENCV",
                "loaded": True,
                "checkpoint_verified": True,
                "device": "CPU",
                "status": "READY",
                "limitations": "High-velocity camera panning may introduce natural transient frame deltas.",
                "last_health_check": datetime.datetime.utcnow().isoformat()
            },
            {
                "name": "signal_audio_forensics",
                "version": "1.0",
                "task": "AUDIO_SIGNAL",
                "framework": "SCIPY",
                "loaded": True,
                "checkpoint_verified": True,
                "device": "CPU",
                "status": "READY",
                "limitations": "Lossy MP3 encoding below 64kbps degrades high-frequency acoustic harmonics.",
                "last_health_check": datetime.datetime.utcnow().isoformat()
            },
            {
                "name": "synthetic_speech_detector",
                "version": "1.0",
                "task": "AUDIO_DEEPFAKE",
                "framework": "PYTORCH",
                "loaded": audio_proc.ai_audio_model is not None,
                "checkpoint_verified": False,
                "device": "CPU",
                "status": "UNAVAILABLE",
                "limitations": "AI speech checkpoint not installed; signal acoustics layer operates independently.",
                "last_health_check": datetime.datetime.utcnow().isoformat()
            },
            {
                "name": "av_synchronization_analyzer",
                "version": "1.0",
                "task": "AV_SYNC",
                "framework": "SCIPY",
                "loaded": True,
                "checkpoint_verified": True,
                "device": "CPU",
                "status": "READY",
                "limitations": "Requires visible speaking mouth with unobstructed audio track.",
                "last_health_check": datetime.datetime.utcnow().isoformat()
            }
        ]
        return status_list

# Global singleton
registry = ModelRegistry()
