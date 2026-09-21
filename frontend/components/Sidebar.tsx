"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderLock,
  Cpu,
  Home
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { name: "Overview", href: "/", icon: Home },
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Cases & Evidence", href: "/cases", icon: FolderLock },
    { name: "Model Registry", href: "/models", icon: Cpu },
  ];

  return (
    <aside className="w-64 border-r border-[#F3E8FF] bg-white/70 backdrop-blur-md flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        <div>
          <div className="text-[10px] font-mono font-semibold uppercase tracking-wider text-[#86729C] px-3 mb-2">
            Investigation Suite
          </div>
          <nav className="space-y-1">
            {links.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href || (link.href !== "/" && pathname?.startsWith(link.href));
              return (
                <Link
                  key={link.name}
                  href={link.href}
                  className={`flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? "bg-gradient-to-r from-[#FDF2F8] to-[#FAF5FF] text-[#EC4899] border-l-4 border-[#EC4899] font-bold shadow-xs"
                      : "text-[#86729C] hover:text-[#2D1B46] hover:bg-[#FAF5FF]"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-[#EC4899]" : "text-[#86729C]"}`} />
                  <span>{link.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="bg-gradient-to-br from-[#FDF2F8] to-[#FAF5FF] border border-[#F3E8FF] rounded-xl p-3.5 shadow-xs">
          <div className="flex items-center space-x-2 text-[11px] font-bold text-[#2D1B46] mb-1 font-mono">
            <span className="w-2 h-2 rounded-full bg-[#10B981] animate-ping" />
            <span>STRICT NO-MOCK POLICY</span>
          </div>
          <p className="text-[10px] text-[#86729C] leading-relaxed">
            All inferences run real PyTorch/ONNX vision & acoustic pipelines. Unprocessed or failed models report MODEL UNAVAILABLE.
          </p>
        </div>
      </div>

      <div className="border-t border-[#F3E8FF] pt-4 text-[10px] text-[#86729C] font-mono">
        <div className="font-semibold text-[#2D1B46]">DeepTrace AI v1.0.0</div>
        <div className="text-[9px] text-[#86729C] mt-0.5">SHA-256 Verified Chains</div>
      </div>
    </aside>
  );
}
