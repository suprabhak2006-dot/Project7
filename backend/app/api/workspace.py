import os
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.app.db.session import get_db
from backend.app.core.config import settings
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.models.case import Case, CaseStatus, CasePriority
from backend.app.models.evidence import Evidence
from backend.app.models.subject import Subject
from backend.app.models.face_track import FaceTrack
from backend.app.models.annotation import Annotation, AnnotationType
from backend.app.models.case_event import CaseEvent, EventType
from backend.app.models.finding import Finding
from backend.app.models.report import Report
from backend.app.models.audit import AuditLog
from backend.forensic.provenance.manifest import CaseManifestExporter

router = APIRouter(tags=["Investigation Workspace"])

class SubjectCreate(BaseModel):
    label: str
    notes: Optional[str] = None

class AnnotationCreate(BaseModel):
    evidence_id: Optional[int] = None
    type: str = "NOTE"  # NOTE, BOOKMARK, HIGHLIGHT
    timestamp: Optional[float] = None
    region_coords: Optional[Dict[str, Any]] = None
    content: str
    tags: Optional[str] = None

@router.get("/cases/{case_id}/workspace")
async def get_case_workspace(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns full persistent investigation workspace state for a Case (Requirement 1):
    Case, Evidence, Subjects, Face Tracks, Findings, Annotations, Events, Reports, Audit.
    """
    case_res = await db.execute(select(Case).where(Case.id == case_id))
    case = case_res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    ev_res = await db.execute(select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.uploaded_at.desc()))
    evidence_items = ev_res.scalars().all()

    sub_res = await db.execute(select(Subject).where(Subject.case_id == case_id))
    subjects = sub_res.scalars().all()

    ann_res = await db.execute(select(Annotation).where(Annotation.case_id == case_id).order_by(Annotation.created_at.desc()))
    annotations = ann_res.scalars().all()

    evt_res = await db.execute(select(CaseEvent).where(CaseEvent.case_id == case_id).order_by(CaseEvent.wall_clock_time.asc()))
    events = evt_res.scalars().all()

    rep_res = await db.execute(select(Report).where(Report.case_id == case_id).order_by(Report.created_at.desc()))
    reports = rep_res.scalars().all()

    # Collect face tracks for evidence in this case
    ev_ids = [e.id for e in evidence_items]
    face_tracks = []
    if ev_ids:
        ft_res = await db.execute(select(FaceTrack).where(FaceTrack.evidence_id.in_(ev_ids)))
        face_tracks = ft_res.scalars().all()

    return {
        "case": {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": case.status.value,
            "priority": case.priority.value,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
        },
        "evidence_count": len(evidence_items),
        "subjects": [
            {"id": s.id, "label": s.label, "notes": s.notes, "created_at": s.created_at.isoformat()}
            for s in subjects
        ],
        "face_tracks": [
            {
                "id": ft.id,
                "evidence_id": ft.evidence_id,
                "subject_id": ft.subject_id,
                "track_id_code": ft.track_id_code,
                "start_time": ft.start_time,
                "end_time": ft.end_time,
                "frames_count": ft.frames_count,
                "avg_confidence": ft.avg_confidence,
                "representative_frame_path": ft.representative_frame_path,
                "geometry_stability": ft.geometry_stability,
                "texture_consistency": ft.texture_consistency,
                "boundary_anomaly_score": ft.boundary_anomaly_score,
            }
            for ft in face_tracks
        ],
        "annotations": [
            {
                "id": a.id,
                "evidence_id": a.evidence_id,
                "type": a.type.value,
                "timestamp": a.timestamp,
                "region_coords": a.region_coords,
                "content": a.content,
                "tags": a.tags,
                "created_at": a.created_at.isoformat(),
            }
            for a in annotations
        ],
        "events": [
            {
                "id": ev.id,
                "evidence_id": ev.evidence_id,
                "event_type": ev.event_type.value,
                "timestamp_in_media": ev.timestamp_in_media,
                "wall_clock_time": ev.wall_clock_time.isoformat(),
                "title": ev.title,
                "description": ev.description,
                "severity": ev.severity,
            }
            for ev in events
        ],
        "reports_count": len(reports),
    }

@router.get("/cases/{case_id}/graph")
async def get_case_investigation_graph(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates dynamic nodes and edges for the Interactive Investigation Case Graph (Requirement 2).
    Nodes: Case, Evidence, Subject, FaceTrack, Finding, Report.
    Edges: Contains, Detected In, Associated With, Generated From.
    """
    case_res = await db.execute(select(Case).where(Case.id == case_id))
    case = case_res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    ev_res = await db.execute(select(Evidence).where(Evidence.case_id == case_id))
    evidence_items = ev_res.scalars().all()

    sub_res = await db.execute(select(Subject).where(Subject.case_id == case_id))
    subjects = sub_res.scalars().all()

    rep_res = await db.execute(select(Report).where(Report.case_id == case_id))
    reports = rep_res.scalars().all()

    nodes = []
    edges = []

    # Root Case Node
    case_node_id = f"case_{case.id}"
    nodes.append({
        "id": case_node_id,
        "label": f"Case: {case.case_number}",
        "type": "CASE",
        "details": {"title": case.title, "status": case.status.value, "priority": case.priority.value}
    })

    # Evidence Nodes & Edges
    for ev in evidence_items:
        ev_node_id = f"evidence_{ev.id}"
        nodes.append({
            "id": ev_node_id,
            "label": f"{ev.evidence_number} ({ev.media_type.value})",
            "type": "EVIDENCE",
            "details": {"filename": ev.filename, "size": ev.file_size, "sha256": ev.sha256[:12] + "..."}
        })
        edges.append({
            "id": f"e_case_{ev.id}",
            "source": case_node_id,
            "target": ev_node_id,
            "label": "Contains"
        })

    # Subject Nodes & Edges
    for s in subjects:
        sub_node_id = f"subject_{s.id}"
        nodes.append({
            "id": sub_node_id,
            "label": s.label,
            "type": "SUBJECT",
            "details": {"notes": s.notes}
        })
        edges.append({
            "id": f"e_sub_{s.id}",
            "source": case_node_id,
            "target": sub_node_id,
            "label": "Associated Subject"
        })

    # Reports Nodes & Edges
    for r in reports:
        rep_node_id = f"report_{r.id}"
        nodes.append({
            "id": rep_node_id,
            "label": f"Report #{r.id}",
            "type": "REPORT",
            "details": {"hash": r.report_hash[:12] + "...", "created_at": r.created_at.isoformat()}
        })
        edges.append({
            "id": f"e_rep_{r.id}",
            "source": case_node_id,
            "target": rep_node_id,
            "label": "Generated From"
        })

    return {"nodes": nodes, "edges": edges}

@router.get("/cases/{case_id}/subjects")
async def list_subjects(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Subject).where(Subject.case_id == case_id).order_by(Subject.created_at.asc()))
    subjects = res.scalars().all()
    return subjects

