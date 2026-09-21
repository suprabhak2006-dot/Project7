# DeepTrace AI - Security Architecture & Threat Model

## 1. Authentication & Access Control (RBAC)

* **Authentication**: Password hashing using `bcrypt` with work factor 12. Stateless JWT access tokens signed with `HS256` and configurable expiration.
* **Role-Based Authorization**:
  * `ADMIN`: Full system administration, user management, audit review, model registry configuration.
  * `INVESTIGATOR`: Case creation, evidence upload, forensic pipeline execution, report generation.
  * `ANALYST`: Forensic data inspection, finding review, timeline visualization.
  * `VIEWER`: Read-only access to authorized cases and finalized PDF reports.
* **Route Protection**: FastAPI dependencies enforce active token verification and role requirements before processing sensitive requests.

---

## 2. File Upload Security & Integrity

Untrusted user uploads represent a critical attack surface in forensic software:
* **Magic Byte & Extension Validation**: Uploads are checked against verified MIME categories (Images, Videos, Audio) and sanitized extensions.
* **Anti-Path-Traversal**: Raw filenames from clients are never used directly as disk paths. Unique UUIDs and sequential identifiers (`EV-XXXXX_UUID_filename`) isolate all stored artifacts.
* **Size Enforcement**: Configurable `MAX_UPLOAD_SIZE_MB` (default 500MB) rejects oversized payloads before exhausting memory or storage.
* **Decompression Safety**: Images and audio are decoded using memory-capped Pillow, OpenCV, and FFmpeg configurations preventing memory exhaustion.

---

## 3. Evidence Privacy & Zero-Exfiltration

Digital evidence may contain sensitive personally identifiable information (PII) or classified investigation material:
* **Local Inference**: All computer vision, temporal, and acoustic models execute locally on the host/worker infrastructure.
* **No External Data Exfiltration**: Evidence files are never dispatched to public third-party APIs.
* **Immutable Audit Trail**: Every access, hash verification, and export action is logged with user ID, IP address, and timestamp in the `audit_logs` database table.

---

## 4. Production Security Hardening

* **Environment Isolation**: Default development credentials are strictly disabled when `ENVIRONMENT=production`.
* **Secret Management**: Production deployments must supply strong, random secrets via `SECRET_KEY` environment variables.
* **CORS & Headers**: Strict CORS origins restrict browser access to verified frontend domains.
