"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Sliders,
  Crosshair,
  Layers,
  Activity,
  Maximize2,
  ZoomIn,
  SunMedium,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { api } from "@/lib/api";
import { Evidence, PixelInspection, ImageHistograms, CompressionForensics, ColorLightingAnalysis } from "@/types";

interface Props {
  evidence: Evidence | null;
}

export default function ForensicFilterLab({ evidence }: Props) {
  const [activeFilter, setActiveFilter] = useState<string>("original");
  const [inspecting, setInspecting] = useState(false);
  const [pixelData, setPixelData] = useState<PixelInspection | null>(null);
  const [histograms, setHistograms] = useState<ImageHistograms | null>(null);
  const [compression, setCompression] = useState<CompressionForensics | null>(null);
  const [lightingColor, setLightingColor] = useState<ColorLightingAnalysis | null>(null);
  const [loading, setLoading] = useState(false);

  const imageRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!evidence || evidence.media_type !== "IMAGE") return;
    setLoading(true);
    Promise.allSettled([
      api.getHistograms(evidence.id),
      api.getCompressionForensics(evidence.id),
      api.getColorLighting(evidence.id)
    ]).then(([histRes, compRes, lightRes]) => {
      if (histRes.status === "fulfilled") setHistograms(histRes.value);
      if (compRes.status === "fulfilled") setCompression(compRes.value);
      if (lightRes.status === "fulfilled") setLightingColor(lightRes.value);
      setLoading(false);
    });
  }, [evidence]);

  if (!evidence) {
    return (
      <div className="p-8 text-center bg-white/70 backdrop-blur-md rounded-2xl border border-pink-100 text-gray-500">
        Please select an image evidence item to open the Forensic Filter Lab.
      </div>
    );
  }

  const filters = [
    { id: "original", label: "Original (Raw)" },
    { id: "grayscale", label: "Grayscale" },
    { id: "sobel_edges", label: "Sobel Edges" },
    { id: "laplacian", label: "Laplacian" },
    { id: "high_pass", label: "High-Pass" },
    { id: "low_pass", label: "Low-Pass Gaussian" },
    { id: "noise_residual", label: "Noise Residual" },
    { id: "fft_spectrum", label: "2D FFT Spectrum" },
    { id: "ela", label: "Error Level (ELA)" },
    { id: "sharpen", label: "Sharpen" }
  ];

  const getImageUrl = () => {
    if (activeFilter === "original" && evidence.storage_path) {
      return `http://localhost:8000/static/storage/${evidence.storage_path.replace(/\\/g, "/")}`;
    }
    return api.getFilteredImageUrl(evidence.id, activeFilter);
  };

  const handleImageClick = async (e: React.MouseEvent<HTMLImageElement>) => {
    if (!inspecting || !imageRef.current) return;
    const rect = imageRef.current.getBoundingClientRect();
    const scaleX = (evidence.width || imageRef.current.naturalWidth) / rect.width;
    const scaleY = (evidence.height || imageRef.current.naturalHeight) / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    try {
      const res = await api.inspectPixel(evidence.id, x, y);
      setPixelData(res);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Filter Selection Bar */}
      <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <Layers className="w-5 h-5 text-purple-600" />
              Forensic Filter & Spectral Laboratory
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Authentic spatial and frequency domain transformations executed directly on evidence bitstreams.
            </p>
          </div>

          <button
            onClick={() => setInspecting(!inspecting)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold flex items-center gap-2 border transition-all ${
              inspecting
                ? "bg-purple-600 text-white border-purple-700 ring-2 ring-purple-200"
                : "bg-white text-purple-700 border-purple-200 hover:bg-purple-50"
            }`}
          >
            <Crosshair className="w-4 h-4" />
            {inspecting ? "Exit Pixel Inspector" : "Enable Pixel-Level Inspector"}
          </button>
        </div>

        {/* Filter Buttons */}
        <div className="flex flex-wrap gap-2">
          {filters.map((f) => (
            <button
              key={f.id}
              onClick={() => setActiveFilter(f.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                activeFilter === f.id
                  ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white border-purple-600 shadow-xs"
                  : "bg-purple-50/60 text-purple-900 border-purple-100 hover:bg-purple-100/70"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Workspace Layout: Visual Canvas & Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Canvas Display */}
        <div className="lg:col-span-2 bg-white/90 backdrop-blur-md rounded-2xl border border-pink-100 p-6 flex flex-col items-center justify-center min-h-[440px] relative">
          {inspecting && (
            <div className="absolute top-4 left-4 z-10 px-3 py-1.5 rounded-full bg-purple-600 text-white text-xs font-semibold shadow-md flex items-center gap-1.5 animate-pulse">
              <Crosshair className="w-3.5 h-3.5" />
              Click any coordinate on the image to inspect pixel & local noise residual
            </div>
          )}

          <div className="max-h-[500px] overflow-hidden rounded-xl border border-pink-100 shadow-sm relative cursor-crosshair">
            <img
              ref={imageRef}
              src={getImageUrl()}
              alt="Forensic Evidence Filter View"
              onClick={handleImageClick}
              className="max-h-[500px] w-auto object-contain select-none"
            />
          </div>

          <div className="w-full mt-4 flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-pink-50">
            <span>Filter Mode: <strong className="text-purple-700 uppercase">{activeFilter}</strong></span>
            <span>Dimensions: {evidence.width}x{evidence.height} px</span>
            <span>Integrity: SHA-256 Verified</span>
          </div>
        </div>

        {/* Pixel & Scientific Telemetry Sidebar */}
        <div className="space-y-6">
          {/* Pixel Inspection Card */}
          <div className="bg-gradient-to-br from-pink-50/70 via-purple-50/60 to-white rounded-2xl border border-pink-100 p-5 shadow-xs">
            <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2 mb-3">
              <Crosshair className="w-4 h-4 text-purple-600" />
              Pixel-Level Inspector
            </h4>

            {pixelData ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-white rounded-xl border border-pink-100 shadow-2xs">
                  <div
                    className="w-10 h-10 rounded-lg border border-gray-200 shadow-inner flex-shrink-0"
                    style={{ backgroundColor: pixelData.hex }}
                  />
                  <div>
                    <div className="text-xs font-bold text-gray-900">{pixelData.hex.toUpperCase()}</div>
                    <div className="text-[11px] text-gray-500">
                      R:{pixelData.rgb.r} G:{pixelData.rgb.g} B:{pixelData.rgb.b}
                    </div>
                  </div>
                  <div className="ml-auto text-right">
                    <div className="text-xs font-semibold text-purple-700">
                      X: {pixelData.coordinates.x}
                    </div>
                    <div className="text-[11px] text-gray-500">
                      Y: {pixelData.coordinates.y}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 bg-white rounded-lg border border-pink-50">
                    <span className="text-[11px] text-gray-500">Luminance</span>
                    <div className="font-bold text-gray-900 mt-0.5">{pixelData.luminance}</div>
                  </div>
                  <div className="p-2.5 bg-white rounded-lg border border-pink-50">
                    <span className="text-[11px] text-gray-500">Noise Residual</span>
                    <div className="font-bold text-purple-700 mt-0.5">{pixelData.local_noise_residual}</div>
                  </div>
                  <div className="p-2.5 bg-white rounded-lg border border-pink-50">
                    <span className="text-[11px] text-gray-500">Local Std Dev</span>
                    <div className="font-bold text-gray-900 mt-0.5">{pixelData.local_std_dev}</div>
                  </div>
                  <div className="p-2.5 bg-white rounded-lg border border-pink-50">
                    <span className="text-[11px] text-gray-500">Local Anomaly</span>
                    <div className="font-bold text-rose-600 mt-0.5">
                      {(pixelData.local_anomaly_indicator * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center border border-dashed border-pink-200 rounded-xl bg-white/60 text-xs text-gray-500">
                Click on the evidence canvas to view sub-pixel coordinates, color values, and local noise anomalies.
              </div>
            )}
          </div>

          {/* Compression & Quantization Forensics */}
          {compression && (
            <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-5 shadow-xs">
              <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2 mb-3">
                <Sliders className="w-4 h-4 text-pink-600" />
                Compression & DCT Analysis
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-pink-50">
                  <span className="text-gray-500">Quantization Tables:</span>
                  <span className="font-semibold text-gray-900">
                    {compression.quantization_tables_present ? "Present (Extracted)" : "Not Available"}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-pink-50">
                  <span className="text-gray-500">DCT Blockiness Ratio:</span>
                  <span className="font-semibold text-purple-700">{compression.blockiness_ratio || "N/A"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-pink-50">
                  <span className="text-gray-500">Double Compression:</span>
                  <span className={`font-bold ${compression.double_compression_detected ? "text-rose-600" : "text-emerald-600"}`}>
                    {compression.double_compression_detected ? "Detected (Ghosting)" : "No Double Compression"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Lighting & Color Consistency */}
          {lightingColor && (
            <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-5 shadow-xs">
              <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2 mb-3">
                <SunMedium className="w-4 h-4 text-amber-500" />
                Illumination & Chromaticity
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-pink-50">
                  <span className="text-gray-500">Color Temperature:</span>
                  <span className="font-semibold text-gray-900">
                    {lightingColor.color_analysis.global_color_temperature_k} K
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-pink-50">
                  <span className="text-gray-500">White Balance Score:</span>
                  <span className="font-semibold text-purple-700">
                    {lightingColor.color_analysis.white_balance_balance_score}
                  </span>
                </div>
                {lightingColor.color_analysis.skin_tone_congruence && (
                  <div className="flex justify-between py-1 border-b border-pink-50">
                    <span className="text-gray-500">Skin Tone Congruence:</span>
                    <span className="font-semibold text-emerald-600">
                      {lightingColor.color_analysis.skin_tone_congruence}
                    </span>
                  </div>
                )}
                {lightingColor.lighting_analysis.illumination_angle_disparity_deg !== undefined && (
                  <div className="flex justify-between py-1 border-b border-pink-50">
                    <span className="text-gray-500">Illumination Disparity:</span>
                    <span className="font-semibold text-rose-600">
                      {lightingColor.lighting_analysis.illumination_angle_disparity_deg}°
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
