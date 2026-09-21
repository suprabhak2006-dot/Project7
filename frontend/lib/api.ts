import {
  User,
  Case,
  Evidence,
  Analysis,
  Finding,
  ModelStatusEntry,
  Report,
  AuditLog,
  DashboardStats
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("deeptrace_token");
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("deeptrace_token", token);
    }
  }

  getToken(): string | null {
    if (!this.token && typeof window !== "undefined") {
      this.token = localStorage.getItem("deeptrace_token");
    }
    return this.token;
  }

  async ensureAuth(): Promise<string> {
    let token = this.getToken();
    if (!token) {
      // Auto-login development admin for immediate usability
      try {
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: "admin@deeptrace.ai",
            password: "Admin@DeepTrace2026!"
          })
        });
        if (res.ok) {
          const data = await res.json();
          this.setToken(data.access_token);
          return data.access_token;
        }
      } catch (err) {
        console.warn("Auto-login error:", err);
      }
    }
    return token || "";
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = await this.ensureAuth();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    if (!res.ok) {
      let errDetail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const data = await res.json();
        if (data.detail) errDetail = data.detail;
      } catch {}
      throw new Error(errDetail);
    }

    return res.json();
  }

  // Auth
  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) throw new Error("Invalid credentials");
    const data = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>("/dashboard/stats");
  }

  // Cases
  async getCases(status?: string): Promise<Case[]> {
    const q = status ? `?status=${status}` : "";
    return this.request<Case[]>(`/cases${q}`);
  }

  async getCase(id: number): Promise<Case> {
    return this.request<Case>(`/cases/${id}`);
  }

  async createCase(data: { title: string; description?: string; priority?: string }): Promise<Case> {
    return this.request<Case>("/cases", {
      method: "POST",
      body: JSON.stringify(data)
    });
  }

  async updateCase(id: number, data: Partial<Case>): Promise<Case> {
    return this.request<Case>(`/cases/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data)
    });
  }

  // Evidence
  async uploadEvidence(caseId: number, file: File): Promise<Evidence> {
    const formData = new FormData();
    formData.append("case_id", String(caseId));
    formData.append("file", file);

    return this.request<Evidence>("/evidence/upload", {
      method: "POST",
      body: formData
    });
  }

  async getEvidence(id: number): Promise<Evidence> {
    return this.request<Evidence>(`/evidence/${id}`);
  }

  async verifyEvidenceIntegrity(id: number): Promise<{
    evidence_id: number;
    evidence_number: string;
    stored_sha256: string;
    recalculated_sha256: string;
    status: string;
    timestamp: string;
  }> {
    return this.request(`/evidence/${id}/verify-integrity`, {
      method: "POST"
    });
  }

  getEvidenceFileUrl(id: number): string {
    return `${API_BASE}/evidence/${id}/file`;
  }

  // Analysis
  async startAnalysis(evidenceId: number): Promise<Analysis> {
    return this.request<Analysis>(`/evidence/${evidenceId}/analyze`, {
      method: "POST"
    });
  }

  async getAnalysis(id: number): Promise<Analysis> {
    return this.request<Analysis>(`/analysis/${id}`);
  }

  // Findings & Timeline
  async getFindings(analysisId: number): Promise<Finding[]> {
    return this.request<Finding[]>(`/findings/${analysisId}`);
  }

  async getTimeline(analysisId: number): Promise<{
    analysis_id: number;
    evidence_id: number;
    timeline: any[];
    av_sync: any;
  }> {
    return this.request(`/timeline/${analysisId}`);
  }

  // Models
  async getModelStatus(): Promise<{ models: ModelStatusEntry[] }> {
    return this.request<{ models: ModelStatusEntry[] }>("/models/status");
  }

  // Reports
  async generateReport(analysisId: number): Promise<Report> {
    return this.request<Report>(`/reports/${analysisId}/generate`, {
      method: "POST"
    });
  }

  async getReport(id: number): Promise<Report> {
    return this.request<Report>(`/reports/${id}`);
  }

  async verifyReport(id: number): Promise<{
    report_id: number;
    report_number: string;
    stored_sha256: string;
    recalculated_sha256: string;
    status: string;
  }> {
    return this.request(`/reports/${id}/verify`, {
      method: "POST"
    });
  }

  getReportDownloadUrl(id: number): string {
    return `${API_BASE}/reports/${id}/download`;
  }

  // Audit Logs
  async getAuditLogs(caseId: number): Promise<AuditLog[]> {
    return this.request<AuditLog[]>(`/audit/${caseId}`);
  }
}

export const api = new ApiClient();
