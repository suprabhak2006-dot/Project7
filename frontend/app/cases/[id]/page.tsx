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
  Clock,
  Layers,
  GitCompare,
  UserCheck,
  Network
} from "lucide-react";
import { api } from "@/lib/api";
import { Case, Evidence, Analysis, Finding, Report, AuditLog, InvestigationGraph, Subject, FaceTrack } from "@/types";

import InvestigationGraphViewer from "./components/InvestigationGraph";
import ForensicFilterLab from "./components/ForensicFilterLab";
import VideoAudioLab from "./components/VideoAudioLab";
import SubjectTrackManager from "./components/SubjectTrackManager";
import EvidenceCompareModal from "./components/EvidenceCompareModal";
import FindingReviewManager from "./components/FindingReviewManager";
import ReportManifestExport from "./components/ReportManifestExport";

export default function CaseWorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const caseId = parseInt(resolvedParams.id, 10);

  const [activeTab, setActiveTab] = useState<
    "overview" | "evidence" | "labs" | "subjects" | "analysis" | "timeline" | "findings" | "reports" | "audit"
  >("overview");

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [graphData, setGraphData] = useState<InvestigationGraph | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [faceTracks, setFaceTracks] = useState<FaceTrack[]>([]);

  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisStage, setAnalysisStage] = useState<string>("IDLE");
  const [analysisMessage, setAnalysisMessage] = useState<string>("");

  // Upload modal state
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // Compare modal state
  const [showCompareModal, setShowCompareModal] = useState(false);

  // Integrity status
  const [integrityStatus, setIntegrityStatus] = useState<Record<number, string>>({});
  const [verifyingHash, setVerifyingHash] = useState<number | null>(null);

  const loadCaseData = async () => {
    try {
      const c = await api.getCase(caseId);
      setCaseData(c);

      const logs = await api.getAuditLogs(caseId);
      setAuditLogs(logs);

      // Load extended workspace data
      const ws = await api.getCaseWorkspace(caseId);
      if (ws) {
        setSubjects(ws.subjects || []);
        setFaceTracks(ws.face_tracks || []);
      }

      // Load graph
      const g = await api.getCaseGraph(caseId);
      setGraphData(g);

      // Load evidence items
      const evs = await api.listEvidence(caseId);
      setEvidenceList(evs);
      if (evs.length > 0 && !selectedEvidence) {
        setSelectedEvidence(evs[0]);
      }
    } catch (err) {
      console.error("Workspace load error:", err);
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
    setSelectedEvidence(ev);
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
          }
          if (payload.stage === "COMPLETED") {
            eventSource.close();
            setAnalyzing(false);
            api.getAnalysis(initiated.id).then((completedAnalysis) => {
              setAnalysis(completedAnalysis);
            });
            api.getFindings(initiated.id).then(setFindings);
            loadCaseData();
          } else if (payload.stage === "FAILED") {
            eventSource.close();
            setAnalyzing(false);
            alert("Analysis failed: " + (payload.data?.error || "Unknown error"));
          }
        } catch (err) {
          console.error("SSE parse error:", err);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setAnalyzing(false);
      };
    } catch (err) {
      setAnalyzing(false);
      alert(err instanceof Error ? err.message : "Analysis trigger failed");
    }
  };

  if (loading || !caseData) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center space-x-3 text-sm font-mono text-[#86729C]">
          <div className="w-4 h-4 border-2 border-[#EC4899] border-t-transparent rounded-full animate-spin" />
          <span>LOADING ADVANCED FORENSIC WORKSPACE...</span>
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
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  caseData.priority === "HIGH" || caseData.priority === "URGENT"
                    ? "bg-[#FFF1F2] text-[#E11D48] border border-[#FECDD3]"
                    : "bg-[#F3E8FF] text-[#7C3AED]"
                }`}
              >
                {caseData.priority} PRIORITY
              </span>
            </div>
            <h1 className="text-lg font-semibold text-[#2D1B46]">{caseData.title}</h1>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowCompareModal(true)}
              className="flex items-center space-x-2 bg-white border border-[#E9D5FF] hover:border-[#F472B6] text-[#2D1B46] font-semibold px-3.5 py-2 rounded-xl text-xs shadow-2xs transition-all"
            >
              <GitCompare className="w-4 h-4 text-purple-600" />
              <span>COMPARE EVIDENCE</span>
            </button>

            <button
              onClick={() => setShowUpload(true)}
              className="flex items-center space-x-2 bg-gradient-to-r from-[#F472B6] to-[#C084FC] hover:opacity-95 text-white font-semibold px-4 py-2 rounded-xl text-xs font-mono shadow-xs transition-all"
            >
              <UploadCloud className="w-4 h-4" />
              <span>INGEST EVIDENCE</span>
            </button>
          </div>
        </div>

        {/* 9 Navigation Tabs */}
        <div className="flex items-center space-x-1 border-t border-[#F3E8FF] pt-3 overflow-x-auto text-xs font-mono">
          {[
            { id: "overview", label: "OVERVIEW & GRAPH", icon: Network },
            { id: "evidence", label: "EVIDENCE", icon: ShieldCheck },
            { id: "labs", label: "FORENSIC LABS", icon: Layers },
            { id: "subjects", label: "SUBJECTS & TRACKS", icon: UserCheck },
            { id: "analysis", label: "LIVE PIPELINE", icon: Activity },
            { id: "timeline", label: "TIMELINE", icon: Play },
            { id: "findings", label: "FINDINGS & REVIEW", icon: AlertTriangle },
            { id: "reports", label: "REPORTS & EXPORT", icon: FileText },
            { id: "audit", label: "AUDIT LOG", icon: Clock }
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl transition-all whitespace-nowrap ${
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

      {/* ----------------- TAB: OVERVIEW & GRAPH ----------------- */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <InvestigationGraphViewer graphData={graphData} />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-3 shadow-xs">
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

            <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 font-mono text-xs shadow-xs">
              <h3 className="font-bold text-[#2D1B46] uppercase">Forensic Workspace Telemetry</h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-pink-50">
                  <span className="text-[#86729C]">Ingested Evidence:</span>
                  <span className="font-bold text-[#2D1B46]">{evidenceList.length} items</span>
                </div>
                <div className="flex justify-between py-1 border-b border-pink-50">
                  <span className="text-[#86729C]">Tracked Subjects:</span>
                  <span className="font-bold text-[#9333EA]">{subjects.length} registered</span>
                </div>
                <div className="flex justify-between py-1 border-b border-pink-50">
                  <span className="text-[#86729C]">Face Tracks Cataloged:</span>
                  <span className="font-bold text-[#EC4899]">{faceTracks.length} tracks</span>
                </div>
                <div className="flex justify-between py-1 border-b border-pink-50">
                  <span className="text-[#86729C]">Audit Events:</span>
                  <span className="font-bold text-[#059669]">{auditLogs.length} verified logs</span>
                </div>
              </div>
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
              <div className="flex gap-2">
                <button
                  onClick={() => setShowCompareModal(true)}
                  className="px-3.5 py-1.5 rounded-xl bg-white border border-[#E9D5FF] text-[#2D1B46] font-mono text-xs font-semibold shadow-2xs hover:border-[#F472B6]"
                >
                  Compare Evidence
                </button>
                <button
                  onClick={() => setShowUpload(true)}
                  className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-[#F472B6] to-[#C084FC] text-white font-mono text-xs font-bold shadow-xs"
                >
                  + ADD EVIDENCE
                </button>
              </div>
            </div>

            {evidenceList.length > 0 ? (
              <div className="space-y-3">
                {evidenceList.map((ev) => {
                  const status = integrityStatus[ev.id];
                  const isVerifying = verifyingHash === ev.id;
                  const isSelected = selectedEvidence?.id === ev.id;
                  return (
                    <div
                      key={ev.id}
                      onClick={() => setSelectedEvidence(ev)}
                      className={`p-4 border rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-xs shadow-xs cursor-pointer transition-all ${
                        isSelected
                          ? "bg-purple-50/70 border-purple-300 ring-2 ring-purple-100"
                          : "bg-[#FAF5FF]/80 border-[#F3E8FF] hover:border-pink-200"
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-[#2D1B46]">{ev.evidence_number}</span>
                          <span className="px-2.5 py-0.5 rounded-full bg-white text-[#9333EA] border border-[#E9D5FF] text-[10px] font-bold">
                            {ev.media_type}
                          </span>
                          <span className="text-[#86729C]">
                            ({(ev.file_size / (1024 * 1024)).toFixed(2)} MB)
                          </span>
                          {isSelected && (
                            <span className="text-[10px] px-2 py-0.5 rounded bg-purple-200 text-purple-900 font-bold">
                              ACTIVE TARGET
                            </span>
                          )}
                        </div>
                        <div className="text-[#2D1B46] font-medium">{ev.filename}</div>
                        <div className="text-[11px] text-[#86729C] flex items-center space-x-1">
                          <span>SHA-256:</span>
                          <code className="text-[#2D1B46] bg-white px-1.5 py-0.5 rounded border border-[#E9D5FF] text-[10px]">
                            {ev.sha256}
                          </code>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 self-start md:self-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleVerifyIntegrity(ev.id);
                          }}
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
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartAnalysis(ev);
                          }}
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

      {/* ----------------- TAB: FORENSIC LABS ----------------- */}
      {activeTab === "labs" && (
        <div className="space-y-6">
          <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-4 flex items-center justify-between">
            <span className="text-xs text-gray-600">
              Target Evidence: <strong className="text-purple-900">{selectedEvidence?.filename || "None selected"}</strong> ({selectedEvidence?.media_type})
            </span>
            <div className="flex gap-2">
              {evidenceList.map((e) => (
                <button
                  key={e.id}
                  onClick={() => setSelectedEvidence(e)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold border ${
                    selectedEvidence?.id === e.id
                      ? "bg-purple-600 text-white border-purple-600"
                      : "bg-white text-gray-700 border-gray-200"
                  }`}
                >
                  {e.evidence_number}
                </button>
              ))}
            </div>
          </div>

          {selectedEvidence?.media_type === "IMAGE" && <ForensicFilterLab evidence={selectedEvidence} />}
          {(selectedEvidence?.media_type === "VIDEO" || selectedEvidence?.media_type === "AUDIO") && (
            <VideoAudioLab evidence={selectedEvidence} />
          )}
        </div>
      )}

      {/* ----------------- TAB: SUBJECTS & TRACKS ----------------- */}
      {activeTab === "subjects" && (
        <SubjectTrackManager
          caseId={caseId}
          subjects={subjects}
          faceTracks={faceTracks}
          onRefresh={loadCaseData}
        />
      )}

      {/* ----------------- TAB: LIVE ANALYSIS PIPELINE ----------------- */}
      {activeTab === "analysis" && (
        <div className="space-y-6">
          {analyzing && (
            <div className="bg-white/80 backdrop-blur-md border border-[#FBCFE8] rounded-2xl p-6 space-y-4 shadow-sm">
              <div className="flex items-center space-x-3 text-sm font-bold text-[#2D1B46] font-mono">
                <div className="w-5 h-5 border-2 border-[#EC4899] border-t-transparent rounded-full animate-spin" />
                <span>MULTIMODAL INVESTIGATION PIPELINE ACTIVE</span>
              </div>

              <div className="space-y-2 font-mono text-xs">
                <div className="flex justify-between text-[#86729C]">
                  <span>CURRENT STAGE: <strong className="text-[#9333EA]">{analysisStage}</strong></span>
                  <span>STATUS: RUNNING</span>
                </div>
                <div className="w-full bg-[#FAF5FF] h-2 rounded-full overflow-hidden border border-[#E9D5FF]">
                  <div
                    className="h-full bg-gradient-to-r from-[#F472B6] to-[#C084FC] transition-all duration-500 rounded-full animate-pulse"
                    style={{
                      width:
                        analysisStage === "QUEUED"
                          ? "10%"
                          : analysisStage === "INGESTION_INTEGRITY"
                          ? "25%"
                          : analysisStage === "METADATA_EXTRACTION"
                          ? "40%"
                          : analysisStage === "FACE_DETECTION"
                          ? "60%"
                          : analysisStage === "VIT_INFERENCE"
                          ? "75%"
                          : analysisStage === "TEMPORAL_ANALYSIS"
                          ? "85%"
                          : analysisStage === "MULTIMODAL_FUSION"
                          ? "95%"
                          : "100%"
                    }}
                  />
                </div>
                <p className="text-[11px] text-[#86729C] italic">{analysisMessage}</p>
              </div>
            </div>
          )}

          {analysis && (
            <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-6 space-y-6 shadow-xs font-mono text-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#F3E8FF] pb-4 gap-4">
                <div>
                  <h3 className="text-base font-bold text-[#2D1B46]">
                    Analysis Outcome #{analysis.id} &bull; Pipeline v{analysis.pipeline_version}
                  </h3>
                  <p className="text-[#86729C] text-[11px] mt-0.5">Execution Device: {analysis.inference_device}</p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold ${
                    analysis.assessment === "HIGH_MANIPULATION_LIKELIHOOD"
                      ? "bg-[#FFF1F2] text-[#E11D48] border border-[#FECDD3]"
                      : analysis.assessment === "LOW_MANIPULATION_LIKELIHOOD"
                      ? "bg-[#ECFDF5] text-[#059669] border-[#A7F3D0]"
                      : "bg-[#F3E8FF] text-[#7C3AED] border border-[#E9D5FF]"
                  }`}
                >
                  {analysis.assessment || "PENDING"}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl space-y-1">
                  <div className="text-[#86729C] text-[11px]">CALIBRATED FUSION SCORE</div>
                  <div className="text-2xl font-bold text-[#2D1B46]">
                    {analysis.final_score !== null ? `${(analysis.final_score * 100).toFixed(1)}%` : "N/A"}
                  </div>
                  <div className="text-[10px] text-[#86729C]">Likelihood of synthetic manipulation</div>
                </div>

                <div className="p-4 bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl space-y-1">
                  <div className="text-[#86729C] text-[11px]">CALIBRATED CONFIDENCE</div>
                  <div className="text-2xl font-bold text-[#9333EA]">
                    {analysis.confidence !== null ? `${(analysis.confidence * 100).toFixed(1)}%` : "N/A"}
                  </div>
                  <div className="text-[10px] text-[#86729C]">Based on biometric clarity and signal variance</div>
                </div>

                <div className="p-4 bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl space-y-1">
                  <div className="text-[#86729C] text-[11px]">EVIDENCE CONFLICT STATUS</div>
                  <div className={`text-sm font-bold ${analysis.evidence_conflict ? "text-[#E11D48]" : "text-[#059669]"}`}>
                    {analysis.evidence_conflict ? "CONFLICT OBSERVED" : "SIGNALS CONGRUENT"}
                  </div>
                  <div className="text-[10px] text-[#86729C]">
                    {analysis.conflict_details || "No contradictory signals between visual & acoustic layers."}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ----------------- TAB: TIMELINE ----------------- */}
      {activeTab === "timeline" && (
        <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-6 space-y-6 shadow-xs font-mono text-xs">
          <h3 className="text-sm font-bold text-[#2D1B46] uppercase">Temporal Frame Anomaly Timeline</h3>
          {analysis?.timeline_data && analysis.timeline_data.length > 0 ? (
            <div className="space-y-4">
              <div className="p-4 bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl">
                <div className="h-32 flex items-end gap-1.5 overflow-x-auto pb-2">
                  {analysis.timeline_data.map((pt, i) => {
                    const heightPct = Math.max(8, Math.min(100, pt.score * 100));
                    const isSpike = pt.is_spike || pt.score >= 0.75;
                    return (
                      <div
                        key={i}
                        title={`t=${pt.timestamp}s, score=${(pt.score * 100).toFixed(1)}%`}
                        className="flex flex-col items-center flex-shrink-0 cursor-pointer"
                      >
                        <div
                          style={{ height: `${heightPct}%` }}
                          className={`w-3.5 rounded-t-md transition-all ${
                            isSpike ? "bg-[#E11D48]" : "bg-gradient-to-t from-[#F472B6] to-[#C084FC]"
                          }`}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-[#86729C]">
              Temporal frame sequence will appear here once video analysis executes.
            </div>
          )}
        </div>
      )}

      {/* ----------------- TAB: FINDINGS & REVIEW ----------------- */}
      {activeTab === "findings" && (
        <FindingReviewManager findings={findings} onRefresh={loadCaseData} />
      )}

      {/* ----------------- TAB: REPORTS & EXPORT ----------------- */}
      {activeTab === "reports" && (
        <ReportManifestExport
          caseData={caseData}
          reports={reports}
          analysisId={analysis?.id}
          onRefresh={loadCaseData}
        />
      )}

      {/* ----------------- TAB: AUDIT LOG ----------------- */}
      {activeTab === "audit" && (
        <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 font-mono text-xs shadow-xs">
          <h3 className="text-sm font-bold text-[#2D1B46] uppercase">Immutable Cryptographic Audit Trail</h3>
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

      {/* Modal: Compare Evidence */}
      {showCompareModal && (
        <EvidenceCompareModal
          evidenceList={evidenceList}
          isOpen={showCompareModal}
          onClose={() => setShowCompareModal(false)}
        />
      )}

      {/* Modal: Upload Evidence */}
      {showUpload && (
        <div className="fixed inset-0 bg-[#2D1B46]/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#F3E8FF] rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#F3E8FF] pb-3">
              <h3 className="font-bold text-[#2D1B46] text-base font-mono">Ingest New Media Evidence</h3>
              <button onClick={() => setShowUpload(false)} className="text-[#86729C] hover:text-[#2D1B46]">
                &times;
              </button>
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
                  <div>Size: <span className="text-[#2D1B46] font-bold">{(uploadFile.size / (1024 * 1024)).toFixed(2)} MB</span></div>
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
