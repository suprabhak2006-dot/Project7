"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  FolderLock,
  UploadCloud,
  FileCheck,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Activity,
  History,
  Play,
  Clock
} from "lucide-react";
import { api } from "@/lib/api";
import { Case, Evidence, Analysis, Finding, Report, AuditLog } from "@/types";

export default function CaseWorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const caseId = parseInt(resolvedParams.id, 10);

  const [activeTab, setActiveTab] = useState<
    "overview" | "evidence" | "analysis" | "timeline" | "findings" | "custody" | "reports" | "audit"
  >("overview");

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisStage, setAnalysisStage] = useState<string>("IDLE");
  const [analysisMessage, setAnalysisMessage] = useState<string>("");

  // Upload modal state
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // Integrity status
  const [integrityStatus, setIntegrityStatus] = useState<Record<number, string>>({});
  const [verifyingHash, setVerifyingHash] = useState<number | null>(null);

  const loadCaseData = async () => {
    try {
      const c = await api.getCase(caseId);
      setCaseData(c);
      const logs = await api.getAuditLogs(caseId);
      setAuditLogs(logs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCaseData();
  }, [caseId]);

  // Handle Evidence Upload
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setUploading(true);
    try {
      const ev = await api.uploadEvidence(caseId, uploadFile);
      setEvidenceList((prev) => [ev, ...prev]);
      setSelectedEvidence(ev);
      setUploadFile(null);
      setShowUpload(false);
      await loadCaseData();
      setActiveTab("evidence");
    } catch (err) {
      alert(err instanceof Error ? err.message : "Evidence upload failed");
    } finally {
      setUploading(false);
    }
  };

  // Verify SHA-256 Integrity
  const handleVerifyIntegrity = async (evidenceId: number) => {
    setVerifyingHash(evidenceId);
    try {
      const res = await api.verifyEvidenceIntegrity(evidenceId);
      setIntegrityStatus((prev) => ({ ...prev, [evidenceId]: res.status }));
      await loadCaseData();
    } catch (err) {
      alert("Integrity verification error");
    } finally {
      setVerifyingHash(null);
    }
  };

  // Trigger Real Analysis
  const handleStartAnalysis = async (ev: Evidence) => {
    setAnalyzing(true);
    setAnalysisStage("QUEUED");
    setAnalysisMessage("Enqueuing forensic analysis job...");
    setActiveTab("analysis");

    try {
      const initiated = await api.startAnalysis(ev.id);
      setAnalysis(initiated);

      // Listen to SSE live events
      const eventSource = new EventSource(`http://localhost:8000/api/analysis/${initiated.id}/events`);
      eventSource.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.stage) {
            setAnalysisStage(payload.stage);
            if (payload.data?.message) {
              setAnalysisMessage(payload.data.message);
            }
            if (payload.stage === "COMPLETED") {
              eventSource.close();
              setAnalyzing(false);
              api.getAnalysis(initiated.id).then((full) => {
                setAnalysis(full);
                api.getFindings(initiated.id).then(setFindings);
              });
              loadCaseData();
            } else if (payload.stage === "FAILED") {
              eventSource.close();
              setAnalyzing(false);
              alert("Analysis pipeline reported failure: " + (payload.data?.error || "Unknown"));
            }
          }
        } catch {}
      };
    } catch (err) {
      setAnalyzing(false);
      alert(err instanceof Error ? err.message : "Failed to start analysis");
    }
  };

  // Generate Report
  const handleGenerateReport = async () => {
    if (!analysis) return;
    try {
      const rep = await api.generateReport(analysis.id);
      setReports((prev) => [rep, ...prev]);
      setActiveTab("reports");
      await loadCaseData();
      alert(`Professional Forensic Report generated! Number: ${rep.report_number}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to generate report");
    }
  };

  if (loading || !caseData) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center space-x-3 text-sm font-mono text-[#86729C]">
          <div className="w-4 h-4 border-2 border-[#EC4899] border-t-transparent rounded-full animate-spin" />
          <span>LOADING CASE WORKSPACE...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner / Case Header */}
      <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-6 space-y-4 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-3 font-mono">
              <span className="text-xl font-bold text-[#2D1B46] tracking-wide">{caseData.case_number}</span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#FAF5FF] text-[#9333EA] border border-[#E9D5FF]">
                {caseData.status}
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                caseData.priority === "HIGH" || caseData.priority === "CRITICAL"
                  ? "bg-[#FFF1F2] text-[#E11D48] border border-[#FECDD3]"
                  : "bg-[#F3E8FF] text-[#7C3AED]"
              }`}>
                {caseData.priority} PRIORITY
              </span>
            </div>
            <h1 className="text-lg font-semibold text-[#2D1B46]">{caseData.title}</h1>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowUpload(true)}
              className="flex items-center space-x-2 bg-gradient-to-r from-[#F472B6] to-[#C084FC] hover:opacity-95 text-white font-semibold px-4 py-2.5 rounded-xl text-xs font-mono shadow-xs transition-all"
            >
              <UploadCloud className="w-4 h-4" />
              <span>INGEST EVIDENCE</span>
            </button>
          </div>
        </div>

        {/* 8 Navigation Tabs */}
        <div className="flex items-center space-x-1 border-t border-[#F3E8FF] pt-3 overflow-x-auto text-xs font-mono">
          {[
            { id: "overview", label: "OVERVIEW", icon: FolderLock },
            { id: "evidence", label: "EVIDENCE", icon: ShieldCheck },
            { id: "analysis", label: "FORENSIC ANALYSIS", icon: Activity },
            { id: "timeline", label: "TIMELINE", icon: Play },
            { id: "findings", label: "FINDINGS", icon: AlertTriangle },
            { id: "custody", label: "CHAIN OF CUSTODY", icon: History },
            { id: "reports", label: "REPORTS", icon: FileText },
            { id: "audit", label: "AUDIT LOG", icon: Clock },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-[#FDF2F8] to-[#FAF5FF] text-[#EC4899] border border-[#FBCFE8] font-bold shadow-xs"
                    : "text-[#86729C] hover:text-[#2D1B46] hover:bg-[#FAF5FF]"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ----------------- TAB: OVERVIEW ----------------- */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-3 shadow-xs">
              <h3 className="text-sm font-bold text-[#2D1B46] font-mono uppercase">Case Overview & Details</h3>
              <p className="text-xs text-[#86729C] leading-relaxed">
                {caseData.description || "No formal case description provided at time of initialization."}
              </p>
              <div className="grid grid-cols-2 gap-4 pt-3 border-t border-[#F3E8FF] text-xs font-mono">
                <div>
                  <span className="text-[#86729C]">Initialized:</span>{" "}
                  <span className="text-[#2D1B46] font-medium">{new Date(caseData.created_at).toUTCString()}</span>
                </div>
                <div>
                  <span className="text-[#86729C]">Last Updated:</span>{" "}
                  <span className="text-[#2D1B46] font-medium">{new Date(caseData.updated_at).toUTCString()}</span>
                </div>
              </div>
            </div>

            <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-3 shadow-xs">
              <h3 className="text-sm font-bold text-[#2D1B46] font-mono uppercase">Forensic Procedures & Defensibility</h3>
              <p className="text-xs text-[#86729C] leading-relaxed">
                Evidence uploaded to this case is stored immutably in isolated directory storage. Cryptographic SHA-256 hashes are recorded immediately upon transmission. All subsequent derivatives (face crops, spectrograms, heatmaps) maintain traceable pointers back to the original evidence hash.
              </p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 font-mono text-xs shadow-xs">
              <h3 className="font-bold text-[#2D1B46] uppercase">Investigation Quick Actions</h3>
              <button
                onClick={() => setShowUpload(true)}
                className="w-full text-left p-3.5 rounded-xl bg-[#FAF5FF] border border-[#E9D5FF] hover:border-[#F472B6] transition-all"
              >
                <div className="font-bold text-[#2D1B46]">+ Upload Media File</div>
                <div className="text-[11px] text-[#86729C]">Images (JPG/PNG), Videos (MP4), Audio (WAV/MP3)</div>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ----------------- TAB: EVIDENCE ----------------- */}
      {activeTab === "evidence" && (
        <div className="space-y-6">
          <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 shadow-xs">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#2D1B46] font-mono uppercase">Ingested Evidence Items</h3>
              <button
                onClick={() => setShowUpload(true)}
                className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-[#F472B6] to-[#C084FC] text-white font-mono text-xs font-bold shadow-xs"
              >
                + ADD EVIDENCE
              </button>
            </div>

            {evidenceList.length > 0 ? (
              <div className="space-y-3">
                {evidenceList.map((ev) => {
                  const status = integrityStatus[ev.id];
                  const isVerifying = verifyingHash === ev.id;
                  return (
                    <div
                      key={ev.id}
                      className="p-4 bg-[#FAF5FF]/80 border border-[#F3E8FF] rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-xs shadow-xs"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-[#2D1B46]">{ev.evidence_number}</span>
                          <span className="px-2.5 py-0.5 rounded-full bg-white text-[#9333EA] border border-[#E9D5FF] text-[10px] font-bold">
                            {ev.media_type}
                          </span>
                          <span className="text-[#86729C]">({(ev.file_size / (1024*1024)).toFixed(2)} MB)</span>
                        </div>
                        <div className="text-[#2D1B46] font-medium">{ev.filename}</div>
                        <div className="text-[11px] text-[#86729C] flex items-center space-x-1">
                          <span>SHA-256:</span>
                          <code className="text-[#2D1B46] bg-white px-1.5 py-0.5 rounded border border-[#E9D5FF] text-[10px]">{ev.sha256}</code>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 self-start md:self-center">
                        <button
                          onClick={() => handleVerifyIntegrity(ev.id)}
                          disabled={isVerifying}
                          className={`px-3.5 py-1.5 rounded-xl border text-[11px] font-semibold transition-all shadow-xs ${
                            status === "INTEGRITY_VERIFIED"
                              ? "bg-[#ECFDF5] text-[#059669] border-[#A7F3D0]"
                              : "bg-white text-[#2D1B46] border-[#E9D5FF] hover:border-[#F472B6]"
                          }`}
                        >
                          {isVerifying ? "Verifying..." : status === "INTEGRITY_VERIFIED" ? "✓ VERIFIED" : "VERIFY SHA-256"}
                        </button>

                        <button
                          onClick={() => handleStartAnalysis(ev)}
                          className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-[#F472B6] to-[#C084FC] hover:opacity-95 text-white font-semibold text-[11px] shadow-xs transition-all"
                        >
                          RUN PIPELINE &rarr;
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-12 text-center text-xs text-[#86729C] font-mono space-y-3">
                <UploadCloud className="w-8 h-8 mx-auto text-[#EC4899]" />
                <div>No evidence files ingested for this case yet.</div>
                <button
                  onClick={() => setShowUpload(true)}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#F472B6] to-[#C084FC] text-white font-semibold shadow-xs"
                >
                  Upload Evidence File
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ----------------- TAB: ANALYSIS ----------------- */}
      {activeTab === "analysis" && (
        <div className="space-y-6">
          {analyzing && (
            <div className="bg-white/80 backdrop-blur-md border border-[#F472B6] rounded-2xl p-6 space-y-4 shadow-xs">
              <div className="flex items-center space-x-3">
                <div className="w-5 h-5 border-2 border-[#EC4899] border-t-transparent rounded-full animate-spin" />
                <span className="font-bold text-[#2D1B46] text-sm font-mono uppercase">
                  Active Forensic Pipeline Stage: [{analysisStage}]
                </span>
              </div>
              <p className="text-xs text-[#86729C] font-mono">{analysisMessage}</p>
              
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 text-[10px] font-mono">
                {["VALIDATING", "METADATA", "FACE_DETECTION", "AI_INFERENCE", "FORENSIC_ANALYSIS", "TEMPORAL_ANALYSIS", "AUDIO_ANALYSIS", "AV_ANALYSIS", "FUSION", "FINDINGS"].map((s, idx) => (
                  <div
                    key={s}
                    className={`p-2.5 rounded-xl border transition-all ${
                      analysisStage === s
                        ? "bg-gradient-to-r from-[#FDF2F8] to-[#FAF5FF] border-[#F472B6] text-[#EC4899] font-bold shadow-xs"
                        : "bg-[#FAF5FF] border-[#F3E8FF] text-[#86729C]"
                    }`}
                  >
                    {idx + 1}. {s.replace("_", " ")}
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis && !analyzing && (
            <div className="space-y-6">
              {/* Conflict Alert Banner */}
              {analysis.evidence_conflict && (
                <div className="bg-[#FFF1F2] border-2 border-[#FECDD3] rounded-2xl p-5 space-y-2 shadow-xs">
                  <div className="flex items-center space-x-2 text-sm font-bold text-[#E11D48] font-mono">
                    <AlertTriangle className="w-5 h-5" />
                    <span>EVIDENCE CONFLICT DETECTED</span>
                  </div>
                  <p className="text-xs text-[#2D1B46] font-mono leading-relaxed">
                    {analysis.conflict_details}
                  </p>
                </div>
              )}

              {/* Assessment Gauge Card */}
              <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-6 grid grid-cols-1 md:grid-cols-3 gap-6 font-mono shadow-xs">
                <div className="space-y-1">
                  <div className="text-xs text-[#86729C] font-medium">MANIPULATION LIKELIHOOD</div>
                  <div className="text-4xl font-extrabold text-[#EC4899]">
                    {analysis.final_score !== null ? `${(analysis.final_score * 100).toFixed(1)}%` : "N/A"}
                  </div>
                  <div className="text-[11px] text-[#86729C]">Probabilistic model aggregation</div>
                </div>

                <div className="space-y-1">
                  <div className="text-xs text-[#86729C] font-medium">EVIDENCE CONFIDENCE</div>
                  <div className="text-4xl font-extrabold text-[#A855F7]">
                    {analysis.confidence !== null ? `${(analysis.confidence * 100).toFixed(1)}%` : "N/A"}
                  </div>
                  <div className="text-[11px] text-[#86729C]">Modality certainty level</div>
                </div>

                <div className="space-y-2 flex flex-col justify-center">
                  <div className="text-xs text-[#86729C] font-medium">OFFICIAL ASSESSMENT</div>
                  <span className={`px-3 py-2 rounded-xl text-xs font-bold text-center border shadow-xs ${
                    analysis.assessment === "HIGH_MANIPULATION_LIKELIHOOD"
                      ? "bg-[#FFF1F2] text-[#E11D48] border-[#FECDD3]"
                      : analysis.assessment === "EVIDENCE_CONFLICT"
                      ? "bg-[#FEF3C7] text-[#D97706] border-[#FDE68A]"
                      : "bg-[#ECFDF5] text-[#059669] border-[#A7F3D0]"
                  }`}>
                    {analysis.assessment?.replace(/_/g, " ")}
                  </span>
                </div>
              </div>

              {/* Evaluated Modalities Table */}
              <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 shadow-xs">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-[#2D1B46] font-mono uppercase">Multi-Signal Forensic Observations</h3>
                  <button
                    onClick={handleGenerateReport}
                    className="px-4 py-2 bg-gradient-to-r from-[#F472B6] to-[#C084FC] text-white font-mono text-xs font-bold rounded-xl shadow-xs hover:opacity-95"
                  >
                    GENERATE PDF REPORT &rarr;
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="border-b border-[#F3E8FF] text-[#86729C]">
                      <tr>
                        <th className="pb-3">MODULE</th>
                        <th className="pb-3">CATEGORY</th>
                        <th className="pb-3">MEASURED SCORE</th>
                        <th className="pb-3">CONFIDENCE</th>
                        <th className="pb-3">FINDING DETAILS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#F3E8FF]">
                      {analysis.fusion_details?.modules_evaluated &&
                        Object.entries(analysis.fusion_details.modules_evaluated).map(([mName, mData]: any) => (
                          <tr key={mName} className="hover:bg-[#FAF5FF]">
                            <td className="py-3 font-semibold text-[#2D1B46]">{mName.replace(/_/g, " ").toUpperCase()}</td>
                            <td className="py-3 text-[#7C3AED] font-medium">{mData.category}</td>
                            <td className="py-3 font-bold text-[#EC4899]">{(mData.score * 100).toFixed(1)}%</td>
                            <td className="py-3 text-[#86729C]">{(mData.confidence * 100).toFixed(0)}%</td>
                            <td className="py-3 text-[#2D1B46]">{mData.description}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {!analysis && !analyzing && (
            <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-12 text-center text-xs font-mono text-[#86729C] space-y-3 shadow-xs">
              <Activity className="w-8 h-8 mx-auto text-[#EC4899]" />
              <div className="text-[#2D1B46] font-bold">No analysis has been initiated on this evidence yet.</div>
              <div className="text-[11px]">Go to the Evidence tab and click &quot;RUN PIPELINE&quot; to execute real AI inference.</div>
            </div>
          )}
        </div>
      )}

      {/* ----------------- TAB: TIMELINE ----------------- */}
      {activeTab === "timeline" && (
        <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 shadow-xs">
          <h3 className="text-sm font-bold text-[#2D1B46] font-mono uppercase">Video Temporal Manipulation Timeline</h3>
          {analysis?.timeline_data && analysis.timeline_data.length > 0 ? (
            <div className="space-y-4 font-mono text-xs">
              <div className="p-4 bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl">
                <div className="flex items-center justify-between text-[#86729C] mb-2 font-medium">
                  <span>FRAME-BY-FRAME MANIPULATION SCORE TRAJECTORY</span>
                  <span>TOTAL FRAMES: {analysis.timeline_data.length}</span>
                </div>
                <div className="h-28 flex items-end gap-1.5 overflow-x-auto py-2">
                  {analysis.timeline_data.map((pt, i) => {
                    const heightPct = Math.max(8, pt.score * 100);
                    const isSpike = pt.score >= 0.70;
                    return (
                      <div
                        key={i}
                        title={`t=${pt.timestamp}s, score=${(pt.score * 100).toFixed(1)}%`}
                        className="flex flex-col items-center flex-shrink-0 group cursor-pointer"
                      >
                        <div
                          style={{ height: `${heightPct}%` }}
                          className={`w-3.5 rounded-t-md transition-all ${
                            isSpike ? "bg-[#E11D48]" : "bg-gradient-to-t from-[#F472B6] to-[#C084FC] hover:opacity-90"
                          }`}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-[#86729C] font-mono">
              Temporal timeline is available for video evidence containing extracted frame sequences.
            </div>
          )}
        </div>
      )}

      {/* ----------------- TAB: FINDINGS ----------------- */}
      {activeTab === "findings" && (
        <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 font-mono text-xs shadow-xs">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#2D1B46] uppercase">Traceable Forensic Findings</h3>
            <span className="text-[#86729C]">{findings.length} findings recorded</span>
          </div>

          {findings.length > 0 ? (
            <div className="divide-y divide-[#F3E8FF]">
              {findings.map((f) => (
                <div key={f.id} className="py-4 space-y-1.5">
                  <div className="flex items-center space-x-3">
                    <span className="font-bold text-[#2D1B46]">{f.finding_code}</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                      f.severity === "CRITICAL"
                        ? "bg-[#FFF1F2] text-[#E11D48] border border-[#FECDD3]"
                        : f.severity === "HIGH"
                        ? "bg-[#FDF2F8] text-[#DB2777] border border-[#FBCFE8]"
                        : "bg-[#F3E8FF] text-[#7C3AED]"
                    }`}>
                      {f.severity}
                    </span>
                    <span className="text-[#9333EA] font-semibold">{f.category}</span>
                    <span className="text-[#86729C]">Score: {(f.score * 100).toFixed(1)}%</span>
                  </div>
                  <p className="text-[#2D1B46] font-medium">{f.description}</p>
                  <div className="text-[10px] text-[#86729C]">
                    Detector: {f.model_name} (v{f.model_version})
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-[#86729C]">
              No findings recorded. Run an analysis on evidence to generate findings.
            </div>
          )}
        </div>
      )}

      {/* ----------------- TAB: CHAIN OF CUSTODY ----------------- */}
      {activeTab === "custody" && (
        <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 font-mono text-xs shadow-xs">
          <h3 className="text-sm font-bold text-[#2D1B46] uppercase">Cryptographic Chain of Custody</h3>
          <div className="divide-y divide-[#F3E8FF]">
            {auditLogs.map((log) => (
              <div key={log.id} className="py-3 flex items-start justify-between">
                <div className="space-y-1">
                  <div className="font-bold text-[#EC4899]">{log.action}</div>
                  <div className="text-[#86729C] text-[11px]">
                    {JSON.stringify(log.details || {})}
                  </div>
                </div>
                <div className="text-[#86729C] text-[11px] text-right font-medium">
                  {new Date(log.timestamp).toUTCString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ----------------- TAB: REPORTS ----------------- */}
      {activeTab === "reports" && (
        <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 font-mono text-xs shadow-xs">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#2D1B46] uppercase">Official Forensic Reports</h3>
            {analysis && (
              <button
                onClick={handleGenerateReport}
                className="px-4 py-2 bg-gradient-to-r from-[#F472B6] to-[#C084FC] text-white font-bold rounded-xl shadow-xs hover:opacity-95"
              >
                + GENERATE NEW PDF REPORT
              </button>
            )}
          </div>

          {reports.length > 0 ? (
            <div className="space-y-3">
              {reports.map((rep) => (
                <div
                  key={rep.id}
                  className="p-4 bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl flex items-center justify-between shadow-xs"
                >
                  <div className="space-y-1">
                    <div className="font-bold text-[#2D1B46]">{rep.report_number}</div>
                    <div className="text-[11px] text-[#86729C]">
                      SHA-256: <code className="text-[#2D1B46] bg-white px-1.5 py-0.5 rounded border border-[#E9D5FF]">{rep.report_sha256}</code>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <a
                      href={api.getReportDownloadUrl(rep.id)}
                      target="_blank"
                      className="px-3.5 py-1.5 rounded-xl bg-white border border-[#E9D5FF] hover:border-[#F472B6] text-[#2D1B46] font-semibold transition-all shadow-xs"
                    >
                      Download PDF &darr;
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center text-[#86729C]">
              No reports generated yet for this case. Run an analysis and click &quot;Generate PDF Report&quot;.
            </div>
          )}
        </div>
      )}

      {/* ----------------- TAB: AUDIT LOG ----------------- */}
      {activeTab === "audit" && (
        <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 font-mono text-xs shadow-xs">
          <h3 className="text-sm font-bold text-[#2D1B46] uppercase">Immutable System Audit Log</h3>
          <div className="divide-y divide-[#F3E8FF]">
            {auditLogs.map((log) => (
              <div key={log.id} className="py-2.5 flex items-center justify-between">
                <div>
                  <span className="font-bold text-[#2D1B46]">{log.action}</span>
                  <span className="text-[#86729C] ml-3">{JSON.stringify(log.details || {})}</span>
                </div>
                <div className="text-[#86729C] text-[10px]">{new Date(log.timestamp).toISOString()}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Evidence Modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-[#2D1B46]/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#F3E8FF] rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#F3E8FF] pb-3">
              <h3 className="font-bold text-[#2D1B46] text-base font-mono">Ingest New Media Evidence</h3>
              <button onClick={() => setShowUpload(false)} className="text-[#86729C] hover:text-[#2D1B46]">&times;</button>
            </div>

            <form onSubmit={handleUpload} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-[#86729C] mb-1 font-semibold">SELECT FILE (IMAGE, VIDEO, AUDIO) *</label>
                <input
                  type="file"
                  required
                  accept="image/*,video/*,audio/*"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl p-3 text-[#2D1B46] file:mr-4 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-gradient-to-r file:from-[#F472B6] file:to-[#C084FC] file:text-white"
                />
              </div>

              {uploadFile && (
                <div className="p-3 bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl space-y-1 text-[11px]">
                  <div>File: <span className="text-[#2D1B46] font-bold">{uploadFile.name}</span></div>
                  <div>Size: <span className="text-[#2D1B46] font-bold">{(uploadFile.size / (1024*1024)).toFixed(2)} MB</span></div>
                  <div className="text-[#059669] font-medium">SHA-256 will be calculated immediately upon ingestion.</div>
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowUpload(false)}
                  className="px-4 py-2 rounded-xl bg-[#FAF5FF] text-[#2D1B46] hover:bg-[#F3E8FF] border border-[#E9D5FF] font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-[#F472B6] to-[#C084FC] hover:opacity-95 text-white font-semibold shadow-xs"
                >
                  {uploading ? "Ingesting & Hashing..." : "Ingest File"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
