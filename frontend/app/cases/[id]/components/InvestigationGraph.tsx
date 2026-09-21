"use client";

import React, { useState } from "react";
import { Network, Shield, Eye, FileText, UserCheck, CheckCircle2 } from "lucide-react";
import { InvestigationGraph, GraphNode } from "@/types";

interface Props {
  graphData: InvestigationGraph | null;
  loading?: boolean;
}

export default function InvestigationGraphViewer({ graphData, loading }: Props) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  if (loading || !graphData) {
    return (
      <div className="flex items-center justify-center p-12 bg-white/70 backdrop-blur-md rounded-2xl border border-pink-100 shadow-sm min-h-[350px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm font-medium text-purple-900">Synthesizing investigation graph...</span>
        </div>
      </div>
    );
  }

  const { nodes, edges } = graphData;

  const getNodeColor = (type: string) => {
    switch (type) {
      case "CASE":
        return "bg-gradient-to-br from-purple-600 to-indigo-600 text-white border-purple-700 shadow-purple-200";
      case "EVIDENCE":
        return "bg-gradient-to-br from-pink-500 to-rose-500 text-white border-pink-600 shadow-pink-200";
      case "SUBJECT":
        return "bg-gradient-to-br from-amber-500 to-orange-500 text-white border-amber-600 shadow-amber-200";
      case "REPORT":
        return "bg-gradient-to-br from-emerald-500 to-teal-600 text-white border-emerald-600 shadow-emerald-200";
      default:
        return "bg-purple-100 text-purple-900 border-purple-300";
    }
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case "CASE":
        return <Shield className="w-4 h-4" />;
      case "EVIDENCE":
        return <Eye className="w-4 h-4" />;
      case "SUBJECT":
        return <UserCheck className="w-4 h-4" />;
      case "REPORT":
        return <FileText className="w-4 h-4" />;
      default:
        return <Network className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-pink-100/80 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-pink-50">
        <div>
          <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Network className="w-5 h-5 text-purple-600" />
            Interactive Investigation Case Graph
          </h3>
          <p className="text-xs text-gray-700 mt-0.5">
            Cryptographically linked database entities (Case, Evidence, Subjects, Reports, and Provenance)
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold">
          <span className="px-2.5 py-1 rounded-full bg-purple-100 text-purple-800">Nodes: {nodes.length}</span>
          <span className="px-2.5 py-1 rounded-full bg-pink-100 text-pink-800">Edges: {edges.length}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Visual Graph Canvas / Nodes Container */}
        <div className="lg:col-span-2 min-h-[380px] bg-gradient-to-b from-purple-50/40 via-pink-50/30 to-purple-50/20 rounded-xl p-6 border border-pink-100 flex flex-col justify-center relative overflow-hidden">
          {/* Subtle Grid pattern */}
          <div className="absolute inset-0 bg-[radial-gradient(#d8b4e2_1px,transparent_1px)] [background-size:16px_16px] opacity-40 pointer-events-none" />

          {/* Connected Tree / Clusters */}
          <div className="relative z-10 flex flex-col items-center gap-8">
            {/* Level 1: Root Case */}
            <div className="flex justify-center">
              {nodes.filter((n) => n.type === "CASE").map((node) => (
                <button
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`px-5 py-2.5 rounded-xl border font-bold text-sm flex items-center gap-2 shadow-md transition-all duration-200 hover:scale-105 active:scale-95 ${getNodeColor(node.type)} ${
                    selectedNode?.id === node.id ? "ring-4 ring-purple-300" : ""
                  }`}
                >
                  {getNodeIcon(node.type)}
                  {node.label}
                </button>
              ))}
            </div>

            {/* Connecting line */}
            <div className="w-0.5 h-6 bg-purple-200 -my-4" />

            {/* Level 2: Evidence & Subjects */}
            <div className="flex flex-wrap justify-center gap-4">
              {nodes.filter((n) => n.type !== "CASE").map((node) => (
                <button
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`px-4 py-2 rounded-lg border font-semibold text-xs flex items-center gap-1.5 shadow-sm transition-all duration-200 hover:scale-105 active:scale-95 ${getNodeColor(node.type)} ${
                    selectedNode?.id === node.id ? "ring-4 ring-pink-300" : ""
                  }`}
                >
                  {getNodeIcon(node.type)}
                  {node.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Node Inspection Panel */}
        <div className="bg-gradient-to-br from-pink-50/60 to-purple-50/50 rounded-xl p-5 border border-pink-100 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 className="w-4 h-4 text-purple-600" />
              <h4 className="text-sm font-bold text-gray-900">Entity Details Inspector</h4>
            </div>

            {selectedNode ? (
              <div className="space-y-3">
                <div className="p-3 bg-white/90 rounded-lg border border-pink-100 shadow-2xs">
                  <div className="text-xs text-gray-700 uppercase font-semibold">Entity Label</div>
                  <div className="text-sm font-bold text-gray-900 mt-0.5">{selectedNode.label}</div>
                  <div className="text-xs text-purple-600 font-medium mt-1">Type: {selectedNode.type}</div>
                </div>

                {selectedNode.details && (
                  <div className="p-3 bg-white/90 rounded-lg border border-pink-100 shadow-2xs space-y-1.5">
                    <div className="text-xs text-gray-700 uppercase font-semibold">Metadata Attributes</div>
                    {Object.entries(selectedNode.details).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-xs py-0.5 border-b border-pink-50/80">
                        <span className="text-gray-700 capitalize">{k.replace("_", " ")}:</span>
                        <span className="font-semibold text-gray-800 text-right truncate max-w-[140px]">
                          {String(v)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-600 text-xs">
                Click any node in the graph to inspect its cryptographic attributes, linked findings, and chain-of-custody edges.
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-pink-100/80 text-[11px] text-gray-700 flex justify-between">
            <span>Graph Version: 2.0-Verified</span>
            <span>Real DB Schema</span>
          </div>
        </div>
      </div>
    </div>
  );
}
