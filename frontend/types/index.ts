export type UserRole = "ADMIN" | "INVESTIGATOR" | "ANALYST" | "VIEWER";

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export type CaseStatus =
  | "OPEN"
  | "UNDER_INVESTIGATION"
  | "ANALYSIS_IN_PROGRESS"
  | "REVIEW_REQUIRED"
  | "COMPLETED"
  | "ARCHIVED";

export type CasePriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT" | "CRITICAL";

export interface Case {
  id: number;
  case_number: string;
  title: string;
  description: string | null;
  status: CaseStatus;
  priority: CasePriority;
  created_by: number;
  created_at: string;
  updated_at: string;
  evidence_count?: number;
}

export type MediaType = "IMAGE" | "VIDEO" | "AUDIO";

export interface Evidence {
  id: number;
  case_id: number;
  evidence_number: string;
  filename: string;
  mime_type: string;
  media_type: MediaType;
  file_size: number;
  sha256: string;
  storage_path?: string;
  duration: number | null;
  width: number | null;
  height: number | null;
  fps: number | null;
  codec: string | null;
  metadata_json: Record<string, any> | null;
  uploaded_by: number;
  uploaded_at: string;
}

export type AnalysisStatus = "QUEUED" | "PROCESSING" | "COMPLETED" | "PARTIAL" | "FAILED";
export type AnalysisAssessment =
  | "LOW_MANIPULATION_LIKELIHOOD"
  | "MODERATE_MANIPULATION_LIKELIHOOD"
  | "HIGH_MANIPULATION_LIKELIHOOD"
  | "INCONCLUSIVE"
  | "EVIDENCE_CONFLICT";

export interface Analysis {
  id: number;
  evidence_id: number;
  status: AnalysisStatus;
  started_at: string | null;
  completed_at: string | null;
  processing_time: number | null;
  inference_device: string;
  pipeline_version: string;
  final_score: number | null;
  confidence: number | null;
  assessment: AnalysisAssessment | null;
  evidence_conflict: boolean;
  conflict_details: string | null;
  limitations: string | null;
  fusion_details: Record<string, any> | null;
  timeline_data: Array<{
    timestamp: number;
    frame: number;
    score: number;
    confidence: number;
    track_id: number;
    is_spike: boolean;
    face_crop?: string;
  }> | null;
  av_sync_data: Record<string, any> | null;
  signal_data: Record<string, any> | null;
}

export type FindingSeverity = "INFO" | "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
export type ReviewStatus = "PENDING" | "CONFIRMED" | "DISPUTED" | "NEEDS_REVIEW";

