"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderLock,
  FileCheck,
  AlertTriangle,
  FileText,
  Activity,
  ArrowUpRight,
  ShieldCheck
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";
import { api } from "@/lib/api";
import { DashboardStats } from "@/types";

const COLORS = ["#EC4899", "#A855F7", "#F472B6", "#C084FC", "#FB7185"];

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboardStats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center space-x-3 text-sm font-mono text-[#86729C]">
          <div className="w-4 h-4 border-2 border-[#EC4899] border-t-transparent rounded-full animate-spin" />
          <span>QUERYING INVESTIGATION DATABASE...</span>
        </div>
      </div>
    );
  }

  const mediaData = Object.entries(stats.media_types).map(([name, value]) => ({ name, value }));
  const categoryData = Object.entries(stats.findings_by_category).map(([name, value]) => ({
    name: name.replace("_", " ").toLowerCase(),
    count: value
  }));
  const outcomeData = Object.entries(stats.outcomes).map(([name, value]) => ({
    name: name.replace("_", " ").slice(0, 12),
    value
  }));

  const cards = [
    { title: "Active Cases", value: stats.cards.active_cases, icon: FolderLock, color: "text-[#A855F7]" },
    { title: "Total Evidence", value: stats.cards.total_evidence, icon: ShieldCheck, color: "text-[#EC4899]" },
    { title: "Analyses Completed", value: stats.cards.completed_analyses, icon: FileCheck, color: "text-[#10B981]" },
    { title: "Active Jobs", value: stats.cards.processing_jobs, icon: Activity, color: "text-[#F59E0B]" },
    { title: "High-Risk Findings", value: stats.cards.high_findings, icon: AlertTriangle, color: "text-[#E11D48]" },
    { title: "Forensic Reports", value: stats.cards.total_reports, icon: FileText, color: "text-[#7C3AED]" },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#2D1B46]">Forensic Investigation Dashboard</h1>
          <p className="text-xs text-[#86729C] font-mono">Live aggregate metrics queried from primary database.</p>
        </div>
        <Link
          href="/cases"
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#F472B6] to-[#C084FC] hover:opacity-95 text-white font-semibold text-xs font-mono shadow-xs transition-all"
        >
          + NEW INVESTIGATION
        </Link>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {cards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div key={i} className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-4 space-y-2 shadow-xs">
              <div className="flex items-center justify-between text-xs text-[#86729C] font-medium">
                <span>{c.title}</span>
                <Icon className={`w-4 h-4 ${c.color}`} />
              </div>
              <div className="text-2xl font-bold text-[#2D1B46] font-mono">{c.value}</div>
            </div>
          );
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Media Distribution */}
        <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 shadow-xs">
          <h3 className="text-sm font-bold text-[#2D1B46]">Evidence Media Types</h3>
          <div className="h-48 w-full flex items-center justify-center">
            {mediaData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={mediaData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={70}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {mediaData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: "#FFFFFF", borderColor: "#F3E8FF", color: "#2D1B46", fontSize: 12, borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-[#86729C] font-mono">No evidence ingested yet</div>
            )}
          </div>
        </div>

        {/* Findings by Category */}
        <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 shadow-xs">
          <h3 className="text-sm font-bold text-[#2D1B46]">Findings by Modality</h3>
          <div className="h-48 w-full">
            {categoryData.some(d => d.count > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData}>
                  <XAxis dataKey="name" stroke="#86729C" fontSize={10} tickLine={false} />
                  <YAxis stroke="#86729C" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: "#FFFFFF", borderColor: "#F3E8FF", color: "#2D1B46", fontSize: 12, borderRadius: 8 }} />
                  <Bar dataKey="count" fill="#EC4899" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-[#86729C] font-mono">No findings recorded yet</div>
            )}
          </div>
        </div>

        {/* Analysis Outcomes */}
        <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 shadow-xs">
          <h3 className="text-sm font-bold text-[#2D1B46]">Probabilistic Assessments</h3>
          <div className="h-48 w-full flex items-center justify-center">
            {outcomeData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={outcomeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={70}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {outcomeData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[(index + 2) % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: "#FFFFFF", borderColor: "#F3E8FF", color: "#2D1B46", fontSize: 12, borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-[#86729C] font-mono">No completed analyses yet</div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Cases Table */}
      <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-5 space-y-4 shadow-xs">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#2D1B46]">Recent Active Investigations</h3>
          <Link href="/cases" className="text-xs text-[#EC4899] hover:underline font-mono flex items-center space-x-1 font-bold">
            <span>VIEW ALL CASES</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="border-b border-[#F3E8FF] text-[#86729C]">
              <tr>
                <th className="pb-3 font-semibold">CASE NUMBER</th>
                <th className="pb-3 font-semibold">TITLE</th>
                <th className="pb-3 font-semibold">STATUS</th>
                <th className="pb-3 font-semibold">PRIORITY</th>
                <th className="pb-3 font-semibold">DATE</th>
                <th className="pb-3 font-semibold text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F3E8FF]">
              {stats.recent_cases.length > 0 ? (
                stats.recent_cases.map((c) => (
                  <tr key={c.id} className="hover:bg-[#FDF2F8]/60 transition-all">
                    <td className="py-3 font-bold text-[#2D1B46]">{c.case_number}</td>
                    <td className="py-3 text-[#2D1B46] font-medium">{c.title}</td>
                    <td className="py-3">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#FAF5FF] text-[#9333EA] border border-[#E9D5FF]">
                        {c.status}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold ${
                        c.priority === "HIGH" || c.priority === "CRITICAL"
                          ? "bg-[#FFF1F2] text-[#E11D48] border border-[#FECDD3]"
                          : "bg-[#F3E8FF] text-[#7C3AED]"
                      }`}>
                        {c.priority}
                      </span>
                    </td>
                    <td className="py-3 text-[#86729C]">{new Date(c.created_at).toLocaleDateString()}</td>
                    <td className="py-3 text-right">
                      <Link
                        href={`/cases/${c.id}`}
                        className="text-[#EC4899] font-bold hover:underline"
                      >
                        Open Case &rarr;
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-[#86729C]">
                    No cases recorded in database. Click &quot;+ New Investigation&quot; to begin.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
