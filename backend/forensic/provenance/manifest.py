import os
import io
import csv
import json
import zipfile
import datetime
from typing import Dict, Any, List

class CaseManifestExporter:
    """
    Generates cryptographic Evidence Manifests (JSON, CSV) and complete
    Case Export Packages (.zip) adhering to forensic chain-of-custody standards.
    """

    @staticmethod
    def generate_manifest_data(case_dict: Dict[str, Any], evidence_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Creates structured evidence manifest dictionary.
        """
        manifest = {
            "case_number": case_dict.get("case_number"),
            "case_title": case_dict.get("title"),
            "manifest_generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "total_evidence_count": len(evidence_items),
            "evidence_records": []
        }

        for ev in evidence_items:
            manifest["evidence_records"].append({
                "evidence_id": ev.get("id"),
                "evidence_number": ev.get("evidence_number"),
                "filename": ev.get("filename"),
                "media_type": ev.get("media_type"),
                "mime_type": ev.get("mime_type"),
                "file_size_bytes": ev.get("file_size"),
                "sha256_hash": ev.get("sha256"),
                "uploaded_at": str(ev.get("uploaded_at")),
                "metadata": ev.get("metadata_json") or {}
            })
        return manifest

    @staticmethod
    def export_manifest_csv(manifest: Dict[str, Any]) -> str:
        """
        Serializes evidence records to RFC-4180 CSV string.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Evidence Number", "Filename", "Media Type", "Size (Bytes)", "SHA-256 Checksum", "Ingested At"])
        for r in manifest.get("evidence_records", []):
            writer.writerow([
                r.get("evidence_number"),
                r.get("filename"),
                r.get("media_type"),
                r.get("file_size_bytes"),
                r.get("sha256_hash"),
                r.get("uploaded_at")
            ])
        return output.getvalue()

    @staticmethod
    def create_case_package_zip(
        case_dict: Dict[str, Any],
        evidence_items: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        audit_logs: List[Dict[str, Any]],
        output_zip_path: str
    ) -> str:
        """
        Bundles complete case package according to Requirement 49:
        case.json, evidence_manifest.json, findings.json, audit_trail.json.
        """
        os.makedirs(os.path.dirname(output_zip_path), exist_ok=True)
        manifest = CaseManifestExporter.generate_manifest_data(case_dict, evidence_items)

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("case.json", json.dumps(case_dict, indent=2, default=str))
            zf.writestr("evidence_manifest.json", json.dumps(manifest, indent=2, default=str))
            zf.writestr("evidence_manifest.csv", CaseManifestExporter.export_manifest_csv(manifest))
            zf.writestr("findings.json", json.dumps(findings, indent=2, default=str))
            zf.writestr("audit_trail.json", json.dumps(audit_logs, indent=2, default=str))
            zf.writestr(
                "PACKAGE_README.txt",
                f"DeepTrace AI Certified Forensic Investigation Package\n"
                f"Case: {case_dict.get('case_number')} - {case_dict.get('title')}\n"
                f"Export Timestamp: {datetime.datetime.utcnow().isoformat()}Z\n"
                f"Notice: All SHA-256 hashes and chain-of-custody audit logs are cryptographically documented.\n"
            )

        return output_zip_path
