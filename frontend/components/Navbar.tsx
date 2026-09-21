"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Shield, Cpu, Activity, User as UserIcon, Search, FileText, CheckCircle2, UserCheck, Eye } from "lucide-react";
import { api } from "@/lib/api";
import { User } from "@/types";

export default function Navbar() {
  const [user, setUser] = useState<User | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any>(null);
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    api.getCurrentUser().then(setUser).catch(() => {});
  }, []);

  const handleSearch = async (val: string) => {
    setSearchQuery(val);
    if (!val.trim()) {
      setSearchResults(null);
      setShowSearchDropdown(false);
      return;
    }
    setSearching(true);
    setShowSearchDropdown(true);
    try {
      const res = await api.globalSearch(val);
      setSearchResults(res.results);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  return (
    <header className="h-16 border-b border-[#F3E8FF] bg-white/80 backdrop-blur-md sticky top-0 z-40 px-6 flex items-center justify-between shadow-xs">
      {/* Brand */}
      <div className="flex items-center space-x-6">
        <Link href="/" className="flex items-center space-x-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#FCE7F3] to-[#F3E8FF] border border-[#FBCFE8] flex items-center justify-center shadow-xs">
            <Shield className="w-5 h-5 text-[#EC4899]" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-bold tracking-wider text-base text-[#2D1B46]">DEEPTRACE</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gradient-to-r from-[#F472B6] to-[#C084FC] text-white shadow-xs">
                AI
              </span>
            </div>
            <p className="text-[10px] text-[#86729C] tracking-wider uppercase font-mono">
              Digital Forensic Lab
            </p>
          </div>
        </Link>

        {/* Global Search Bar (Requirement 43) */}
        <div className="relative hidden md:block w-72 lg:w-96">
          <div className="flex items-center bg-purple-50/50 border border-purple-100 rounded-xl px-3 py-1.5 focus-within:ring-2 focus-within:ring-purple-300 focus-within:bg-white transition-all">
            <Search className="w-4 h-4 text-purple-400 mr-2 flex-shrink-0" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Global Search (Cases, Hash, Evidence, Subjects)..."
              className="w-full text-xs bg-transparent text-gray-900 focus:outline-none"
            />
          </div>

          {/* Search Dropdown */}
          {showSearchDropdown && searchResults && (
            <div className="absolute top-11 left-0 w-full bg-white rounded-2xl border border-pink-100 shadow-2xl p-3 z-50 space-y-3 max-h-[380px] overflow-y-auto">
              <div className="flex justify-between items-center pb-1 border-b border-pink-50 text-[11px] font-bold text-purple-900">
                <span>Unified Forensic Search Results</span>
                <button
                  onClick={() => setShowSearchDropdown(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              {/* Cases */}
              {searchResults.cases?.length > 0 && (
                <div>
                  <span className="text-[10px] uppercase font-bold text-gray-400">Cases</span>
                  <div className="space-y-1 mt-1">
                    {searchResults.cases.map((c: any) => (
                      <Link
                        key={c.id}
                        href={`/cases/${c.id}`}
                        onClick={() => setShowSearchDropdown(false)}
                        className="p-2 rounded-lg hover:bg-purple-50 flex items-center justify-between text-xs"
                      >
                        <span className="font-semibold text-purple-950">{c.case_number}: {c.title}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-100 text-purple-800">{c.status}</span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Evidence */}
              {searchResults.evidence?.length > 0 && (
                <div>
                  <span className="text-[10px] uppercase font-bold text-gray-400">Evidence</span>
                  <div className="space-y-1 mt-1">
                    {searchResults.evidence.map((ev: any) => (
                      <Link
                        key={ev.id}
                        href={`/cases/${ev.case_id}`}
                        onClick={() => setShowSearchDropdown(false)}
                        className="p-2 rounded-lg hover:bg-pink-50 flex items-center justify-between text-xs"
                      >
                        <span className="font-semibold text-pink-950">{ev.evidence_number} ({ev.filename})</span>
                        <span className="text-[10px] text-gray-500">{ev.type}</span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Findings */}
              {searchResults.findings?.length > 0 && (
                <div>
                  <span className="text-[10px] uppercase font-bold text-gray-400">Findings</span>
                  <div className="space-y-1 mt-1">
                    {searchResults.findings.map((f: any) => (
                      <div key={f.id} className="p-2 rounded-lg bg-gray-50 text-xs">
                        <span className="font-bold text-gray-800">{f.code} ({f.severity})</span>
                        <p className="text-[11px] text-gray-600 truncate mt-0.5">{f.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* System Status Indicators */}
      <div className="flex items-center space-x-4 text-xs font-mono">
        <div className="hidden lg:flex items-center space-x-2 bg-white/90 border border-[#F3E8FF] px-3 py-1.5 rounded-lg shadow-xs">
          <Activity className="w-3.5 h-3.5 text-[#10B981] animate-pulse" />
          <span className="text-[#86729C]">CORE PIPELINE:</span>
          <span className="text-[#059669] font-semibold">LIVE</span>
        </div>

        <div className="hidden sm:flex items-center space-x-2 bg-white/90 border border-[#F3E8FF] px-3 py-1.5 rounded-lg shadow-xs">
          <Cpu className="w-3.5 h-3.5 text-[#A855F7]" />
          <span className="text-[#86729C]">INFERENCE:</span>
          <span className="text-[#2D1B46] font-semibold">ONNX / TORCH</span>
        </div>

        {/* User Pill */}
        <div className="flex items-center space-x-2.5 bg-gradient-to-r from-[#FDF2F8] to-[#FAF5FF] border border-[#F3E8FF] px-3 py-1.5 rounded-lg shadow-xs">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#F472B6] to-[#C084FC] flex items-center justify-center text-white">
            <UserIcon className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-[#2D1B46] leading-tight">
              {user ? user.name : "Chief Investigator"}
            </div>
            <div className="text-[9px] text-[#86729C] uppercase tracking-wider font-bold">
              {user ? user.role : "ADMIN"}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
