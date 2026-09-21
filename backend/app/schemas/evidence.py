from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from backend.app.models.evidence import MediaType

class EvidenceResponse(BaseModel):
    id: int
    case_id: int
    evidence_number: str
    filename: str
    mime_type: str
    media_type: MediaType
    file_size: int
    sha256: str
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    codec: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    uploaded_by: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class IntegrityVerificationResponse(BaseModel):
    evidence_id: int
    evidence_number: str
    stored_sha256: str
    recalculated_sha256: str
    status: str  # "INTEGRITY_VERIFIED" or "INTEGRITY_MISMATCH"
    timestamp: datetime
