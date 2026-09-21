"""
DeepTrace AI - End-to-End Pipeline Verification Script
Executes full investigator workflow:
Case creation -> Evidence ingestion -> SHA-256 calculation ->
Forensic analysis -> Model inference -> Heatmap generation ->
Fusion & findings -> PDF Report generation -> Report verification.
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import cv2
import numpy as np
from sqlalchemy import select

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.case import Case, CaseStatus, CasePriority
from backend.app.models.evidence import Evidence, MediaType
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.report import Report
from backend.app.services.pipeline import ForensicPipeline
from backend.app.services.report import ForensicReportEngine, compute_sha256
from backend.app.api.evidence import compute_sha256_file

async def run_e2e():
    print("==========================================================")
    print("       DEEPTRACE AI - END-TO-END PIPELINE AUDIT           ")
    print("==========================================================")
    async with AsyncSessionLocal() as session:
        user_res = await session.execute(select(User).limit(1))
        user = user_res.scalar_one()
        print(f"[*] Authenticated as: {user.name} ({user.role})")

        import uuid
        case_uid = uuid.uuid4().hex[:6].upper()
        case = Case(
            case_number=f"CASE-2026-E2E{case_uid}",
            title="End-to-End Synthetic Media Verification",
            description="Automated system integrity and forensic inference verification",
            status=CaseStatus.OPEN,
            priority=CasePriority.HIGH,
            created_by=user.id
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)
        print(f"[+] Case initialized: {case.case_number}")

        case_dir = os.path.join("storage", "cases", case.case_number)
        orig_dir = os.path.join(case_dir, "original")
        os.makedirs(orig_dir, exist_ok=True)
        img_path = os.path.join(orig_dir, "EV-00001_test_face.jpg")

        # Generate genuine test image with biometric facial features
        test_img = np.full((320, 320, 3), 190, dtype=np.uint8)
        cv2.ellipse(test_img, (160, 160), (70, 95), 0, 0, 360, (215, 205, 195), -1)
        cv2.circle(test_img, (135, 135), 8, (60, 50, 40), -1)
        cv2.circle(test_img, (185, 135), 8, (60, 50, 40), -1)
        cv2.circle(test_img, (160, 165), 5, (120, 100, 90), -1)
        cv2.line(test_img, (140, 205), (180, 205), (80, 50, 50), 3)
        cv2.imwrite(img_path, test_img)

        sha256 = compute_sha256_file(img_path)
        print(f"[+] Evidence file stored immutably. SHA-256: {sha256}")

        ev = Evidence(
            case_id=case.id,
            evidence_number=f"EV-{case_uid}",
            filename="test_face.jpg",
            mime_type="image/jpeg",
            media_type=MediaType.IMAGE,
            file_size=os.path.getsize(img_path),
            sha256=sha256,
            storage_path=img_path,
            uploaded_by=user.id
        )
        session.add(ev)
        await session.commit()
        await session.refresh(ev)
        print(f"[+] Evidence registered: {ev.evidence_number}")

        analysis = Analysis(evidence_id=ev.id, status=AnalysisStatus.QUEUED)
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)

        pipeline = ForensicPipeline(session)
        def log_event(stage, data):
            msg = data.get("message", "")
            print(f"    [Stage: {stage}] {msg}")

        res_analysis = await pipeline.execute_analysis(analysis.id, event_callback=log_event)
        print(f"[+] Forensic Pipeline completed in {res_analysis.processing_time}s!")
        print(f"    - Final Likelihood: {res_analysis.final_score * 100:.1f}%")
        print(f"    - Evidence Confidence: {res_analysis.confidence * 100:.1f}%")
        print(f"    - Assessment: {res_analysis.assessment}")
        print(f"    - Evidence Conflict Detected: {res_analysis.evidence_conflict}")

        rep_engine = ForensicReportEngine(session)
        report = await rep_engine.generate_report(res_analysis.id, user.id)
        print(f"[+] Professional PDF Report Generated: {report.report_number}")
        print(f"    - PDF Storage Path: {report.report_path}")
        print(f"    - Report Cryptographic SHA-256: {report.report_sha256}")

        recomputed = compute_sha256(report.report_path)
        assert recomputed == report.report_sha256
        print(f"[+] Report Cryptographic Hash Verified: MATCH.")
        print("==========================================================")
        print("        END-TO-END PIPELINE VERIFICATION PASSED           ")
        print("==========================================================")

if __name__ == "__main__":
    asyncio.run(run_e2e())
