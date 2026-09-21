"use client";

import React, { useState } from "react";
import { CheckCircle, XCircle, Clock, MessageSquare, ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";
import { Finding, ReviewStatus } from "@/types";

interface Props {
  findings: Finding[];
  onRefresh: () => void;
}

export default function FindingReviewManager({ findings, onRefresh }: Props) {
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>("CONFIRMED");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const handleOpenReview = (f: Finding) => {
    setReviewingId(f.id);
    setSelectedStatus(f.review_status && f.review_status !== "PENDING" ? f.review_status : "CONFIRMED");
    setNotes(f.reviewer_notes || "");
  };

  const handleSaveReview = async () => {
    if (!reviewingId) return;
    setSaving(true);
    try {
      await api.reviewFinding(reviewingId, selectedStatus, notes);
      setReviewingId(null);
      onRefresh();
    } catch (err) {
      alert("Failed to submit review");
    } finally {
      setSaving(false);
    }
  };

  const getReviewBadge = (status?: ReviewStatus) => {
    switch (status) {
      case "CONFIRMED":
        return <span className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 font-bold text-xs flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> Confirmed</span>;
      case "DISPUTED":
        return <span className="px-2.5 py-1 rounded-full bg-rose-100 text-rose-800 font-bold text-xs flex items-center gap-1"><XCircle className="w-3.5 h-3.5" /> Disputed</span>;
      case "NEEDS_REVIEW":
        return <span className="px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 font-bold text-xs flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> Needs Review</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 font-medium text-xs flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> Pending Review</span>;
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-6 shadow-xs space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-pink-50">
        <div>
          <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-purple-600" />
            Investigator Review Mode (Human vs AI Provenance)
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Strict chain of custody: Human decisions never overwrite raw AI outputs. Both assessments are preserved independently.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {findings.map((f) => (
          <div
            key={f.id}
            className="p-4 bg-gradient-to-r from-purple-50/30 via-pink-50/20 to-white rounded-xl border border-pink-100 space-y-3"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-bold text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-900 font-mono">
                  {f.finding_code}
                </span>
                <span className="text-xs text-gray-500">{f.model_name} v{f.model_version}</span>
              </div>
              <div className="flex items-center gap-3">
                {getReviewBadge(f.review_status)}
                <button
                  onClick={() => handleOpenReview(f)}
                  className="px-3 py-1 rounded-lg text-xs font-semibold bg-white border border-purple-200 text-purple-700 hover:bg-purple-50 transition-all shadow-2xs"
                >
                  Review Finding
                </button>
              </div>
            </div>

            <p className="text-xs text-gray-800 leading-relaxed">{f.description}</p>

            {/* AI vs Human Split Telemetry */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-pink-50 text-xs">
              <div className="p-2.5 bg-white rounded-lg border border-pink-50">
                <span className="text-[11px] text-gray-500 uppercase font-semibold">AI Assessment:</span>
                <div className="font-bold text-purple-900 mt-0.5">
                  Anomaly Score: {(f.score * 100).toFixed(1)}% | Confidence: {(f.confidence * 100).toFixed(1)}%
                </div>
              </div>

              <div className="p-2.5 bg-white rounded-lg border border-pink-50">
                <span className="text-[11px] text-gray-500 uppercase font-semibold">Investigator Assessment:</span>
                <div className="font-bold text-gray-900 mt-0.5">
                  {f.review_status || "Pending Review"}
                  {f.reviewer_notes && (
                    <span className="font-normal text-gray-600 block text-[11px] mt-0.5 italic">
                      &quot;{f.reviewer_notes}&quot;
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {findings.length === 0 && (
          <div className="p-8 text-center border border-dashed border-pink-200 rounded-xl bg-purple-50/20 text-xs text-gray-500">
            No forensic findings generated yet. Run analysis on evidence to populate investigative findings.
          </div>
        )}
      </div>

      {/* Review Modal */}
      {reviewingId && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-pink-100 p-6 max-w-md w-full shadow-2xl animate-in fade-in zoom-in-95">
            <h3 className="text-base font-bold text-gray-900 mb-1">Submit Forensic Review</h3>
            <p className="text-xs text-gray-500 mb-4">
              Formalize investigator judgment. The original AI prediction is cryptographically retained in audit records.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Review Decision</label>
                <div className="grid grid-cols-3 gap-2">
                  {["CONFIRMED", "DISPUTED", "NEEDS_REVIEW"].map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setSelectedStatus(st)}
                      className={`py-2 px-2 rounded-xl text-xs font-bold border transition-all ${
                        selectedStatus === st
                          ? "bg-purple-600 text-white border-purple-700"
                          : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100"
                      }`}
                    >
                      {st.replace("_", " ")}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Investigative Rationale</label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="State technical justification, corroborating evidence, or dispute rationale..."
                  className="w-full px-3 py-2 rounded-xl border border-pink-200 text-xs focus:ring-2 focus:ring-purple-400 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setReviewingId(null)}
                  className="px-4 py-2 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={saving}
                  onClick={handleSaveReview}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs font-semibold hover:opacity-95 disabled:opacity-50"
                >
                  {saving ? "Registering..." : "Record Review"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
