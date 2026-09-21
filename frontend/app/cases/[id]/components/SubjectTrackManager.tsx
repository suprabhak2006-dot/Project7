"use client";

import React, { useState } from "react";
import { UserCheck, Plus, Sparkles, ShieldAlert, CheckCircle2, Clock } from "lucide-react";
import { api } from "@/lib/api";
import { Subject, FaceTrack } from "@/types";

interface Props {
  caseId: number;
  subjects: Subject[];
  faceTracks: FaceTrack[];
  onRefresh: () => void;
}

export default function SubjectTrackManager({ caseId, subjects, faceTracks, onRefresh }: Props) {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [label, setLabel] = useState("");
  const [notes, setNotes] = useState("");
  const [creating, setCreating] = useState(false);

  const handleCreateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!label.trim()) return;
    setCreating(true);
    try {
      await api.createSubject(caseId, { label, notes });
      setLabel("");
      setNotes("");
      setShowCreateModal(false);
      onRefresh();
    } catch (err) {
      alert("Failed to create subject");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Subject Management Section */}
      <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-purple-600" />
              Investigation Subjects ({subjects.length})
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Subject profiles and biometric associations (Labels such as &quot;Unknown Person #001&quot;, avoiding unwarranted identity claims).
            </p>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold text-xs flex items-center gap-1.5 shadow-xs hover:opacity-95 transition-all"
          >
            <Plus className="w-4 h-4" /> Add Subject
          </button>
        </div>

        {subjects.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {subjects.map((sub) => (
              <div
                key={sub.id}
                className="p-4 bg-gradient-to-br from-purple-50/50 to-pink-50/40 rounded-xl border border-pink-100 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-bold text-gray-900">{sub.label}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 font-semibold">
                      Subject #{sub.id}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mt-2">{sub.notes || "No investigative notes recorded."}</p>
                </div>
                <div className="text-[11px] text-gray-400 mt-3 pt-2 border-t border-pink-100/80">
                  Added: {new Date(sub.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center border border-dashed border-pink-200 rounded-xl bg-purple-50/20 text-xs text-gray-500">
            No subjects registered for this case yet. Click &quot;Add Subject&quot; to organize face tracks and biometric evidence.
          </div>
        )}
      </div>

      {/* Face Tracking Database Section */}
      <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-5 shadow-xs">
        <h3 className="text-base font-bold text-gray-900 flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-pink-600" />
          Face Tracking Database & Biometric Consistency
        </h3>

        {faceTracks.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {faceTracks.map((ft) => (
              <div
                key={ft.id}
                className="p-4 bg-white rounded-xl border border-pink-100 shadow-2xs space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-purple-900">{ft.track_id_code}</span>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-pink-100 text-pink-800">
                    {ft.frames_count} Frames
                  </span>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between text-gray-600">
                    <span>Active Interval:</span>
                    <span className="font-semibold text-gray-900">
                      {ft.start_time.toFixed(1)}s → {ft.end_time.toFixed(1)}s
                    </span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span>Avg Detection Confidence:</span>
                    <span className="font-semibold text-purple-700">
                      {(ft.avg_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span>Geometry Stability:</span>
                    <span className="font-semibold text-emerald-600">{ft.geometry_stability}</span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span>Texture Consistency:</span>
                    <span className="font-semibold text-purple-700">{ft.texture_consistency}</span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span>Boundary Anomaly:</span>
                    <span className="font-semibold text-rose-600">
                      {(ft.boundary_anomaly_score * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center border border-dashed border-pink-200 rounded-xl bg-pink-50/20 text-xs text-gray-500">
            No persistent face tracks cataloged for this case. Run video forensic analysis to track faces across sequences.
          </div>
        )}
      </div>

      {/* Modal: Add Subject */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-pink-100 p-6 max-w-md w-full shadow-2xl animate-in fade-in zoom-in-95">
            <h3 className="text-base font-bold text-gray-900 mb-1">Create Subject Profile</h3>
            <p className="text-xs text-gray-500 mb-4">
              Designate a subject label (e.g. &quot;Unknown Person #001&quot; or &quot;Subject Alpha&quot;) for evidence correlation.
            </p>

            <form onSubmit={handleCreateSubject} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Subject Label *</label>
                <input
                  type="text"
                  required
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="e.g. Unknown Person #001"
                  className="w-full px-3 py-2 rounded-xl border border-pink-200 text-xs focus:ring-2 focus:ring-purple-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Investigative Notes</label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Describe associated media, physical characteristics, or context..."
                  className="w-full px-3 py-2 rounded-xl border border-pink-200 text-xs focus:ring-2 focus:ring-purple-400 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs font-semibold hover:opacity-95 disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Save Subject"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
