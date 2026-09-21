import asyncio
import json
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import get_db, AsyncSessionLocal
from backend.app.models.evidence import Evidence
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.audit import AuditLog
from backend.app.models.user import User
from backend.app.schemas.analysis import AnalysisResponse
from backend.app.api.deps import get_current_user
from backend.app.services.pipeline import ForensicPipeline

router = APIRouter(tags=["Analysis"])

# In-memory pub-sub for live analysis pipeline events
_event_subscribers: Dict[int, List[asyncio.Queue]] = {}

def broadcast_event(analysis_id: int, stage: str, data: Dict[str, Any]):
    queues = _event_subscribers.get(analysis_id, [])
    payload = {"stage": stage, "data": data}
    for q in queues:
        q.put_nowait(payload)

async def run_pipeline_task(analysis_id: int):
    async with AsyncSessionLocal() as session:
        pipeline = ForensicPipeline(session)
        def on_event(stage: str, data: Dict[str, Any]):
            broadcast_event(analysis_id, stage, data)
        try:
            await pipeline.execute_analysis(analysis_id, event_callback=on_event)
        except Exception as e:
            print(f"[!] Pipeline error for analysis {analysis_id}: {e}")
            res = await session.execute(select(Analysis).where(Analysis.id == analysis_id))
            analysis = res.scalar_one_or_none()
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                analysis.limitations = f"Pipeline execution failed: {str(e)}"
                await session.commit()
            broadcast_event(analysis_id, "FAILED", {"error": str(e)})

@router.post("/evidence/{evidence_id}/analyze", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(
    evidence_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res_ev = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = res_ev.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    analysis = Analysis(
        evidence_id=evidence.id,
        status=AnalysisStatus.QUEUED,
        inference_device="CPU",
        pipeline_version="1.0.0"
    )
    db.add(analysis)
    await db.flush()

    audit = AuditLog(
        case_id=evidence.case_id,
        user_id=current_user.id,
        action="ANALYSIS_QUEUED",
        details={"analysis_id": analysis.id, "evidence_id": evidence.id}
    )
    db.add(audit)
    await db.commit()
    await db.refresh(analysis)

    # Launch background forensic pipeline
    background_tasks.add_task(run_pipeline_task, analysis.id)

    return AnalysisResponse.model_validate(analysis)

@router.get("/analysis/{id}", response_model=AnalysisResponse)
async def get_analysis(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Analysis).where(Analysis.id == id))
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return AnalysisResponse.model_validate(analysis)

@router.get("/analysis/{id}/status")
async def get_analysis_status(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Analysis).where(Analysis.id == id))
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return {
        "id": analysis.id,
        "evidence_id": analysis.evidence_id,
        "status": str(analysis.status),
        "started_at": analysis.started_at,
        "completed_at": analysis.completed_at,
        "processing_time": analysis.processing_time
    }

@router.get("/analysis/{id}/events")
async def stream_analysis_events(id: int):
    """
    Server-Sent Events (SSE) stream for real-time forensic pipeline state updates.
    """
    queue = asyncio.Queue()
    _event_subscribers.setdefault(id, []).append(queue)

    async def event_generator():
        try:
            # Yield initial connect event
            yield f"data: {json.dumps({'stage': 'CONNECTED', 'data': {'analysis_id': id}})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event["stage"] in ("COMPLETED", "FAILED"):
                        break
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            if id in _event_subscribers and queue in _event_subscribers[id]:
                _event_subscribers[id].remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
