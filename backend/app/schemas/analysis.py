from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel
from backend.app.models.analysis import AnalysisStatus, AnalysisAssessment
from backend.app.models.finding import FindingCategory, FindingSeverity

class AnalysisResponse(BaseModel):
    id: int
    evidence_id: int
    status: AnalysisStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time: Optional[float]
    inference_device: str
    pipeline_version: str
    final_score: Optional[float]
    confidence: Optional[float]
    assessment: Optional[AnalysisAssessment]
    evidence_conflict: bool
    conflict_details: Optional[str]
    limitations: Optional[str]
    fusion_details: Optional[Dict[str, Any]]
    timeline_data: Optional[List[Dict[str, Any]]]
    av_sync_data: Optional[Dict[str, Any]]
    signal_data: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

class FindingResponse(BaseModel):
    id: int
    analysis_id: int
    finding_code: str
    category: FindingCategory
    severity: FindingSeverity
    confidence: float
    score: float
    description: str
    timestamp: Optional[float]
    frame_number: Optional[int]
    bounding_box: Optional[Any]
    model_name: str
    model_version: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReportResponse(BaseModel):
    id: int
    case_id: int
    analysis_id: int
    report_number: str
    report_sha256: str
    generated_by: int
    generated_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    case_id: Optional[int]
    user_id: Optional[int]
    action: str
    ip_address: Optional[str]
    details: Optional[Dict[str, Any]]
    timestamp: datetime

    class Config:
        from_attributes = True
