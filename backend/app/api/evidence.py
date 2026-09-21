import os
import hashlib
import shutil
import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.case import Case
from backend.app.models.evidence import Evidence, MediaType
from backend.app.models.audit import AuditLog
from backend.app.models.user import User
from backend.app.schemas.evidence import EvidenceResponse, IntegrityVerificationResponse
from backend.app.api.deps import get_current_user
from backend.forensic.metadata.extractor import extract_image_metadata, extract_video_metadata

router = APIRouter(prefix="/evidence", tags=["Evidence"])

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
ALLOWED_AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac"}

def compute_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def compute_sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()

@router.post("/upload", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify case exists
    res_case = await db.execute(select(Case).where(Case.id == case_id))
    case = res_case.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    filename = os.path.basename(file.filename or "upload")
    ext = os.path.splitext(filename)[1].lower()

    if ext in ALLOWED_IMAGE_EXTS:
        media_type = MediaType.IMAGE
    elif ext in ALLOWED_VIDEO_EXTS:
        media_type = MediaType.VIDEO
    elif ext in ALLOWED_AUDIO_EXTS:
        media_type = MediaType.AUDIO
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: images, videos, audio."
        )

    # Read bytes and compute cryptographic SHA-256
    content = await file.read()
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty (0 bytes).")
    
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB.")

    sha256_hash = compute_sha256_bytes(content)

    # Setup storage directory: storage/cases/{case_number}/original/
    case_dir = os.path.join(settings.STORAGE_PATH, "cases", case.case_number)
    original_dir = os.path.join(case_dir, "original")
    os.makedirs(original_dir, exist_ok=True)

    # Generate sequential evidence number EV-XXXXX
    count_res = await db.execute(select(func.count(Evidence.id)))
    total_ev = count_res.scalar_one() or 0
    evidence_number = f"EV-{(total_ev + 1):05d}"

    safe_name = f"{evidence_number}_{uuid.uuid4().hex[:8]}_{filename}"
    storage_path = os.path.join(original_dir, safe_name)

    # Write file bytes to disk (IMMUTABLE ORIGINAL)
    with open(storage_path, "wb") as f:
        f.write(content)

    # Extract initial basic metadata
    metadata = {}
    duration = None
    width = None
    height = None
    fps = None
    codec = None

    if media_type == MediaType.IMAGE:
        meta = extract_image_metadata(storage_path)
        metadata = meta
        width = meta.get("width")
        height = meta.get("height")
    elif media_type == MediaType.VIDEO:
        vmeta = extract_video_metadata(storage_path)
        metadata = vmeta
        duration = vmeta.get("duration")
        width = vmeta.get("width")
        height = vmeta.get("height")
        fps = vmeta.get("fps")
        codec = vmeta.get("video_codec")

    evidence = Evidence(
        case_id=case.id,
        evidence_number=evidence_number,
        filename=filename,
        mime_type=file.content_type or "application/octet-stream",
        media_type=media_type,
        file_size=file_size,
        sha256=sha256_hash,
        storage_path=storage_path,
        duration=duration,
        width=width,
        height=height,
        fps=fps,
        codec=codec,
        metadata_json=metadata,
        uploaded_by=current_user.id
    )
    db.add(evidence)
    await db.flush()

    # Log chain of custody & audit
    audit = AuditLog(
        case_id=case.id,
        user_id=current_user.id,
        action="EVIDENCE_UPLOADED",
        details={
            "evidence_id": evidence.id,
            "evidence_number": evidence.evidence_number,
            "filename": filename,
            "sha256": sha256_hash,
            "size_bytes": file_size
        }
    )
    db.add(audit)

    await db.commit()
    await db.refresh(evidence)
    return EvidenceResponse.model_validate(evidence)

@router.get("/{id}", response_model=EvidenceResponse)
async def get_evidence(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Evidence).where(Evidence.id == id))
    evidence = res.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return EvidenceResponse.model_validate(evidence)

@router.post("/{id}/verify-integrity", response_model=IntegrityVerificationResponse)
async def verify_integrity(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Evidence).where(Evidence.id == id))
    evidence = res.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    if not os.path.exists(evidence.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original evidence file missing from storage")

    # Recalculate hash from stored original bytes
    recalculated = compute_sha256_file(evidence.storage_path)
    status_str = "INTEGRITY_VERIFIED" if recalculated == evidence.sha256 else "INTEGRITY_MISMATCH"

    audit = AuditLog(
        case_id=evidence.case_id,
        user_id=current_user.id,
        action="INTEGRITY_VERIFICATION",
        details={
            "evidence_id": evidence.id,
            "stored_sha256": evidence.sha256,
            "recalculated_sha256": recalculated,
            "status": status_str
        }
    )
    db.add(audit)
    await db.commit()

    return IntegrityVerificationResponse(
        evidence_id=evidence.id,
        evidence_number=evidence.evidence_number,
        stored_sha256=evidence.sha256,
        recalculated_sha256=recalculated,
        status=status_str,
        timestamp=datetime.datetime.utcnow()
    )

@router.get("/{id}/file")
async def get_evidence_raw_file(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Evidence).where(Evidence.id == id))
    evidence = res.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    if not os.path.exists(evidence.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found on disk")

    return FileResponse(evidence.storage_path, media_type=evidence.mime_type, filename=evidence.filename)
