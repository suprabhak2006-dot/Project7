from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.db.session import get_db
from backend.app.models.case import Case, CaseStatus
from backend.app.models.evidence import Evidence, MediaType
from backend.app.models.analysis import Analysis, AnalysisStatus, AnalysisAssessment
from backend.app.models.finding import Finding, FindingCategory
from backend.app.models.report import Report
from backend.app.models.user import User
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    # 1. Total & Active Cases
    total_cases_res = await db.execute(select(func.count(Case.id)))
    total_cases = total_cases_res.scalar_one() or 0

    active_cases_res = await db.execute(
        select(func.count(Case.id)).where(Case.status.in_([CaseStatus.OPEN, CaseStatus.IN_PROGRESS, CaseStatus.UNDER_REVIEW]))
    )
    active_cases = active_cases_res.scalar_one() or 0

    # 2. Total Evidence
    total_ev_res = await db.execute(select(func.count(Evidence.id)))
    total_evidence = total_ev_res.scalar_one() or 0

    # 3. Analyses counts
    total_analyses_res = await db.execute(select(func.count(Analysis.id)))
    total_analyses = total_analyses_res.scalar_one() or 0

    completed_analyses_res = await db.execute(
        select(func.count(Analysis.id)).where(Analysis.status == AnalysisStatus.COMPLETED)
    )
    completed_analyses = completed_analyses_res.scalar_one() or 0

    processing_jobs_res = await db.execute(
        select(func.count(Analysis.id)).where(Analysis.status.in_([AnalysisStatus.QUEUED, AnalysisStatus.PROCESSING]))
    )
    processing_jobs = processing_jobs_res.scalar_one() or 0

    # 4. High-Likelihood Findings & Reports
    high_findings_res = await db.execute(
        select(func.count(Finding.id)).where(Finding.score >= 0.70)
    )
    high_findings = high_findings_res.scalar_one() or 0

    total_reports_res = await db.execute(select(func.count(Report.id)))
    total_reports = total_reports_res.scalar_one() or 0

    # 5. Media Types Breakdown
    media_breakdown = {}
    for mtype in MediaType:
        count_res = await db.execute(select(func.count(Evidence.id)).where(Evidence.media_type == mtype))
        media_breakdown[mtype.value] = count_res.scalar_one() or 0

    # 6. Findings by Category
    findings_by_category = {}
    for cat in FindingCategory:
        f_count_res = await db.execute(select(func.count(Finding.id)).where(Finding.category == cat))
        findings_by_category[cat.value] = f_count_res.scalar_one() or 0

    # 7. Analysis Outcomes
    assessment_distribution = {}
    for asm in AnalysisAssessment:
        asm_count_res = await db.execute(select(func.count(Analysis.id)).where(Analysis.assessment == asm))
        assessment_distribution[asm.value] = asm_count_res.scalar_one() or 0

    # 8. Recent Cases
    recent_cases_res = await db.execute(select(Case).order_by(Case.created_at.desc()).limit(5))
    recent_cases = [
        {
            "id": c.id,
            "case_number": c.case_number,
            "title": c.title,
            "status": c.status.value,
            "priority": c.priority.value,
            "created_at": c.created_at.isoformat()
        }
        for c in recent_cases_res.scalars().all()
    ]

    return {
        "cards": {
            "active_cases": active_cases,
            "total_cases": total_cases,
            "total_evidence": total_evidence,
            "completed_analyses": completed_analyses,
            "processing_jobs": processing_jobs,
            "high_findings": high_findings,
            "total_reports": total_reports
        },
        "media_types": media_breakdown,
        "findings_by_category": findings_by_category,
        "outcomes": assessment_distribution,
        "recent_cases": recent_cases
    }
