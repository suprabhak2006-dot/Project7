"use client";

import React, { useEffect, useState } from "react";
import { Activity, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { ModelStatusEntry } from "@/types";

export default function ModelRegistryPage() {
  const [models, setModels] = useState<ModelStatusEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await api.getModelStatus();
      setModels(res.models);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#2D1B46]">Forensic Model Registry</h1>
          <p className="text-xs text-[#86729C] font-mono">
            Auditable inventory of computer vision, acoustic, and temporal neural architectures.
          </p>
        </div>
        <button
          onClick={fetchStatus}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white hover:bg-[#FAF5FF] border border-[#E9D5FF] text-xs font-mono text-[#2D1B46] shadow-xs transition-all font-semibold"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>RUN HEALTH CHECK</span>
        </button>
      </div>

      {/* Strict Transparency Note */}
      <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-4 flex items-center space-x-3 text-xs font-mono shadow-xs">
        <div className="p-2.5 rounded-xl bg-[#FAF5FF] border border-[#E9D5FF] text-[#9333EA]">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <span className="font-bold text-[#2D1B46]">LIVE MODEL REGISTRY POLICY:</span>
          <span className="text-[#86729C] ml-2">
            Models are verified directly against checkpoints on disk. Missing or unloaded models explicitly display UNAVAILABLE rather than generating fabricated outputs.
          </span>
        </div>
      </div>

      {/* Models Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs">
        {models.map((m) => {
          const isReady = m.status === "READY";
          return (
            <div
              key={m.name}
              className={`bg-white/80 backdrop-blur-md border rounded-2xl p-5 space-y-4 shadow-xs transition-all ${
                isReady ? "border-[#F3E8FF] hover:border-[#F472B6]" : "border-[#FECDD3] bg-[#FFF1F2]/50"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-[#2D1B46] text-sm">{m.name.toUpperCase()}</span>
                    <span className="text-[10px] text-[#86729C]">v{m.version}</span>
                  </div>
                  <div className="text-[11px] text-[#9333EA] font-semibold">{m.task}</div>
                </div>

                <span
                  className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                    isReady
                      ? "bg-[#ECFDF5] text-[#059669] border-[#A7F3D0]"
                      : "bg-[#FFF1F2] text-[#E11D48] border-[#FECDD3]"
                  }`}
                >
                  {m.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 py-2 border-y border-[#F3E8FF] text-[11px]">
                <div>
                  <span className="text-[#86729C]">Framework:</span> <span className="text-[#2D1B46] font-medium">{m.framework}</span>
                </div>
                <div>
                  <span className="text-[#86729C]">Device:</span> <span className="text-[#2D1B46] font-medium">{m.device}</span>
                </div>
                <div>
                  <span className="text-[#86729C]">Weights:</span>{" "}
                  <span className={m.checkpoint_verified ? "text-[#059669] font-bold" : "text-[#E11D48] font-bold"}>
                    {m.checkpoint_verified ? "VERIFIED (SHA-256)" : "NOT LOADED"}
                  </span>
                </div>
                <div>
                  <span className="text-[#86729C]">Runtime:</span>{" "}
                  <span className={m.loaded ? "text-[#059669] font-bold" : "text-[#86729C]"}>
                    {m.loaded ? "INITIALIZED" : "STANDBY"}
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                <div className="text-[#86729C] text-[10px] uppercase font-bold">Documented Limitations & Bounds:</div>
                <p className="text-[11px] text-[#2D1B46] leading-relaxed bg-[#FAF5FF] p-3 rounded-xl border border-[#E9D5FF]">
                  {m.limitations}
                </p>
              </div>

              <div className="text-[10px] text-[#86729C] text-right">
                Health Check: {new Date(m.last_health_check).toUTCString()}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
