import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.models.finding import Finding, ReviewStatus
from backend.app.models.user import User
from backend.app.schemas.analysis import FindingResponse
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/findings", tags=["Findings"])

class FindingReviewRequest(BaseModel):
    review_status: str  # CONFIRMED, DISPUTED, NEEDS_REVIEW
    reviewer_notes: Optional[str] = None

@router.get("/{analysis_id}", response_model=List[FindingResponse])
async def get_findings_for_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Finding).where(Finding.analysis_id == analysis_id).order_by(Finding.id.asc()))
    findings = res.scalars().all()
    return [FindingResponse.model_validate(f) for f in findings]

@router.patch("/{finding_id}/review")
async def review_finding(
    finding_id: int,
    payload: FindingReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Investigator Review Mode (Requirements 34, 37, 38).
    Allows investigator to confirm or dispute findings without modifying raw AI outputs.
    """
    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    status_str = payload.review_status.upper()
    if status_str not in ReviewStatus.__members__:
        raise HTTPException(status_code=400, detail=f"Invalid review status: {payload.review_status}")

    finding.review_status = ReviewStatus[status_str]
    finding.reviewer_id = current_user.id
    finding.reviewer_notes = payload.reviewer_notes
    finding.reviewed_at = datetime.datetime.utcnow()

    await db.commit()
    await db.refresh(finding)

    return {
        "finding_id": finding.id,
        "finding_code": finding.finding_code,
        "ai_score": finding.score,
        "ai_confidence": finding.confidence,
        "review_status": finding.review_status.value,
        "reviewer_id": finding.reviewer_id,
        "reviewer_notes": finding.reviewer_notes,
        "reviewed_at": finding.reviewed_at.isoformat() if finding.reviewed_at else None,
        "message": "Investigator review registered. AI raw inference provenance preserved."
    }
