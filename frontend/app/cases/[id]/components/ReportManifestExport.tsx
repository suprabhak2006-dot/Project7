"use client";

import React, { useState } from "react";
import {
  FileText,
  Download,
  Shield,
  EyeOff,
  FileCheck,
  Archive,
  CheckCircle2,
  Lock
} from "lucide-react";
import { api } from "@/lib/api";
import { Case, Report } from "@/types";

interface Props {
  caseData: Case;
  reports: Report[];
  analysisId?: number;
  onRefresh: () => void;
}

export default function ReportManifestExport({ caseData, reports, analysisId, onRefresh }: Props) {
  const [reportType, setReportType] = useState<string>("TECHNICAL");
  const [redactFaces, setRedactFaces] = useState(false);
  const [redactPii, setRedactPii] = useState(true);
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!analysisId) {
      alert("Please run or select an evidence analysis before generating a certified forensic report.");
      return;
    }
    setGenerating(true);
    try {
      await api.generateReport(analysisId);
      onRefresh();
    } catch (err) {
      alert("Report generation failed");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Report Generation Suite */}
      <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-6 shadow-xs space-y-6">
        <div>
          <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <FileText className="w-5 h-5 text-purple-600" />
            Certified Forensic Report Suite
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Cryptographically signed PDF reports generated from authentic forensic analysis runs, complete with SHA-256 integrity checksums.
          </p>
        </div>

        {/* 4 Report Types Selector */}
        <div>
          <label className="block text-xs font-bold text-gray-700 mb-2">Select Report Format</label>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            {[
              { id: "EXECUTIVE", title: "Executive Report", desc: "High-level summary for legal and executive leadership" },
              { id: "TECHNICAL", title: "Technical Report", desc: "In-depth model logits, frequency transforms, and calibration" },
              { id: "EVIDENCE", title: "Evidence Report", desc: "Bitstream hashes, EXIF provenance, and container telemetry" },
              { id: "INVESTIGATION", title: "Investigation Report", desc: "Full case timeline, subject links, and review records" }
            ].map((t) => (
              <div
                key={t.id}
                onClick={() => setReportType(t.id)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                  reportType === t.id
                    ? "bg-purple-50 border-purple-400 ring-2 ring-purple-200"
                    : "bg-white border-pink-100 hover:bg-purple-50/30"
                }`}
              >
                <span className="text-xs font-bold text-gray-900 block">{t.title}</span>
                <span className="text-[11px] text-gray-500 mt-1 block leading-snug">{t.desc}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Privacy Redaction Toggles */}
        <div className="p-4 bg-purple-50/30 rounded-xl border border-purple-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <EyeOff className="w-4 h-4 text-purple-600" />
            <span className="font-semibold text-purple-950">Privacy Protection & PII Masking:</span>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-1.5 cursor-pointer text-gray-700">
              <input
                type="checkbox"
                checked={redactFaces}
                onChange={(e) => setRedactFaces(e.target.checked)}
                className="rounded border-purple-300 text-purple-600 focus:ring-purple-400"
              />
              Redact Biometric Face Crops
            </label>

            <label className="flex items-center gap-1.5 cursor-pointer text-gray-700">
              <input
                type="checkbox"
                checked={redactPii}
                onChange={(e) => setRedactPii(e.target.checked)}
                className="rounded border-purple-300 text-purple-600 focus:ring-purple-400"
              />
              Mask GPS / Hardware PII
            </label>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold text-xs shadow-md hover:opacity-95 disabled:opacity-50 transition-all flex items-center gap-2"
          >
            <FileCheck className="w-4 h-4" />
            {generating ? "Generating Certified Report..." : `Generate ${reportType} Report`}
          </button>
        </div>
      </div>

      {/* Manifest & Case Package Downloads */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Evidence Manifest Export */}
        <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2 mb-1">
              <FileCheck className="w-4 h-4 text-emerald-600" />
              Cryptographic Evidence Manifest
            </h4>
            <p className="text-xs text-gray-500 mb-4">
              Export chain-of-custody checksums, media dimensions, and timestamps in RFC-4180 CSV or JSON format.
            </p>
          </div>

          <div className="flex gap-2">
            <a
              href={api.getCaseManifestUrl(caseData.id, "json")}
              target="_blank"
              rel="noreferrer"
              className="flex-1 py-2 text-center text-xs font-semibold rounded-xl bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 transition-all"
            >
              Export JSON
            </a>
            <a
              href={api.getCaseManifestUrl(caseData.id, "csv")}
              target="_blank"
              rel="noreferrer"
              className="flex-1 py-2 text-center text-xs font-semibold rounded-xl bg-pink-50 text-pink-700 border border-pink-200 hover:bg-pink-100 transition-all"
            >
              Export CSV
            </a>
          </div>
        </div>

        {/* Certified Case Package Export */}
        <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2 mb-1">
              <Archive className="w-4 h-4 text-purple-600" />
              Complete Case Package ZIP
            </h4>
            <p className="text-xs text-gray-500 mb-4">
              Bundles case metadata, manifests, findings, audit trail logs, and certified documentation into an immutable archive.
            </p>
          </div>

          <a
            href={api.getCasePackageUrl(caseData.id)}
            target="_blank"
            rel="noreferrer"
            className="w-full py-2 text-center text-xs font-bold rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-xs hover:opacity-95 transition-all flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4" /> Download Case Package (.zip)
          </a>
        </div>
      </div>
    </div>
  );
}
