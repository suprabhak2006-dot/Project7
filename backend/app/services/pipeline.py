import os
import time
import datetime
import cv2
import numpy as np
from typing import Dict, Any, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.models.evidence import Evidence, MediaType
from backend.app.models.analysis import Analysis, AnalysisStatus, AnalysisAssessment
from backend.app.models.finding import Finding, FindingCategory, FindingSeverity
from backend.app.models.audit import AuditLog
from backend.app.services.model_registry import registry
from backend.forensic.image.forensic_modules import (
    analyze_jpeg_compression,
    analyze_noise_distribution,
    analyze_frequency_spectrum,
    analyze_lighting_consistency,
    analyze_landmark_geometry
)
from backend.forensic.metadata.extractor import extract_image_metadata, extract_video_metadata

class ForensicPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_analysis(
        self,
        analysis_id: int,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> Analysis:
        start_time = time.time()
        
        # Load analysis and evidence
        res = await self.db.execute(select(Analysis).where(Analysis.id == analysis_id))
        analysis = res.scalar_one_or_none()
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        res_ev = await self.db.execute(select(Evidence).where(Evidence.id == analysis.evidence_id))
        evidence = res_ev.scalar_one_or_none()
        if not evidence:
            raise ValueError(f"Evidence {analysis.evidence_id} not found")

        def emit(stage: str, data: Optional[Dict[str, Any]] = None):
            if event_callback:
                event_callback(stage, data or {})

        analysis.status = AnalysisStatus.PROCESSING
        analysis.started_at = datetime.datetime.utcnow()
        await self.db.commit()

        emit("VALIDATING", {"message": "Verifying media file integrity..."})
        file_path = evidence.storage_path
        if not os.path.exists(file_path):
            analysis.status = AnalysisStatus.FAILED
            analysis.limitations = f"Evidence file not found on disk: {file_path}"
            await self.db.commit()
            emit("FAILED", {"error": analysis.limitations})
            return analysis

        case_dir = os.path.dirname(os.path.dirname(os.path.abspath(file_path)))
        heatmaps_dir = os.path.join(case_dir, "heatmaps")
        faces_dir = os.path.join(case_dir, "faces")
        audio_dir = os.path.join(case_dir, "audio")
        os.makedirs(heatmaps_dir, exist_ok=True)
        os.makedirs(faces_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

        observations: Dict[str, Dict[str, Any]] = {}

        # -------------------------------------------------------------
        # IMAGE PIPELINE
        # -------------------------------------------------------------
        if evidence.media_type == MediaType.IMAGE:
            emit("METADATA", {"message": "Extracting EXIF and structural metadata..."})
            meta = extract_image_metadata(file_path)
            evidence.metadata_json = meta
            observations["metadata"] = {
                "score": 0.85 if meta.get("suspicious_software_tag") else 0.10,
                "confidence": 0.80,
                "available": True,
                "description": f"Metadata status: {meta.get('metadata_status')} (Software: {meta.get('software') or 'None'})"
            }

            emit("FACE_DETECTION", {"message": "Executing OpenCV YuNet face detection..."})
            image_bgr = cv2.imread(file_path)
            if image_bgr is None:
                analysis.status = AnalysisStatus.FAILED
                analysis.limitations = "Failed to decode image pixels"
                await self.db.commit()
                emit("FAILED", {"error": analysis.limitations})
                return analysis

            face_detector = registry.get_face_detector()
            faces = face_detector.detect_faces(image_bgr) if face_detector else []

            primary_face_box = None
            primary_landmarks = None

            if len(faces) > 0:
                primary_face = faces[0]
                primary_face_box = primary_face["bbox"]
                primary_landmarks = primary_face["landmarks"]

                # Save face crop
                face_crop_filename = f"face_ev{evidence.id}.jpg"
                face_crop_path = os.path.join(faces_dir, face_crop_filename)
                cv2.imwrite(face_crop_path, primary_face["face_crop"])

                emit("AI_INFERENCE", {"message": "Running real Vision Transformer deepfake inference..."})
                ai_detector = registry.get_image_ai_detector()
                if ai_detector and ai_detector.is_available():
                    ai_pred = ai_detector.predict(primary_face["face_crop"])
                    observations["vision_ai"] = {
                        "score": ai_pred["manipulation_score"],
                        "confidence": ai_pred["confidence"],
                        "available": True,
                        "model_name": ai_pred["model_name"],
                        "model_version": ai_pred["model_version"],
                        "raw_output": ai_pred["raw_logits"],
                        "bounding_box": primary_face_box,
                        "description": (
                            f"ViT model classified face as "
                            f"{'manipulated' if ai_pred['manipulation_score'] >= 0.5 else 'authentic'} "
                            f"(score: {ai_pred['manipulation_score']:.4f}, conf: {ai_pred['confidence']:.4f})."
                        )
                    }

                    emit("HEATMAPS", {"message": "Generating gradient-based saliency heatmap..."})
                    heatmap_img, overlay_img = ai_detector.generate_saliency_heatmap(primary_face["face_crop"])
                    heatmap_filename = f"heatmap_ev{evidence.id}.jpg"
                    overlay_filename = f"overlay_ev{evidence.id}.jpg"
                    cv2.imwrite(os.path.join(heatmaps_dir, heatmap_filename), heatmap_img)
                    cv2.imwrite(os.path.join(heatmaps_dir, overlay_filename), overlay_img)
                else:
                    observations["vision_ai"] = {
                        "available": False,
                        "score": None,
                        "description": "ViT detector unavailable"
                    }

                # Landmark geometry
                geom = analyze_landmark_geometry(primary_landmarks)
                observations["landmark_geometry"] = {
                    "score": geom["anomaly_score"],
                    "confidence": geom["confidence"],
                    "available": True,
                    "description": f"Facial symmetry ratio: {geom.get('facial_symmetry_ratio')}"
                }
            else:
                emit("AI_INFERENCE", {"message": "No face detected in image; evaluating full scene forensics..."})

            emit("FORENSIC_ANALYSIS", {"message": "Executing scientific compression, noise, FFT & lighting forensics..."})
            ela = analyze_jpeg_compression(image_bgr)
            observations["compression_ela"] = {
                "score": ela["anomaly_score"],
                "confidence": ela["confidence"],
                "available": True,
                "description": f"JPEG ELA standard deviation: {ela['error_std_dev']}"
            }

            noise = analyze_noise_distribution(image_bgr, primary_face_box)
            observations["noise_distribution"] = {
                "score": noise["anomaly_score"],
                "confidence": noise["confidence"],
                "available": True,
                "description": f"Noise variance ratio: {noise['noise_variance_ratio']}"
            }

            fft = analyze_frequency_spectrum(image_bgr)
            observations["frequency_spectrum"] = {
                "score": fft["anomaly_score"],
                "confidence": fft["confidence"],
                "available": True,
                "description": f"2D FFT frequency energy ratio: {fft['frequency_energy_ratio']}"
            }

            light = analyze_lighting_consistency(image_bgr, primary_face_box)
            observations["lighting_consistency"] = {
                "score": light["anomaly_score"],
                "confidence": light["confidence"],
                "available": True,
                "description": f"Illumination angle disparity: {light['illumination_angle_disparity_deg']} deg"
            }

        # -------------------------------------------------------------
        # VIDEO PIPELINE
        # -------------------------------------------------------------
        elif evidence.media_type == MediaType.VIDEO:
            emit("METADATA", {"message": "Extracting video container and stream metadata..."})
            vmeta = extract_video_metadata(file_path)
            evidence.metadata_json = vmeta
            evidence.duration = vmeta.get("duration")
            evidence.width = vmeta.get("width")
            evidence.height = vmeta.get("height")
            evidence.fps = vmeta.get("fps")
            evidence.codec = vmeta.get("video_codec")

            emit("FRAME_EXTRACTION", {"message": "Sampling video frames and tracking facial regions..."})
            v_proc = registry.get_video_processor()
            if not v_proc:
                analysis.status = AnalysisStatus.FAILED
                analysis.limitations = "Video processor models not available"
                await self.db.commit()
                emit("FAILED", {"error": analysis.limitations})
                return analysis

            v_res = v_proc.process_video(
                file_path,
                case_dir,
                mode="BALANCED",
                progress_callback=lambda p, m: emit("FRAME_EXTRACTION", {"progress": p, "message": m})
            )

            analysis.timeline_data = v_res["timeline"]

            observations["vision_ai"] = {
                "score": v_res["average_frame_score"],
                "confidence": 0.85,
                "available": True,
                "description": f"Evaluated {v_res['analyzed_frames_count']} frames. Peak frame score: {v_res['peak_frame_score']:.4f}."
            }

            temp = v_res["temporal_analysis"]
            observations["temporal_consistency"] = {
                "score": temp.get("temporal_anomaly_score", 0.0),
                "confidence": temp.get("confidence", 0.8),
                "available": True,
                "description": f"Score volatility: {temp.get('score_volatility', 0.0):.4f}, landmark drift: {temp.get('average_landmark_drift', 0.0):.4f}"
            }

            # If video has audio, process audio track and AV Sync
            if vmeta.get("has_audio"):
                emit("AUDIO_ANALYSIS", {"message": "Extracting and analyzing video audio stream..."})
                wav_path = os.path.join(audio_dir, f"audio_ev{evidence.id}.wav")
                audio_proc = registry.get_audio_processor()
                extracted = audio_proc.extract_audio_from_video(file_path, wav_path)
                
                if extracted:
                    a_res = audio_proc.analyze_audio(wav_path)
                    sig_forensics = a_res["signal_forensics"]
                    observations["audio_signal"] = {
                        "score": sig_forensics.get("signal_anomaly_indicator", 0.0),
                        "confidence": 0.75,
                        "available": True,
                        "description": f"Acoustic spectral flatness: {sig_forensics.get('spectral_flatness')}, pitch std: {sig_forensics.get('pitch_standard_deviation')}"
                    }

                    emit("AV_ANALYSIS", {"message": "Evaluating facial mouth aperture vs audio energy synchronization..."})
                    av_analyzer = registry.get_av_sync_analyzer()
                    # Read WAV samples for sync
                    import scipy.io.wavfile as wavfile
                    sr, y = wavfile.read(wav_path)
                    if y.ndim > 1: y = y.mean(axis=1)
                    sync_res = av_analyzer.analyze_sync(
                        v_res["analyzed_records"],
                        y.astype(np.float32) / 32768.0,
                        sr,
                        v_res["fps"]
                    )
                    analysis.av_sync_data = sync_res
                    observations["av_sync"] = {
                        "score": sync_res["sync_anomaly_score"],
                        "confidence": sync_res["confidence"],
                        "available": True,
                        "description": f"Estimated AV lag: {sync_res['estimated_lag_ms']} ms (corr: {sync_res['measured_correlation']})"
                    }

        # -------------------------------------------------------------
        # AUDIO PIPELINE
        # -------------------------------------------------------------
        elif evidence.media_type == MediaType.AUDIO:
            emit("AUDIO_ANALYSIS", {"message": "Executing Layer A signal forensics and Layer B speech detection..."})
            audio_proc = registry.get_audio_processor()
            a_res = audio_proc.analyze_audio(file_path)
            sig_forensics = a_res["signal_forensics"]
            observations["audio_signal"] = {
                "score": sig_forensics.get("signal_anomaly_indicator", 0.0),
                "confidence": 0.75,
                "available": True,
                "description": f"Acoustic spectral flatness: {sig_forensics.get('spectral_flatness')}, pitch: {sig_forensics.get('average_pitch_hz')} Hz"
            }
            analysis.signal_data = a_res

        # -------------------------------------------------------------
        # EVIDENCE FUSION & FINDINGS
        # -------------------------------------------------------------
        emit("FUSION", {"message": "Fusing multimodal observations and assessing conflict..."})
        fusion_engine = registry.get_fusion_engine()
        fusion_result = fusion_engine.fuse_evidence(observations)

        emit("FINDINGS", {"message": "Persisting traceable forensic findings..."})
        analysis.final_score = fusion_result["final_score"]
        analysis.confidence = fusion_result["confidence"]
        analysis.assessment = AnalysisAssessment[fusion_result["assessment"]]
        analysis.evidence_conflict = fusion_result["evidence_conflict"]
        analysis.conflict_details = fusion_result["conflict_details"]
        analysis.fusion_details = fusion_result

        # Save findings to database
        for f_data in fusion_result["findings"]:
            finding = Finding(
                analysis_id=analysis.id,
                finding_code=f_data["finding_code"],
                category=FindingCategory[f_data["category"]],
                severity=FindingSeverity[f_data["severity"]],
                confidence=f_data["confidence"],
                score=f_data["score"],
                description=f_data["description"],
                timestamp=f_data.get("timestamp"),
                frame_number=f_data.get("frame_number"),
                bounding_box=f_data.get("bounding_box"),
                model_name=f_data["model_name"],
                model_version=f_data["model_version"],
                raw_output=f_data.get("raw_output")
            )
            self.db.add(finding)

        elapsed = time.time() - start_time
        analysis.processing_time = round(elapsed, 2)
        analysis.completed_at = datetime.datetime.utcnow()
        analysis.status = AnalysisStatus.COMPLETED

        # Audit Log
        audit = AuditLog(
            case_id=evidence.case_id,
            user_id=evidence.uploaded_by,
            action="ANALYSIS_COMPLETED",
            details={
                "analysis_id": analysis.id,
                "evidence_id": evidence.id,
                "final_score": analysis.final_score,
                "assessment": str(analysis.assessment),
                "duration_seconds": analysis.processing_time
            }
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(analysis)

        emit("COMPLETED", {
            "analysis_id": analysis.id,
            "final_score": analysis.final_score,
            "assessment": str(analysis.assessment),
            "processing_time": analysis.processing_time
        })

        return analysis