export interface Finding {
  id: number;
  analysis_id: number;
  finding_code: string;
  category: string;
  severity: FindingSeverity;
  confidence: number;
  score: number;
  description: string;
  timestamp: number | null;
  frame_number: number | null;
  bounding_box: any;
  model_name: string;
  model_version: string;
  review_status?: ReviewStatus;
  reviewer_id?: number | null;
  reviewer_notes?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface Subject {
  id: number;
  label: string;
  notes: string | null;
  created_at: string;
}

export interface FaceTrack {
  id: number;
  evidence_id: number;
  subject_id: number | null;
  track_id_code: string;
  start_time: number;
  end_time: number;
  frames_count: number;
  avg_confidence: number;
  representative_frame_path: string | null;
  geometry_stability: string;
  texture_consistency: string;
  boundary_anomaly_score: number;
}

export interface Annotation {
  id: number;
  evidence_id: number | null;
  type: "NOTE" | "BOOKMARK" | "HIGHLIGHT";
  timestamp: number | null;
  region_coords: any;
  content: string;
  tags: string | null;
  created_at: string;
}

export interface CaseEvent {
  id: number;
  evidence_id: number | null;
  event_type: string;
  timestamp_in_media: number | null;
  wall_clock_time: string;
  title: string;
  description: string | null;
  severity: string;
}

export interface CaseWorkspace {
  case: Case;
  evidence_count: number;
  subjects: Subject[];
  face_tracks: FaceTrack[];
  annotations: Annotation[];
  events: CaseEvent[];
  reports_count: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "CASE" | "EVIDENCE" | "SUBJECT" | "REPORT";
  details?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
}

export interface InvestigationGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ProvenanceAnalysis {
  original_capture_indicators: string[];
  editing_indicators: string[];
  reencoding_indicators: string[];
  pii_warnings: string[];
  provenance_confidence: string;
  provenance_score: number;
  assessment_summary: string;
  container_metadata: Record<string, any>;
  disclaimer: string;
}

export interface PixelInspection {
  coordinates: { x: number; y: number };
  rgb: { r: number; g: number; b: number };
  hex: string;
  luminance: number;
  local_window: { width: number; height: number };
  local_mean: number;
  local_std_dev: number;
  local_noise_residual: number;
  local_edge_magnitude: number;
  local_anomaly_indicator: number;
}

export interface ImageHistograms {
  red: number[];
  green: number[];
  blue: number[];
  luminance: number[];
  face_vs_background?: {
    face_luma_hist: number[];
    bg_luma_hist: number[];
    correlation: number;
    chi_square_divergence: number;
    bhattacharyya_distance: number;
    anomaly_score: number;
    interpretation: string;
  } | null;
}

export interface CompressionForensics {
  quantization_tables_present?: boolean;
  quantization_tables?: Record<string, number[]>;
  blockiness_ratio?: number;
  double_compression_detected?: boolean;
  anomaly_score?: number;
  methodology?: string;
}

export interface ColorLightingAnalysis {
  lighting_analysis: {
    face_gradient_angle_deg?: number;
    background_gradient_angle_deg?: number;
    illumination_angle_disparity_deg?: number;
    anomaly_score: number;
    confidence: number;
    methodology: string;
  };
  color_analysis: {
    global_color_temperature_k: number;
    white_balance_balance_score: number;
    face_chroma_delta?: number;
    skin_tone_congruence?: string;
    color_anomaly_score?: number;
    interpretation?: string;
  };
}

export interface VideoLabData {
  quality_scorecard: {
    resolution: string;
    fps: number;
    duration_sec: number;
    blur_score: number;
    blur_assessment: string;
    motion_intensity: number;
    duplicate_frames_pct: number;
    quality_warnings: string[];
  };
  scenes: Array<{
    scene_id: number;
    start_time: number;
    end_time: number;
    duration: number;
    transition_confidence: number;
  }>;
  temporal_consistency_matrix: {
    matrix: number[][];
    labels: string[];
    mean_consecutive_consistency: number;
    interpretation: string;
  };
}

export interface AudioLabData {
  duration: number;
  sample_rate: number;
  waveform: number[];
  energy_curve: Array<{ time: number; energy: number }>;
  pitch_contour: Array<{ time: number; pitch_hz: number }>;
  splices_detected: Array<{
    timestamp: number;
    confidence: number;
    type: string;
    description: string;
  }>;
  segments: Array<{
    segment_index: number;
    interval: string;
    start_time: number;
    end_time: number;
    energy_rms: number;
    spectral_flatness: number;
    anomaly_flag: boolean;
  }>;
}

export interface EvidenceComparisonResult {
  evidence_1: {
    id: number;
    evidence_number: string;
    filename: string;
    media_type: string;
    file_size: number;
    sha256: string;
    resolution: string | null;
    uploaded_at: string;
  };
  evidence_2: {
    id: number;
    evidence_number: string;
    filename: string;
    media_type: string;
    file_size: number;
    sha256: string;
    resolution: string | null;
    uploaded_at: string;
  };
  cryptographic_equality: "MATCH" | "DIFFERENT";
  sha256_match: boolean;
  visual_similarity: Record<string, any>;
  is_potential_duplicate: boolean;
  disclaimer: string;
}

export interface SystemHealth {
  status: string;
  api_version: string;
  hardware: {
    cpu_usage_percent: number;
    ram_total_gb: number;
    ram_used_gb: number;
    ram_usage_percent: number;
    disk_storage_free_gb: number;
    disk_storage_total_gb: number;
    gpu: {
      available: boolean;
      device_name: string;
      vram_total_gb: number;
      vram_used_gb: number;
    };
  };
  services: {
    database: string;
    storage: string;
    opencv_yunet: string;
    huggingface_vit: string;
  };
  registered_models_count: number;
  models: Array<{
    name: string;
    version: string;
    task: string;
    status: string;
    device: string;
  }>;
}

export interface ModelStatusEntry {
  name: string;
  version: string;
  task: string;
  framework: string;
  loaded: boolean;
  checkpoint_verified: boolean;
  device: string;
  status: "READY" | "UNAVAILABLE" | "ERROR";
  limitations: string;
  last_health_check: string;
}

export interface Report {
  id: number;
  case_id: number;
  analysis_id: number;
  report_number: string;
  report_sha256: string;
  generated_by: number;
  generated_at: string;
}

export interface AuditLog {
  id: number;
  case_id: number | null;
  user_id: number | null;
  action: string;
  ip_address: string | null;
  details: Record<string, any> | null;
  timestamp: string;
}

export interface DashboardStats {
  cards: {
    active_cases: number;
    total_cases: number;
    total_evidence: number;
    completed_analyses: number;
    processing_jobs: number;
    high_findings: number;
    total_reports: number;
  };
  media_types: Record<string, number>;
  findings_by_category: Record<string, number>;
  outcomes: Record<string, number>;
  recent_cases: Array<{
    id: number;
    case_number: string;
    title: string;
    status: CaseStatus;
    priority: CasePriority;
    created_at: string;
  }>;
}
