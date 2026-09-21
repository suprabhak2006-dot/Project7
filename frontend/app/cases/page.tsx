"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { FolderLock, Plus, Search, Filter, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { Case, CasePriority } from "@/types";

export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("");

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<CasePriority>("MEDIUM");
  const [creating, setCreating] = useState(false);

  const fetchCases = async () => {
    try {
      const data = await api.getCases(filterStatus || undefined);
      setCases(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, [filterStatus]);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setCreating(true);
    try {
      await api.createCase({ title, description, priority });
      setTitle("");
      setDescription("");
      setShowModal(false);
      await fetchCases();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create case");
    } finally {
      setCreating(false);
    }
  };

  const filteredCases = cases.filter(
    (c) =>
      c.title.toLowerCase().includes(search.toLowerCase()) ||
      c.case_number.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#2D1B46]">Forensic Cases</h1>
          <p className="text-xs text-[#86729C] font-mono">
            Manage evidence files, chain of custody logs, and multi-modal investigation pipelines.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 bg-gradient-to-r from-[#F472B6] to-[#C084FC] hover:opacity-95 text-white font-semibold px-4 py-2.5 rounded-xl text-xs font-mono shadow-xs transition-all self-start"
        >
          <Plus className="w-4 h-4" />
          <span>NEW CASE</span>
        </button>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-[#86729C]" />
          <input
            type="text"
            placeholder="Search by case number or title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-white/80 border border-[#F3E8FF] rounded-xl pl-10 pr-4 py-2.5 text-xs text-[#2D1B46] placeholder-[#86729C] focus:outline-none focus:border-[#F472B6] shadow-xs"
          />
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-[#86729C]" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-white/80 border border-[#F3E8FF] rounded-xl px-3.5 py-2.5 text-xs text-[#2D1B46] focus:outline-none focus:border-[#F472B6] font-mono shadow-xs"
          >
            <option value="">ALL STATUSES</option>
            <option value="OPEN">OPEN</option>
            <option value="IN_PROGRESS">IN PROGRESS</option>
            <option value="UNDER_REVIEW">UNDER REVIEW</option>
            <option value="CLOSED">CLOSED</option>
          </select>
        </div>
      </div>

      {/* Cases Table */}
      <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl overflow-hidden shadow-xs">
        {loading ? (
          <div className="py-12 text-center text-xs text-[#86729C] font-mono">Loading cases...</div>
        ) : filteredCases.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="border-b border-[#F3E8FF] bg-[#FAF5FF]/70 text-[#86729C]">
                <tr>
                  <th className="py-3 px-4 font-semibold">CASE NUMBER</th>
                  <th className="py-3 px-4 font-semibold">TITLE</th>
                  <th className="py-3 px-4 font-semibold">PRIORITY</th>
                  <th className="py-3 px-4 font-semibold">STATUS</th>
                  <th className="py-3 px-4 font-semibold">EVIDENCE</th>
                  <th className="py-3 px-4 font-semibold">CREATED</th>
                  <th className="py-3 px-4 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F3E8FF]">
                {filteredCases.map((c) => (
                  <tr key={c.id} className="hover:bg-[#FDF2F8]/60 transition-all">
                    <td className="py-3.5 px-4 font-bold text-[#2D1B46] flex items-center space-x-2">
                      <FolderLock className="w-4 h-4 text-[#A855F7]" />
                      <span>{c.case_number}</span>
                    </td>
                    <td className="py-3.5 px-4 text-[#2D1B46] font-medium">{c.title}</td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold ${
                        c.priority === "HIGH" || c.priority === "CRITICAL"
                          ? "bg-[#FFF1F2] text-[#E11D48] border border-[#FECDD3]"
                          : "bg-[#F3E8FF] text-[#7C3AED]"
                      }`}>
                        {c.priority}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#FAF5FF] text-[#9333EA] border border-[#E9D5FF]">
                        {c.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-[#86729C]">{c.evidence_count || 0} files</td>
                    <td className="py-3.5 px-4 text-[#86729C]">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/cases/${c.id}`}
                        className="px-3 py-1.5 bg-[#FAF5FF] hover:bg-[#FCE7F3] text-[#EC4899] border border-[#E9D5FF] rounded-lg text-[11px] font-bold transition-all"
                      >
                        Enter Case &rarr;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-xs text-[#86729C] font-mono space-y-2">
            <AlertCircle className="w-6 h-6 mx-auto text-[#EC4899]" />
            <div>No cases found matching your criteria.</div>
          </div>
        )}
      </div>

      {/* New Case Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-[#2D1B46]/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#F3E8FF] rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#F3E8FF] pb-3">
              <h3 className="font-bold text-[#2D1B46] text-base">Initialize New Forensic Case</h3>
              <button onClick={() => setShowModal(false)} className="text-[#86729C] hover:text-[#2D1B46]">&times;</button>
            </div>

            <form onSubmit={handleCreateCase} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-[#86729C] mb-1 font-semibold">CASE TITLE *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Suspected Executive Video Impersonation"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl p-3 text-[#2D1B46] focus:outline-none focus:border-[#F472B6]"
                />
              </div>

              <div>
                <label className="block text-[#86729C] mb-1 font-semibold">CASE DESCRIPTION</label>
                <textarea
                  rows={3}
                  placeholder="Case context, origin of suspicious media, referral details..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl p-3 text-[#2D1B46] focus:outline-none focus:border-[#F472B6]"
                />
              </div>

              <div>
                <label className="block text-[#86729C] mb-1 font-semibold">INVESTIGATION PRIORITY</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as CasePriority)}
                  className="w-full bg-[#FAF5FF] border border-[#E9D5FF] rounded-xl p-3 text-[#2D1B46] focus:outline-none focus:border-[#F472B6]"
                >
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl bg-[#FAF5FF] text-[#2D1B46] hover:bg-[#F3E8FF] border border-[#E9D5FF] font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-[#F472B6] to-[#C084FC] hover:opacity-95 text-white font-semibold shadow-xs"
                >
                  {creating ? "Creating..." : "Create Case"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
