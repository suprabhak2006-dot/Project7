"use client";

import React, { useState, useEffect } from "react";
import {
  Film,
  Music,
  Activity,
  AlertTriangle,
  Scissors,
  BarChart3,
  Clock,
  Sparkles,
  Volume2
} from "lucide-react";
import { api } from "@/lib/api";
import { Evidence, VideoLabData, AudioLabData } from "@/types";

interface Props {
  evidence: Evidence | null;
}

export default function VideoAudioLab({ evidence }: Props) {
  const [videoData, setVideoData] = useState<VideoLabData | null>(null);
  const [audioData, setAudioData] = useState<AudioLabData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTimestamp, setSelectedTimestamp] = useState<number | null>(null);

  useEffect(() => {
    if (!evidence) return;
    setLoading(true);

    if (evidence.media_type === "VIDEO") {
      Promise.allSettled([api.getVideoLab(evidence.id), api.getAudioLab(evidence.id)]).then(
        ([vRes, aRes]) => {
          if (vRes.status === "fulfilled") setVideoData(vRes.value);
          if (aRes.status === "fulfilled") setAudioData(aRes.value);
          setLoading(false);
        }
      );
    } else if (evidence.media_type === "AUDIO") {
      api
        .getAudioLab(evidence.id)
        .then((data) => setAudioData(data))
        .finally(() => setLoading(false));
    }
  }, [evidence]);

  if (!evidence) {
    return (
      <div className="p-8 text-center bg-white/70 backdrop-blur-md rounded-2xl border border-pink-100 text-gray-500">
        Please select a Video or Audio evidence item to view temporal and acoustic forensic analysis.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Video Forensics Section (if video) */}
      {evidence.media_type === "VIDEO" && videoData && (
        <div className="space-y-6">
          {/* Quality Scorecard */}
          <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-5 shadow-xs">
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2 mb-3">
              <Film className="w-5 h-5 text-purple-600" />
              Video Quality & Stream Integrity Scorecard
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-4">
              <div className="p-3 bg-purple-50/50 rounded-xl border border-purple-100">
                <span className="text-gray-500">Resolution & FPS</span>
                <div className="text-sm font-bold text-gray-900 mt-1">
                  {videoData.quality_scorecard.resolution} @ {videoData.quality_scorecard.fps} fps
                </div>
              </div>
              <div className="p-3 bg-pink-50/50 rounded-xl border border-pink-100">
                <span className="text-gray-500">Blur & Sharpness</span>
                <div className="text-sm font-bold text-purple-700 mt-1">
                  {videoData.quality_scorecard.blur_assessment} ({videoData.quality_scorecard.blur_score})
                </div>
              </div>
              <div className="p-3 bg-purple-50/50 rounded-xl border border-purple-100">
                <span className="text-gray-500">Motion Intensity</span>
                <div className="text-sm font-bold text-gray-900 mt-1">
                  {videoData.quality_scorecard.motion_intensity}
                </div>
              </div>
              <div className="p-3 bg-pink-50/50 rounded-xl border border-pink-100">
                <span className="text-gray-500">Duplicate Frames</span>
                <div className="text-sm font-bold text-rose-600 mt-1">
                  {videoData.quality_scorecard.duplicate_frames_pct}%
                </div>
              </div>
            </div>

            {videoData.quality_scorecard.quality_warnings.length > 0 && (
              <div className="p-3 bg-amber-50/80 rounded-xl border border-amber-200 text-xs text-amber-800 space-y-1">
                <span className="font-bold flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-600" /> Quality Pre-Inference Warnings:
                </span>
                <ul className="list-disc list-inside space-y-0.5 ml-2">
                  {videoData.quality_scorecard.quality_warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Scene Detection & Temporal Consistency Matrix */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Scene Segmentation */}
            <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-5 shadow-xs">
              <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2 mb-3">
                <Scissors className="w-4 h-4 text-pink-600" />
                Scene Transition & Cut Detection
              </h4>
              <div className="space-y-2 max-h-[260px] overflow-y-auto">
                {videoData.scenes.map((scene) => (
                  <div
                    key={scene.scene_id}
                    className="flex items-center justify-between p-3 bg-purple-50/40 rounded-xl border border-purple-100/80 text-xs"
                  >
                    <div>
                      <span className="font-bold text-purple-900">Scene #{scene.scene_id}</span>
                      <div className="text-gray-500 mt-0.5">
                        {scene.start_time}s → {scene.end_time}s ({scene.duration}s duration)
                      </div>
                    </div>
                    <span className="px-2.5 py-1 rounded-full bg-pink-100 text-pink-800 font-semibold">
                      {(scene.transition_confidence * 100).toFixed(0)}% Conf
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Temporal Consistency Matrix */}
            <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-purple-600" />
                  Temporal Consistency Matrix
                </h4>
                <span className="text-xs font-semibold text-purple-700">
                  Mean: {(videoData.temporal_consistency_matrix.mean_consecutive_consistency * 100).toFixed(1)}%
                </span>
              </div>

              <div className="overflow-x-auto">
                <div className="inline-block min-w-full">
                  <div className="grid grid-cols-10 gap-1 text-[10px] text-center font-mono">
                    {videoData.temporal_consistency_matrix.matrix.slice(0, 10).map((row, rIdx) => (
                      <React.Fragment key={rIdx}>
                        {row.slice(0, 10).map((val, cIdx) => (
                          <div
                            key={cIdx}
                            className={`p-1 rounded font-bold ${
                              val > 0.8
                                ? "bg-emerald-100 text-emerald-800"
                                : val > 0.5
                                ? "bg-amber-100 text-amber-800"
                                : "bg-rose-100 text-rose-800"
                            }`}
                            title={`F${rIdx+1} vs F${cIdx+1}: ${val}`}
                          >
                            {val.toFixed(2)}
                          </div>
                        ))}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              </div>
              <p className="text-[11px] text-gray-500 mt-3 text-center">
                {videoData.temporal_consistency_matrix.interpretation}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Audio Forensics Section */}
      {audioData && (
        <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100 p-5 shadow-xs space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <Volume2 className="w-5 h-5 text-purple-600" />
              Audio Forensics & Acoustic Signal Laboratory
            </h3>
            <span className="text-xs text-gray-500">
              Sample Rate: {audioData.sample_rate} Hz | Duration: {audioData.duration}s
            </span>
          </div>

          {/* Waveform Envelope Visualization */}
          <div>
            <div className="text-xs font-bold text-gray-700 mb-2">Waveform Amplitude Envelope</div>
            <div className="h-20 bg-gradient-to-r from-purple-50 via-pink-50 to-purple-50 rounded-xl border border-pink-100 p-2 flex items-center gap-0.5 overflow-hidden">
              {audioData.waveform.map((amp, idx) => {
                const heightPct = Math.max(8, Math.min(100, amp * 100));
                return (
                  <div
                    key={idx}
                    className="flex-1 bg-gradient-to-t from-purple-600 to-pink-500 rounded-full hover:bg-rose-500 transition-all cursor-pointer"
                    style={{ height: `${heightPct}%` }}
                    title={`Amplitude: ${amp}`}
                  />
                );
              })}
            </div>
          </div>

          {/* Splice Anomaly Detections */}
          {audioData.splices_detected.length > 0 ? (
            <div className="p-4 bg-rose-50/70 rounded-xl border border-rose-200 text-xs">
              <span className="font-bold text-rose-800 flex items-center gap-1.5 mb-2">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                Detected Audio Splices / Discontinuities ({audioData.splices_detected.length}):
              </span>
              <div className="space-y-1.5">
                {audioData.splices_detected.map((s, idx) => (
                  <div key={idx} className="flex justify-between items-center text-rose-900">
                    <span>
                      At <strong>{s.timestamp}s</strong>: {s.description}
                    </span>
                    <span className="font-semibold bg-rose-200/80 px-2 py-0.5 rounded text-[11px]">
                      {(s.confidence * 100).toFixed(0)}% Conf
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-600" />
              Continuous acoustic energy stream verified. No sudden noise floor or energy splices detected.
            </div>
          )}

          {/* 3-Second Segment Windows */}
          <div>
            <div className="text-xs font-bold text-gray-700 mb-2">Segment Window Forensic Breakdown</div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {audioData.segments.map((seg) => (
                <div
                  key={seg.segment_index}
                  className={`p-3 rounded-xl border text-xs ${
                    seg.anomaly_flag
                      ? "bg-rose-50/70 border-rose-200 text-rose-900"
                      : "bg-purple-50/40 border-purple-100/80 text-purple-900"
                  }`}
                >
                  <div className="flex justify-between font-bold">
                    <span>Segment #{seg.segment_index}</span>
                    <span>{seg.interval}</span>
                  </div>
                  <div className="mt-2 space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-gray-500">RMS Energy:</span>
                      <span className="font-semibold">{seg.energy_rms}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Spectral Flatness:</span>
                      <span className="font-semibold">{seg.spectral_flatness}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
