# DeepTrace AI - REST API Reference

The DeepTrace AI backend exposes a complete RESTful API at `/api`. Interactive OpenAPI Swagger documentation is available at `/docs`.

---

## Authentication Endpoints

### `POST /api/auth/login`
Authenticates user and returns JWT access token.
* **Request**: `{"email": "admin@deeptrace.ai", "password": "Admin@DeepTrace2026!"}`
* **Response**: `{"access_token": "<jwt>", "token_type": "bearer", "user": {...}}`

### `POST /api/auth/register`
Registers a new user (admin / investigator).
* **Request**: `{"name": "...", "email": "...", "password": "...", "role": "INVESTIGATOR"}`

### `GET /api/auth/me`
Returns details of the currently authenticated user.

---

## Case Management Endpoints

### `POST /api/cases`
Initializes a new forensic investigation case.
* **Request**: `{"title": "...", "description": "...", "priority": "HIGH"}`
* **Response**: Case object with generated `case_number` (`CASE-YYYY-XXXX`).

### `GET /api/cases`
Returns a list of cases, with optional filter `?status=OPEN`.

### `GET /api/cases/{id}`
Returns case details and evidence count.

### `PATCH /api/cases/{id}`
Updates case status, title, description, or priority.

---

## Evidence Endpoints

### `POST /api/evidence/upload`
Uploads evidence media to a case (`multipart/form-data`).
* **Parameters**: `case_id` (int), `file` (binary).
* **Process**: Computes SHA-256 hash immediately, saves bytes immutably under `storage/cases/{case_number}/original/`, extracts metadata.
* **Response**: Evidence record with `evidence_number`, `sha256`, dimensions, format.

### `GET /api/evidence/{id}`
Returns metadata and details of an evidence item.

### `POST /api/evidence/{id}/verify-integrity`
Recalculates the cryptographic SHA-256 of the stored original file and verifies against the original ingestion hash.
* **Response**:
  ```json
  {
    "evidence_id": 1,
    "stored_sha256": "53c52cccf...",
    "recalculated_sha256": "53c52cccf...",
    "status": "INTEGRITY_VERIFIED"
  }
  ```

### `GET /api/evidence/{id}/file`
Securely streams the raw evidence file.

---

## Analysis Endpoints

### `POST /api/evidence/{evidence_id}/analyze`
Enqueues forensic pipeline execution in the background.
* **Response**: Initial Analysis object with `status: QUEUED`.

### `GET /api/analysis/{id}`
Returns full analysis results, final score, confidence, assessment, conflict status, and modal observations.

### `GET /api/analysis/{id}/status`
Returns lightweight status check for polling clients.

### `GET /api/analysis/{id}/events`
Server-Sent Events (SSE) streaming real-time stage updates (`VALIDATING`, `METADATA`, `FACE_DETECTION`, `AI_INFERENCE`, `FORENSIC_ANALYSIS`, `TEMPORAL_ANALYSIS`, `AUDIO_ANALYSIS`, `AV_ANALYSIS`, `FUSION`, `FINDINGS`, `COMPLETED`).

---

## Findings & Timeline Endpoints

### `GET /api/findings/{analysis_id}`
Returns list of structured findings (`finding_code`, `category`, `severity`, `score`, `confidence`, `description`, `bounding_box`, `model_name`).

### `GET /api/timeline/{analysis_id}`
Returns temporal score sequence, tracked face crop references, and anomaly spikes for video evidence.

---

## Model Registry Endpoints

### `GET /api/models/status`
Returns real-time health, loaded status, device (CUDA/CPU), checkpoint verification, and limitations of all registered models.

---

## Forensic Report Endpoints

### `POST /api/reports/{analysis_id}/generate`
Compiles and renders an official PDF forensic report, hashes it with SHA-256, and stores it under `reports/`.

### `GET /api/reports/{id}`
Returns report metadata and cryptographic hash.

### `GET /api/reports/{id}/download`
Downloads the official PDF report.

### `POST /api/reports/{id}/verify`
Verifies that the PDF report on disk matches its recorded SHA-256 hash.

---

## Audit Trail & Dashboard

### `GET /api/audit/{case_id}`
Returns the chronological audit log for a case.

### `GET /api/dashboard/stats`
Returns aggregated case counts, media type breakdowns, findings by category, and recent cases.
