from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from backend.app.models.case import CaseStatus, CasePriority

class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: CasePriority = CasePriority.MEDIUM

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None

class CaseResponse(BaseModel):
    id: int
    case_number: str
    title: str
    description: Optional[str]
    status: CaseStatus
    priority: CasePriority
    created_by: int
    created_at: datetime
    updated_at: datetime
    evidence_count: Optional[int] = 0

    class Config:
        from_attributes = True
