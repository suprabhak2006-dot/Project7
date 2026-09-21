from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.models.audit import AuditLog
from backend.app.models.user import User
from backend.app.schemas.analysis import AuditLogResponse
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("/{case_id}", response_model=List[AuditLogResponse])
async def get_audit_trail_for_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(
        select(AuditLog).where(AuditLog.case_id == case_id).order_by(AuditLog.timestamp.desc())
    )
    logs = res.scalars().all()
    return [AuditLogResponse.model_validate(l) for l in logs]
