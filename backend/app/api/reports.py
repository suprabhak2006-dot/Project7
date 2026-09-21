import os
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.models.report import Report
from backend.app.models.analysis import Analysis
from backend.app.models.user import User
from backend.app.schemas.analysis import ReportResponse
from backend.app.api.deps import get_current_user
from backend.app.services.report import ForensicReportEngine

router = APIRouter(prefix="/reports", tags=["Reports"])

def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()

@router.post("/{analysis_id}/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    engine = ForensicReportEngine(db)
    try:
        report = await engine.generate_report(analysis_id, current_user.id)
        return ReportResponse.model_validate(report)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{id}", response_model=ReportResponse)
async def get_report_metadata(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Report).where(Report.id == id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return ReportResponse.model_validate(report)

@router.get("/{id}/download")
async def download_report_pdf(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Report).where(Report.id == id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if not os.path.exists(report.report_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report PDF file missing from disk")

    return FileResponse(
        report.report_path,
        media_type="application/pdf",
        filename=f"{report.report_number}.pdf"
    )

@router.post("/{id}/verify")
async def verify_report_integrity(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Report).where(Report.id == id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if not os.path.exists(report.report_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report PDF file missing from disk")

    recalculated = compute_sha256(report.report_path)
    is_valid = recalculated == report.report_sha256

    return {
        "report_id": report.id,
        "report_number": report.report_number,
        "stored_sha256": report.report_sha256,
        "recalculated_sha256": recalculated,
        "status": "INTEGRITY_VERIFIED" if is_valid else "INTEGRITY_MISMATCH"
    }
