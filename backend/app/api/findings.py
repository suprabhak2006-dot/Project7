from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.models.finding import Finding
from backend.app.models.user import User
from backend.app.schemas.analysis import FindingResponse
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/findings", tags=["Findings"])

@router.get("/{analysis_id}", response_model=List[FindingResponse])
async def get_findings_for_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Finding).where(Finding.analysis_id == analysis_id).order_by(Finding.id.asc()))
    findings = res.scalars().all()
    return [FindingResponse.model_validate(f) for f in findings]
