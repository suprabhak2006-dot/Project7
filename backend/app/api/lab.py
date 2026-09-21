import os
import io
import cv2
import numpy as np
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.models.evidence import Evidence, MediaType
from backend.forensic.image.forensic_modules import (
    inspect_pixel_region,
    apply_forensic_filter,
    compute_image_histograms,
    analyze_compression_detailed,
    analyze_color_consistency,
    analyze_lighting_consistency
)
from backend.forensic.video.processor import VideoForensicProcessor
from backend.forensic.audio.processor import AudioForensicProcessor
from backend.forensic.similarity.engine import MediaSimilarityEngine
from backend.forensic.metadata.provenance import MediaProvenanceAnalyzer

router = APIRouter(prefix="/evidence", tags=["Forensic Labs & Evidence Inspection"])

class PixelInspectRequest(BaseModel):
    x: int
    y: int
    window_size: int = 16

class CompareRequest(BaseModel):
    evidence_id_1: int
    evidence_id_2: int

@router.get("/{evidence_id}/provenance")
async def get_evidence_provenance(
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ev = await db.get(Evidence, evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    prov = MediaProvenanceAnalyzer.inspect_file_structure_and_provenance(ev.storage_path)
    return prov

@router.post("/{evidence_id}/pixel-inspect")
async def inspect_pixel(
    evidence_id: int,
    payload: PixelInspectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Forensic pixel-level inspection mode (Requirement 13).
    """
    ev = await db.get(Evidence, evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    img_bgr = cv2.imread(ev.storage_path)
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Cannot decode image for pixel inspection")

    res = inspect_pixel_region(img_bgr, payload.x, payload.y, payload.window_size)
    return res

@router.get("/{evidence_id}/filter/{filter_name}")
async def get_filtered_image(
    evidence_id: int,
    filter_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Forensic filter laboratory (Requirement 14).
    Applies real filter to genuine evidence image and returns image/jpeg.
    """
    ev = await db.get(Evidence, evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    img_bgr = cv2.imread(ev.storage_path)
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Unable to load evidence image")

    filtered_bgr = apply_forensic_filter(img_bgr, filter_name)
    success, buffer = cv2.imencode(".jpg", filtered_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not success:
        raise HTTPException(status_code=500, detail="Filter encoding failed")

    return Response(content=buffer.tobytes(), media_type="image/jpeg")

@router.get("/{evidence_id}/histograms")
async def get_histograms(
    evidence_id: int,
    fx: Optional[int] = Query(None),
    fy: Optional[int] = Query(None),
    fw: Optional[int] = Query(None),
    fh: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Image histogram analysis and Face vs Background comparison (Requirement 15).
    """
    ev = await db.get(Evidence, evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    img_bgr = cv2.imread(ev.storage_path)
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Unable to load evidence image")

    face_box = [fx, fy, fw, fh] if (fx is not None and fy is not None and fw is not None and fh is not None) else None
    return compute_image_histograms(img_bgr, face_box)

@router.get("/{evidence_id}/compression")
async def get_compression_forensics(
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deep compression forensics: JPEG quantization tables and 8x8 DCT blockiness (Requirement 16).
    """
    ev = await db.get(Evidence, evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    return analyze_compression_detailed(ev.storage_path)

@router.get("/{evidence_id}/color-lighting")
async def get_color_and_lighting(
    evidence_id: int,
    fx: Optional[int] = Query(None),
    fy: Optional[int] = Query(None),
    fw: Optional[int] = Query(None),
    fh: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lighting and color consistency analysis (Requirements 19 & 20).
    """
    ev = await db.get(Evidence, evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    img_bgr = cv2.imread(ev.storage_path)
    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Unable to load evidence image")

    face_box = [fx, fy, fw, fh] if (fx is not None and fy is not None and fw is not None and fh is not None) else None
    lighting = analyze_lighting_consistency(img_bgr, face_box)
    color = analyze_color_consistency(img_bgr, face_box)

    return {
        "lighting_analysis": lighting,
        "color_analysis": color
    }

@router.get("/{evidence_id}/video-lab")
async def get_video_lab(
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Video quality scorecard, scene detection, and temporal consistency matrix (Requirements 21-24).
    """
    ev = await db.get(Evidence, evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if ev.media_type != MediaType.VIDEO:
        raise HTTPException(status_code=400, detail="Evidence is not a video file")

    quality = VideoForensicProcessor.analyze_video_quality(ev.storage_path)
    scenes = VideoForensicProcessor.detect_scenes(ev.storage_path)

    # Sample consecutive frames for temporal matrix
    cap = cv2.VideoCapture(ev.storage_path)
    frames = []
    while cap.isOpened() and len(frames) < 10:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()

    temp_matrix = VideoForensicProcessor.compute_temporal_consistency_matrix(frames)

    return {
        "quality_scorecard": quality,
        "scenes": scenes,
        "temporal_consistency_matrix": temp_matrix
    }

@router.get("/{evidence_id}/audio-lab")
async def get_audio_lab(
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Audio Forensics Lab: waveform, energy curve, pitch contour, segments, splice detections (Requirements 25-29).
    """
    ev = await db.get(Evidence, evidence_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    wav_path = ev.storage_path
    if ev.media_type == MediaType.VIDEO:
        temp_wav = os.path.splitext(ev.storage_path)[0] + "_extracted.wav"
        if not os.path.exists(temp_wav):
            proc = AudioForensicProcessor()
            proc.extract_audio_from_video(ev.storage_path, temp_wav)
        wav_path = temp_wav

    proc = AudioForensicProcessor()
    data = proc.generate_audio_lab_data(wav_path)
    return data

@router.post("/compare")
async def compare_evidence_pair(
    payload: CompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Evidence Comparison View (Requirements 9, 44, 46):
    Cryptographic equality (SHA-256) vs Visual similarity (pHash, dHash, color histogram).
    """
    ev1 = await db.get(Evidence, payload.evidence_id_1)
    ev2 = await db.get(Evidence, payload.evidence_id_2)
    if not ev1 or not ev2:
        raise HTTPException(status_code=404, detail="One or both evidence items not found")

    sha256_match = bool(ev1.sha256.lower() == ev2.sha256.lower())

    similarity_metrics = {}
    if ev1.media_type == MediaType.IMAGE and ev2.media_type == MediaType.IMAGE:
        similarity_metrics = MediaSimilarityEngine.compare_images(ev1.storage_path, ev2.storage_path)

    return {
        "evidence_1": {
            "id": ev1.id,
            "evidence_number": ev1.evidence_number,
            "filename": ev1.filename,
            "media_type": ev1.media_type.value,
            "file_size": ev1.file_size,
            "sha256": ev1.sha256,
            "resolution": f"{ev1.width}x{ev1.height}" if ev1.width else None,
            "uploaded_at": ev1.uploaded_at.isoformat()
        },
        "evidence_2": {
            "id": ev2.id,
            "evidence_number": ev2.evidence_number,
            "filename": ev2.filename,
            "media_type": ev2.media_type.value,
            "file_size": ev2.file_size,
            "sha256": ev2.sha256,
            "resolution": f"{ev2.width}x{ev2.height}" if ev2.width else None,
            "uploaded_at": ev2.uploaded_at.isoformat()
        },
        "cryptographic_equality": "MATCH" if sha256_match else "DIFFERENT",
        "sha256_match": sha256_match,
        "visual_similarity": similarity_metrics,
        "is_potential_duplicate": sha256_match or similarity_metrics.get("is_duplicate_candidate", False),
        "disclaimer": "Cryptographic equality verifies identical bitstreams; visual similarity evaluates perceptual and geometric variance."
    }
