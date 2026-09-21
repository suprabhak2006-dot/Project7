export type UserRole = "ADMIN" | "INVESTIGATOR" | "ANALYST" | "VIEWER";

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export type CaseStatus = "OPEN" | "IN_PROGRESS" | "UNDER_REVIEW" | "CLOSED" | "ARCHIVED";
export type CasePriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

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

export interface Finding {
  id: number;
  analysis_id: number;
  finding_code: string;
  category: string;
  severity: "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  score: number;
  description: string;
  timestamp: number | null;
  frame_number: number | null;
  bounding_box: any;
  model_name: string;
  model_version: string;
  created_at: string;
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
