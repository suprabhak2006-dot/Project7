from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.models.analysis import Analysis
from backend.app.models.user import User
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/timeline", tags=["Timeline"])

@router.get("/{analysis_id}")
async def get_timeline_for_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return {
        "analysis_id": analysis.id,
        "evidence_id": analysis.evidence_id,
        "timeline": analysis.timeline_data or [],
        "av_sync": analysis.av_sync_data or {}
    }
