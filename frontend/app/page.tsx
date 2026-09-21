"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldAlert,
  Search,
  Hash,
  Video,
  Mic,
  FileCheck,
  ChevronRight,
  Activity,
  Cpu,
  Layers,
  ArrowRight
} from "lucide-react";

export default function LandingPage() {
  const pillars = [
    {
      icon: ShieldAlert,
      title: "Multimodal AI Detection",
      desc: "Real executable Vision Transformer (ViT) deepfake classifiers combined with OpenCV YuNet 5-point facial landmark geometry."
    },
    {
      icon: Search,
      title: "Explainable Forensics",
      desc: "Gradient-based saliency heatmaps, JPEG Error Level Analysis (ELA), and 2D FFT azimuthal frequency power spectrum profiling."
    },
    {
      icon: Hash,
      title: "Cryptographic Evidence Integrity",
      desc: "Instantaneous SHA-256 evidence hashing at ingestion, immutable byte storage, and tamper-verification audits."
    },
    {
      icon: Video,
      title: "Temporal Dynamics & Tracking",
      desc: "Face tracking across consecutive video frames measuring inter-frame landmark drift, score volatility, and anomaly spike intervals."
    },
    {
      icon: Mic,
      title: "Acoustic Signal & AV Sync",
      desc: "Short-Time Fourier Transform (STFT), pitch tracking, spectral flatness, and mouth aperture vs audio energy cross-correlation."
    },
    {
      icon: FileCheck,
      title: "Professional Forensic Reporting",
      desc: "Court-ready structured PDF documentation with evidence hashes, methodology disclosure, finding codes, and probabilistic limitations."
    }
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-16 py-6">
      {/* Hero Section */}
      <div className="text-center space-y-6 pt-8 pb-4">
        <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-[#FCE7F3] to-[#F3E8FF] border border-[#FBCFE8] text-[#BE185D] text-xs font-mono font-semibold shadow-xs">
          <span className="w-2 h-2 rounded-full bg-[#EC4899] animate-pulse" />
          <span>PRODUCTION-GRADE MULTIMODAL FORENSIC PLATFORM</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-[#2D1B46] leading-tight">
          DEEPFAKE FORENSICS, <br />
          <span className="bg-gradient-to-r from-[#EC4899] via-[#D946EF] to-[#8B5CF6] bg-clip-text text-transparent">
            BUILT FOR INVESTIGATIONS.
          </span>
        </h1>

        <p className="max-w-2xl mx-auto text-base sm:text-lg text-[#7E6A94] leading-relaxed">
          Detect. Analyze. Explain. Preserve digital evidence with multimodal AI-powered media forensics.
          Zero mock models, absolute cryptographic chain of custody, and honest uncertainty disclosures.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <Link
            href="/cases"
            className="flex items-center space-x-2 bg-gradient-to-r from-[#F472B6] to-[#C084FC] hover:opacity-95 text-white font-semibold px-7 py-3.5 rounded-xl shadow-md hover:shadow-lg transition-all"
          >
            <span>Start Investigation</span>
            <ChevronRight className="w-4 h-4" />
          </Link>

          <Link
            href="/dashboard"
            className="flex items-center space-x-2 bg-white/90 hover:bg-white text-[#2D1B46] border border-[#E9D5FF] font-medium px-7 py-3.5 rounded-xl shadow-xs hover:shadow-sm transition-all"
          >
            <span>Explore Platform</span>
            <ArrowRight className="w-4 h-4 text-[#A855F7]" />
          </Link>
        </div>
      </div>

      {/* Strict No-Mock Guarantee Banner */}
      <div className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] rounded-2xl p-6 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-[#FCE7F3]/40 to-[#F3E8FF]/40 rounded-full blur-3xl pointer-events-none" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10 text-xs font-mono">
          <div className="flex items-start space-x-3">
            <div className="p-2.5 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] text-[#059669]">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-[#2D1B46] uppercase text-sm mb-1">Genuine Inference</div>
              <p className="text-[#7E6A94]">Real PyTorch ViT & ONNX YuNet forward passes. Never hardcodes percentages or simulated outputs.</p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="p-2.5 rounded-xl bg-[#F5F3FF] border border-[#DDD6FE] text-[#7C3AED]">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-[#2D1B46] uppercase text-sm mb-1">Conflict Detection</div>
              <p className="text-[#7E6A94]">Flags contradictory evidence honestly when visual AI and acoustic signal forensics diverge.</p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="p-2.5 rounded-xl bg-[#FDF2F8] border border-[#FBCFE8] text-[#DB2777]">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-[#2D1B46] uppercase text-sm mb-1">Transparent Registry</div>
              <p className="text-[#7E6A94]">Every model version, training corpora limitations, and checkpoint integrity are cryptographically auditable.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Pillars Grid */}
      <div className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-[#2D1B46]">Scientific Forensic Architecture</h2>
          <p className="text-sm text-[#7E6A94]">Engineered for digital forensics laboratories, cyber intelligence, and legal defensibility.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pillars.map((p, idx) => {
            const Icon = p.icon;
            return (
              <div
                key={idx}
                className="bg-white/80 backdrop-blur-md border border-[#F3E8FF] hover:border-[#F472B6] rounded-2xl p-5 shadow-xs hover:shadow-md transition-all space-y-3"
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FCE7F3] to-[#F3E8FF] border border-[#FBCFE8] flex items-center justify-center text-[#EC4899]">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-[#2D1B46] text-base">{p.title}</h3>
                <p className="text-xs text-[#7E6A94] leading-relaxed">{p.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
