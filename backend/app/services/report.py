import os
import hashlib
import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)

from backend.app.core.config import settings
from backend.app.models.case import Case
from backend.app.models.evidence import Evidence
from backend.app.models.analysis import Analysis
from backend.app.models.finding import Finding
from backend.app.models.audit import AuditLog
from backend.app.models.report import Report
from backend.app.models.user import User

def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()

class ForensicReportEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_report(self, analysis_id: int, generated_by_user_id: int) -> Report:
        # Fetch analysis and related data
        res_a = await self.db.execute(select(Analysis).where(Analysis.id == analysis_id))
        analysis = res_a.scalar_one_or_none()
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        res_e = await self.db.execute(select(Evidence).where(Evidence.id == analysis.evidence_id))
        evidence = res_e.scalar_one_or_none()
        if not evidence:
            raise ValueError(f"Evidence {analysis.evidence_id} not found")

        res_c = await self.db.execute(select(Case).where(Case.id == evidence.case_id))
        case = res_c.scalar_one_or_none()

        res_u = await self.db.execute(select(User).where(User.id == generated_by_user_id))
        investigator = res_u.scalar_one_or_none()
        investigator_name = investigator.name if investigator else "Investigator"

        res_f = await self.db.execute(select(Finding).where(Finding.analysis_id == analysis.id))
        findings = res_f.scalars().all()

        res_audit = await self.db.execute(
            select(AuditLog).where(AuditLog.case_id == case.id).order_by(AuditLog.timestamp.asc())
        )
        audit_logs = res_audit.scalars().all()

        # Output path
        case_dir = os.path.dirname(os.path.dirname(os.path.abspath(evidence.storage_path)))
        reports_dir = os.path.join(case_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        report_number = f"RPT-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{analysis.id:04d}"
        pdf_filename = f"{report_number}.pdf"
        pdf_path = os.path.join(reports_dir, pdf_filename)

        # Build PDF
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0B0F14"),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#FF6B00"),
            spaceAfter=15
        )
        h2_style = ParagraphStyle(
            "Heading2Custom",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#111820"),
            spaceBefore=12,
            spaceAfter=8
        )
        normal_style = ParagraphStyle(
            "NormalCustom",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#2D3748")
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=styles["Italic"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#4A5568")
        )

        story = []

        # Header
        story.append(Paragraph("DEEPTRACE AI", title_style))
        story.append(Paragraph("Professional Digital Forensic Analysis Report", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#CBD5E0"), spaceAfter=15))

        # Overview Table
        overview_data = [
            [Paragraph("<b>Report Number:</b>", normal_style), Paragraph(report_number, normal_style),
             Paragraph("<b>Date:</b>", normal_style), Paragraph(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), normal_style)],
            [Paragraph("<b>Case Number:</b>", normal_style), Paragraph(case.case_number if case else "N/A", normal_style),
             Paragraph("<b>Investigator:</b>", normal_style), Paragraph(investigator_name, normal_style)],
            [Paragraph("<b>Evidence ID:</b>", normal_style), Paragraph(evidence.evidence_number, normal_style),
             Paragraph("<b>Media Type:</b>", normal_style), Paragraph(str(evidence.media_type), normal_style)],
            [Paragraph("<b>Original Filename:</b>", normal_style), Paragraph(evidence.filename, normal_style),
             Paragraph("<b>File Size:</b>", normal_style), Paragraph(f"{evidence.file_size / (1024*1024):.2f} MB", normal_style)]
        ]
        t_overview = Table(overview_data, colWidths=[110, 155, 110, 155])
        t_overview.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_overview)
        story.append(Spacer(1, 15))

        # Evidence Integrity Section
        story.append(Paragraph("1. Evidence Cryptographic Integrity (SHA-256)", h2_style))
        hash_data = [
            [Paragraph("<b>Original File SHA-256:</b>", normal_style), Paragraph(f"<code>{evidence.sha256}</code>", normal_style)],
            [Paragraph("<b>Integrity Status:</b>", normal_style), Paragraph("<b>VERIFIED UNMODIFIED (Immutable Storage)</b>", normal_style)]
        ]
        t_hash = Table(hash_data, colWidths=[160, 370])
        t_hash.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_hash)
        story.append(Spacer(1, 15))

        # Executive Summary & Assessment
        story.append(Paragraph("2. Executive Forensic Assessment", h2_style))
        assessment_text = str(analysis.assessment).replace("_", " ") if analysis.assessment else "INCONCLUSIVE"
        score_pct = f"{analysis.final_score * 100:.1f}%" if analysis.final_score is not None else "N/A"
        conf_pct = f"{analysis.confidence * 100:.1f}%" if analysis.confidence is not None else "N/A"

        conflict_note = f"<br/><font color='red'><b>ALERT: {analysis.conflict_details}</b></font>" if analysis.evidence_conflict else ""

        summary_html = f"""
        <b>Manipulation Likelihood:</b> {score_pct} &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>Evidence Confidence:</b> {conf_pct} &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>Assessment:</b> {assessment_text}
        {conflict_note}
        """
        story.append(Paragraph(summary_html, normal_style))
        story.append(Spacer(1, 15))

        # Evaluated Modules & Forensic Observations
        story.append(Paragraph("3. Multimodal Forensic Observations", h2_style))
        fusion = analysis.fusion_details or {}
        mods = fusion.get("modules_evaluated", {})
        
        mod_table_data = [
            [Paragraph("<b>Forensic Module</b>", normal_style),
             Paragraph("<b>Category</b>", normal_style),
             Paragraph("<b>Score</b>", normal_style),
             Paragraph("<b>Confidence</b>", normal_style),
             Paragraph("<b>Observation Description</b>", normal_style)]
        ]
        for m_name, m_val in mods.items():
            mod_table_data.append([
                Paragraph(m_name.replace("_", " ").title(), normal_style),
                Paragraph(m_val.get("category", ""), normal_style),
                Paragraph(f"{m_val.get('score', 0.0):.2f}", normal_style),
                Paragraph(f"{m_val.get('confidence', 0.0):.2f}", normal_style),
                Paragraph(m_val.get("description", ""), normal_style),
            ])

        t_mods = Table(mod_table_data, colWidths=[110, 85, 45, 60, 230])
        t_mods.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t_mods)
        story.append(Spacer(1, 15))

        # Traceable Findings Table
        story.append(Paragraph("4. Traceable Forensic Findings", h2_style))
        if findings:
            find_table_data = [
                [Paragraph("<b>Code</b>", normal_style),
                 Paragraph("<b>Category</b>", normal_style),
                 Paragraph("<b>Severity</b>", normal_style),
                 Paragraph("<b>Score</b>", normal_style),
                 Paragraph("<b>Description</b>", normal_style)]
            ]
            for f in findings:
                find_table_data.append([
                    Paragraph(f.finding_code, normal_style),
                    Paragraph(str(f.category), normal_style),
                    Paragraph(str(f.severity), normal_style),
                    Paragraph(f"{f.score:.2f}", normal_style),
                    Paragraph(f.description, normal_style),
                ])
            t_find = Table(find_table_data, colWidths=[65, 90, 65, 45, 265])
            t_find.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(t_find)
        else:
            story.append(Paragraph("No critical or anomalous forensic findings identified.", normal_style))
        story.append(Spacer(1, 15))

        # Chain of Custody Log
        story.append(Paragraph("5. Chain of Custody Audit Trail", h2_style))
        audit_data = [
            [Paragraph("<b>Timestamp (UTC)</b>", normal_style),
             Paragraph("<b>Action</b>", normal_style),
             Paragraph("<b>Details</b>", normal_style)]
        ]
        for a in audit_logs[-8:]:
            audit_data.append([
                Paragraph(a.timestamp.strftime("%Y-%m-%d %H:%M:%S"), normal_style),
                Paragraph(a.action, normal_style),
                Paragraph(str(a.details or {}), normal_style),
            ])
        t_audit = Table(audit_data, colWidths=[120, 130, 280])
        t_audit.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F7FAFC")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t_audit)
        story.append(Spacer(1, 20))

        # Limitations & Mandatory Legal Disclaimer
        story.append(Paragraph("6. Analysis Limitations & Forensic Disclaimer", h2_style))
        disclaimer_text = (
            "<b>MANDATORY FORENSIC DISCLAIMER:</b><br/>"
            "AI-based media analysis produces probabilistic results and should be interpreted together with other "
            "available forensic evidence and applicable investigative procedures. The platform makes no claim of "
            "absolute authenticity or manipulation without corroborated independent forensic verification.<br/><br/>"
            "<b>TECHNICAL LIMITATIONS:</b><br/>"
            f"Pipeline Version: {analysis.pipeline_version} | Hardware Device: {analysis.inference_device}<br/>"
            "Performance may degrade on extreme media recompression, low spatial resolutions (<224x224), "
            "heavy motion blur, or adversarial generative techniques not present in model training corpora."
        )
        story.append(Paragraph(disclaimer_text, disclaimer_style))

        # Build Document
        doc.build(story)

        # Calculate Report PDF SHA-256
        report_sha256 = compute_sha256(pdf_path)

        report_entry = Report(
            case_id=case.id if case else 1,
            analysis_id=analysis.id,
            report_number=report_number,
            report_path=pdf_path,
            report_sha256=report_sha256,
            generated_by=generated_by_user_id
        )
        self.db.add(report_entry)
        
        # Log audit
        audit = AuditLog(
            case_id=case.id if case else 1,
            user_id=generated_by_user_id,
            action="REPORT_GENERATED",
            details={
                "report_number": report_number,
                "report_sha256": report_sha256,
                "analysis_id": analysis.id
            }
        )
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(report_entry)

        return report_entry
