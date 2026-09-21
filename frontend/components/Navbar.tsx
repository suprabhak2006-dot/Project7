"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Shield, Cpu, Activity, User as UserIcon } from "lucide-react";
import { api } from "@/lib/api";
import { User } from "@/types";

export default function Navbar() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.getCurrentUser().then(setUser).catch(() => {});
  }, []);

  return (
    <header className="h-16 border-b border-[#F3E8FF] bg-white/80 backdrop-blur-md sticky top-0 z-40 px-6 flex items-center justify-between shadow-xs">
      {/* Brand */}
      <div className="flex items-center space-x-3">
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
      </div>

      {/* System Status Indicators */}
      <div className="flex items-center space-x-4 text-xs font-mono">
        <div className="hidden md:flex items-center space-x-2 bg-white/90 border border-[#F3E8FF] px-3 py-1.5 rounded-lg shadow-xs">
          <Activity className="w-3.5 h-3.5 text-[#10B981] animate-pulse" />
          <span className="text-[#86729C]">CORE PIPELINE:</span>
          <span className="text-[#059669] font-semibold">VERIFIED / LIVE</span>
        </div>

        <div className="hidden sm:flex items-center space-x-2 bg-white/90 border border-[#F3E8FF] px-3 py-1.5 rounded-lg shadow-xs">
          <Cpu className="w-3.5 h-3.5 text-[#A855F7]" />
          <span className="text-[#86729C]">INFERENCE:</span>
          <span className="text-[#2D1B46] font-semibold">CPU (ONNX / TORCH)</span>
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
