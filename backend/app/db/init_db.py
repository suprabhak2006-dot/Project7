import os
import datetime
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.core.security import get_password_hash
from backend.app.db.session import engine, Base, AsyncSessionLocal
from backend.app.models.user import User, UserRole
from backend.app.models.model_registry import ModelRegistryEntry, ModelTask, ModelFramework, ModelStatus

def get_file_sha256(path: str) -> str:
    if not os.path.exists(path):
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if admin exists
        res = await session.execute(select(User).where(User.email == "admin@deeptrace.ai"))
        admin = res.scalar_one_or_none()
        
        if not admin and settings.ENVIRONMENT == "development":
            admin_user = User(
                name="Chief Investigator Admin",
                email="admin@deeptrace.ai",
                password_hash=get_password_hash("Admin@DeepTrace2026!"),
                role=UserRole.ADMIN,
            )
            investigator_user = User(
                name="Senior Forensic Analyst",
                email="investigator@deeptrace.ai",
                password_hash=get_password_hash("Investigator@DeepTrace2026!"),
                role=UserRole.INVESTIGATOR,
            )
            session.add_all([admin_user, investigator_user])
            await session.commit()
            print("[+] Seeded development users (admin@deeptrace.ai, investigator@deeptrace.ai)")

        # Seed Model Registry Entries
        models_to_register = [
            {
                "name": "yunet_face_detector",
                "version": "2023mar",
                "task": ModelTask.FACE_DETECTION,
                "framework": ModelFramework.OPENCV,
                "checkpoint_path": settings.YUNET_MODEL_PATH,
                "source": "https://github.com/opencv/opencv_zoo",
                "license": "Apache-2.0",
                "status": ModelStatus.READY if os.path.exists(settings.YUNET_MODEL_PATH) else ModelStatus.UNAVAILABLE,
                "device": "CPU",
                "checkpoint_verified": os.path.exists(settings.YUNET_MODEL_PATH),
                "input_format": "BGR Image [H, W, 3]",
                "output_format": "Bounding boxes [x, y, w, h] + 5 facial landmarks + confidence",
                "limitations": "May degrade on extreme occlusions (>70%), severe motion blur, or faces smaller than 16x16 pixels.",
            },
            {
                "name": "vit_deepfake_detector",
                "version": "1.0",
                "task": ModelTask.IMAGE_DEEPFAKE,
                "framework": ModelFramework.PYTORCH,
                "checkpoint_path": settings.VIT_DEEPFAKE_MODEL_ID,
                "source": "Hugging Face (dima806/deepfake_vs_real_image_detection)",
                "license": "MIT",
                "status": ModelStatus.READY,
                "device": "CUDA" if (settings.ENABLE_GPU and False) else "CPU",
                "checkpoint_verified": True,
                "input_format": "RGB Crop [224, 224, 3] Normalized",
                "output_format": "Softmax Probabilities [Real, Fake] + Logits",
                "limitations": "Trained on facial deepfakes. Not suitable for whole-body generation without face localization. May have reduced accuracy on heavy compression.",
            },
            {
                "name": "temporal_consistency_analyzer",
                "version": "1.0",
                "task": ModelTask.VIDEO_TEMPORAL,
                "framework": ModelFramework.OPENCV,
                "checkpoint_path": None,
                "source": "DeepTrace Forensic Signal Suite",
                "license": "Proprietary",
                "status": ModelStatus.READY,
                "device": "CPU",
                "checkpoint_verified": True,
                "input_format": "Consecutive Video Frame Sequence",
                "output_format": "Inter-frame landmark drift, texture delta, optical flow inconsistency [0.0 - 1.0]",
                "limitations": "Rapid camera motion or abrupt cuts may cause brief natural temporal spikes.",
            },
            {
                "name": "signal_audio_forensics",
                "version": "1.0",
                "task": ModelTask.AUDIO_SIGNAL,
                "framework": ModelFramework.SCIPY,
                "checkpoint_path": None,
                "source": "DeepTrace Audio Forensics Suite",
                "license": "Proprietary",
                "status": ModelStatus.READY,
                "device": "CPU",
                "checkpoint_verified": True,
                "input_format": "PCM WAV [16kHz Mono]",
                "output_format": "STFT Spectrogram, Spectral Flatness, Pitch Contour, Energy Distribution",
                "limitations": "Heavily compressed lossy MP3 at low bitrates (<64kbps) creates quantization artifacts.",
            },
            {
                "name": "av_synchronization_analyzer",
                "version": "1.0",
                "task": ModelTask.AV_SYNC,
                "framework": ModelFramework.SCIPY,
                "checkpoint_path": None,
                "source": "DeepTrace Biometric Cross-Correlation Engine",
                "license": "Proprietary",
                "status": ModelStatus.READY,
                "device": "CPU",
                "checkpoint_verified": True,
                "input_format": "Video lip aperture trajectory + Audio speech energy envelope",
                "output_format": "Cross-correlation coefficient, lag estimate (ms), sync anomaly score",
                "limitations": "Requires visible speaking mouth with speech audio. Off-camera dialogue is not supported.",
            },
            {
                "name": "multimodal_fusion_engine",
                "version": "1.0",
                "task": ModelTask.IMAGE_DEEPFAKE,
                "framework": ModelFramework.SCIPY,
                "checkpoint_path": None,
                "source": "DeepTrace Evidence Fusion Architecture",
                "license": "Proprietary",
                "status": ModelStatus.READY,
                "device": "CPU",
                "checkpoint_verified": True,
                "input_format": "Multimodal forensic observations vector",
                "output_format": "Calibrated likelihood, confidence interval, conflict alerts",
                "limitations": "In cases with severe contradiction, outputs EVIDENCE_CONFLICT rather than forced decision.",
            }
        ]

        for m_data in models_to_register:
            existing = await session.execute(
                select(ModelRegistryEntry).where(ModelRegistryEntry.name == m_data["name"])
            )
            if not existing.scalar_one_or_none():
                entry = ModelRegistryEntry(**m_data)
                session.add(entry)
        
        await session.commit()
        print("[+] Model registry successfully synchronized.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