@router.post("/cases/{case_id}/subjects")
async def create_subject(
    case_id: int,
    payload: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    sub = Subject(case_id=case_id, label=payload.label, notes=payload.notes)
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub

@router.get("/cases/{case_id}/annotations")
async def list_annotations(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Annotation).where(Annotation.case_id == case_id).order_by(Annotation.created_at.desc()))
    return res.scalars().all()

@router.post("/cases/{case_id}/annotations")
async def create_annotation(
    case_id: int,
    payload: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    ann_type = AnnotationType.NOTE
    if payload.type.upper() == "BOOKMARK":
        ann_type = AnnotationType.BOOKMARK
    elif payload.type.upper() == "HIGHLIGHT":
        ann_type = AnnotationType.HIGHLIGHT

    ann = Annotation(
        case_id=case_id,
        evidence_id=payload.evidence_id,
        user_id=current_user.id,
        type=ann_type,
        timestamp=payload.timestamp,
        region_coords=payload.region_coords,
        content=payload.content,
        tags=payload.tags
    )
    db.add(ann)

    # Add to unified chronological timeline (Requirement 31 & 32)
    evt = CaseEvent(
        case_id=case_id,
        evidence_id=payload.evidence_id,
        event_type=EventType.INVESTIGATOR_NOTE,
        timestamp_in_media=payload.timestamp,
        title=f"Investigator Annotation ({payload.type.upper()})",
        description=payload.content[:180],
        severity="INFO"
    )
    db.add(evt)

    await db.commit()
    await db.refresh(ann)
    return ann

@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ann = await db.get(Annotation, annotation_id)
    if not ann:
        raise HTTPException(status_code=404, detail="Annotation not found")
    await db.delete(ann)
    await db.commit()
    return {"message": "Annotation deleted successfully"}

@router.get("/cases/{case_id}/manifest")
async def export_case_manifest(
    case_id: int,
    format: str = Query("json", pattern="^(json|csv)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exports cryptographic evidence manifest (Requirement 48).
    """
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    ev_res = await db.execute(select(Evidence).where(Evidence.case_id == case_id))
    evidence_items = [
        {
            "id": e.id,
            "evidence_number": e.evidence_number,
            "filename": e.filename,
            "media_type": e.media_type.value,
            "mime_type": e.mime_type,
            "file_size": e.file_size,
            "sha256": e.sha256,
            "uploaded_at": e.uploaded_at,
            "metadata_json": e.metadata_json
        }
        for e in ev_res.scalars().all()
    ]

    case_dict = {
        "case_number": case.case_number,
        "title": case.title,
        "status": case.status.value,
        "created_at": case.created_at
    }

    manifest = CaseManifestExporter.generate_manifest_data(case_dict, evidence_items)

    if format == "csv":
        csv_data = CaseManifestExporter.export_manifest_csv(manifest)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="evidence_manifest_{case.case_number}.csv"'}
        )
    
    return manifest

@router.get("/cases/{case_id}/package")
async def export_case_package(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates and downloads certified ZIP Case Package (Requirement 49).
    """
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    ev_res = await db.execute(select(Evidence).where(Evidence.case_id == case_id))
    ev_items = [
        {"id": e.id, "evidence_number": e.evidence_number, "filename": e.filename, "media_type": e.media_type.value,
         "mime_type": e.mime_type, "file_size": e.file_size, "sha256": e.sha256, "uploaded_at": e.uploaded_at, "metadata_json": e.metadata_json}
        for e in ev_res.scalars().all()
    ]

    find_res = await db.execute(select(Finding))
    findings = [
        {"code": f.finding_code, "category": f.category.value, "severity": f.severity.value,
         "confidence": f.confidence, "score": f.score, "description": f.description, "model": f.model_name}
        for f in find_res.scalars().all()
    ]

    aud_res = await db.execute(select(AuditLog).where(AuditLog.case_id == case_id))
    audit_logs = [
        {"action": a.action, "entity": a.entity_type, "user_id": a.user_id, "timestamp": str(a.timestamp), "details": a.details}
        for a in aud_res.scalars().all()
    ]

    case_dict = {
        "case_number": case.case_number,
        "title": case.title,
        "description": case.description,
        "status": case.status.value,
        "priority": case.priority.value,
        "created_at": str(case.created_at)
    }

    zip_dir = os.path.join(settings.STORAGE_PATH, "exports")
    zip_path = os.path.join(zip_dir, f"CASE_PACKAGE_{case.case_number}.zip")
    CaseManifestExporter.create_case_package_zip(case_dict, ev_items, findings, audit_logs, zip_path)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"CASE_PACKAGE_{case.case_number}.zip"
    )
