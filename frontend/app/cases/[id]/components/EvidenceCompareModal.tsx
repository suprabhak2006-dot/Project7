"use client";

import React, { useState } from "react";
import { GitCompare, ShieldCheck, AlertTriangle, CheckCircle2, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { Evidence, EvidenceComparisonResult } from "@/types";

interface Props {
  evidenceList: Evidence[];
  isOpen: boolean;
  onClose: () => void;
}

export default function EvidenceCompareModal({ evidenceList, isOpen, onClose }: Props) {
  const [selectedId1, setSelectedId1] = useState<number>(evidenceList[0]?.id || 0);
  const [selectedId2, setSelectedId2] = useState<number>(evidenceList[1]?.id || evidenceList[0]?.id || 0);
  const [result, setResult] = useState<EvidenceComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleCompare = async () => {
    if (!selectedId1 || !selectedId2) return;
    setLoading(true);
    try {
      const res = await api.compareEvidence(selectedId1, selectedId2);
      setResult(res);
    } catch (err) {
      alert("Failed to compare evidence items");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-pink-100 p-6 max-w-3xl w-full shadow-2xl animate-in fade-in zoom-in-95 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-pink-100">
          <div>
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <GitCompare className="w-5 h-5 text-purple-600" />
              Cross-Evidence Comparison & Near-Duplicate Detection
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Strictly distinguishes cryptographic equality (bitstream SHA-256) from perceptual visual similarity (DCT pHash).
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-lg font-bold px-2 py-1"
          >
            ✕
          </button>
        </div>

        {/* Evidence Selection Dropdowns */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div className="p-3 bg-purple-50/50 rounded-xl border border-purple-100">
            <label className="block text-xs font-semibold text-purple-950 mb-1.5">Evidence Item A</label>
            <select
              value={selectedId1}
              onChange={(e) => setSelectedId1(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-purple-200 text-xs bg-white focus:outline-none"
            >
              {evidenceList.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.evidence_number} - {e.filename} ({e.media_type})
                </option>
              ))}
            </select>
          </div>

          <div className="p-3 bg-pink-50/50 rounded-xl border border-pink-100">
            <label className="block text-xs font-semibold text-pink-950 mb-1.5">Evidence Item B</label>
            <select
              value={selectedId2}
              onChange={(e) => setSelectedId2(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-pink-200 text-xs bg-white focus:outline-none"
            >
              {evidenceList.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.evidence_number} - {e.filename} ({e.media_type})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex justify-center mb-6">
          <button
            onClick={handleCompare}
            disabled={loading || !selectedId1 || !selectedId2}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold text-xs shadow-md hover:opacity-95 disabled:opacity-50 transition-all"
          >
            {loading ? "Computing Cross-Correlation..." : "Run Scientific Comparison"}
          </button>
        </div>

        {/* Results Display */}
        {result && (
          <div className="space-y-4">
            {/* Near-Duplicate Alert Badge */}
            <div
              className={`p-4 rounded-xl border flex items-center justify-between text-xs font-semibold ${
                result.is_potential_duplicate
                  ? "bg-rose-50 border-rose-200 text-rose-900"
                  : "bg-emerald-50 border-emerald-200 text-emerald-900"
              }`}
            >
              <div className="flex items-center gap-2">
                {result.is_potential_duplicate ? (
                  <AlertTriangle className="w-5 h-5 text-rose-600" />
                ) : (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                )}
                <span>
                  {result.is_potential_duplicate
                    ? "Potential Duplicate or Transcoded Derivative Detected"
                    : "Evidence items are distinct and independent"}
                </span>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-white text-gray-800 border shadow-2xs font-bold">
                Cryptographic: {result.cryptographic_equality}
              </span>
            </div>

            {/* Side-by-Side Metadata Grid */}
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-purple-50/40 rounded-xl border border-purple-100 space-y-2">
                <div className="font-bold text-purple-950 pb-1 border-b border-purple-100">
                  {result.evidence_1.evidence_number} - {result.evidence_1.filename}
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Size:</span>
                  <span className="font-semibold">{(result.evidence_1.file_size / 1024).toFixed(1)} KB</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">SHA-256:</span>
                  <span className="font-mono text-[10px] truncate max-w-[150px]">
                    {result.evidence_1.sha256}
                  </span>
                </div>
              </div>

              <div className="p-4 bg-pink-50/40 rounded-xl border border-pink-100 space-y-2">
                <div className="font-bold text-pink-950 pb-1 border-b border-pink-100">
                  {result.evidence_2.evidence_number} - {result.evidence_2.filename}
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Size:</span>
                  <span className="font-semibold">{(result.evidence_2.file_size / 1024).toFixed(1)} KB</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">SHA-256:</span>
                  <span className="font-mono text-[10px] truncate max-w-[150px]">
                    {result.evidence_2.sha256}
                  </span>
                </div>
              </div>
            </div>

            {/* Perceptual Hash Metrics */}
            {result.visual_similarity && Object.keys(result.visual_similarity).length > 0 && (
              <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 text-xs space-y-2">
                <div className="font-bold text-gray-800">Perceptual & Frequency Hash Correlation:</div>
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2 bg-white rounded border">
                    <span className="text-gray-500 text-[11px]">pHash Similarity</span>
                    <div className="font-bold text-purple-700 text-sm">
                      {((result.visual_similarity.phash_similarity || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-2 bg-white rounded border">
                    <span className="text-gray-500 text-[11px]">dHash Gradient</span>
                    <div className="font-bold text-pink-700 text-sm">
                      {((result.visual_similarity.dhash_similarity || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-2 bg-white rounded border">
                    <span className="text-gray-500 text-[11px]">Color Correlation</span>
                    <div className="font-bold text-emerald-700 text-sm">
                      {((result.visual_similarity.color_similarity || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
                <div className="text-[11px] text-gray-500 italic mt-1">
                  {result.visual_similarity.interpretation}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
