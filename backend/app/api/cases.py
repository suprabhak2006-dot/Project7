import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.db.session import get_db
from backend.app.models.case import Case, CaseStatus, CasePriority
from backend.app.models.evidence import Evidence
from backend.app.models.audit import AuditLog
from backend.app.models.user import User, UserRole
from backend.app.schemas.case import CaseCreate, CaseUpdate, CaseResponse
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/cases", tags=["Cases"])

@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_in: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Generate unique case number: CASE-YYYY-XXXX
    year = datetime.datetime.utcnow().year
    count_res = await db.execute(select(func.count(Case.id)))
    total_cases = count_res.scalar_one() or 0
    case_number = f"CASE-{year}-{(total_cases + 1):04d}"

    case = Case(
        case_number=case_number,
        title=case_in.title,
        description=case_in.description,
        priority=case_in.priority,
        status=CaseStatus.OPEN,
        created_by=current_user.id
    )
    db.add(case)
    await db.flush()

    # Log audit
    audit = AuditLog(
        case_id=case.id,
        user_id=current_user.id,
        action="CASE_CREATED",
        details={"case_number": case.case_number, "title": case.title}
    )
    db.add(audit)
    await db.commit()
    await db.refresh(case)

    resp = CaseResponse.model_validate(case)
    resp.evidence_count = 0
    return resp

@router.get("", response_model=List[CaseResponse])
async def list_cases(
    status_filter: Optional[CaseStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Case).order_by(Case.created_at.desc())
    if status_filter:
        query = query.where(Case.status == status_filter)

    res = await db.execute(query)
    cases = res.scalars().all()

    # Count evidence for each case
    results = []
    for c in cases:
        ev_count_res = await db.execute(select(func.count(Evidence.id)).where(Evidence.case_id == c.id))
        count = ev_count_res.scalar_one() or 0
        resp = CaseResponse.model_validate(c)
        resp.evidence_count = count
        results.append(resp)

    return results

@router.get("/{id}", response_model=CaseResponse)
async def get_case(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Case).where(Case.id == id))
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    ev_count_res = await db.execute(select(func.count(Evidence.id)).where(Evidence.case_id == case.id))
    count = ev_count_res.scalar_one() or 0
    resp = CaseResponse.model_validate(case)
    resp.evidence_count = count
    return resp

@router.patch("/{id}", response_model=CaseResponse)
async def update_case(
    id: int,
    case_in: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Case).where(Case.id == id))
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    if case_in.title is not None:
        case.title = case_in.title
    if case_in.description is not None:
        case.description = case_in.description
    if case_in.status is not None:
        case.status = case_in.status
    if case_in.priority is not None:
        case.priority = case_in.priority

    case.updated_at = datetime.datetime.utcnow()

    audit = AuditLog(
        case_id=case.id,
        user_id=current_user.id,
        action="CASE_UPDATED",
        details={"status": str(case.status), "priority": str(case.priority)}
    )
    db.add(audit)

    await db.commit()
    await db.refresh(case)

    ev_count_res = await db.execute(select(func.count(Evidence.id)).where(Evidence.case_id == case.id))
    count = ev_count_res.scalar_one() or 0
    resp = CaseResponse.model_validate(case)
    resp.evidence_count = count
    return resp

@router.get("/{id}/evidence")
async def list_case_evidence(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ev_res = await db.execute(select(Evidence).where(Evidence.case_id == id).order_by(Evidence.uploaded_at.desc()))
    return ev_res.scalars().all()

