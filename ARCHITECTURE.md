# DeepTrace AI - System Architecture

## Architecture Diagram

```
                    INVESTIGATOR / ANALYST
                             │
                             ▼
            ┌───────────────────────────────────┐
            │       Next.js 15+ Frontend        │
            │  (Dark Forensic UI / TypeScript)  │
            └─────────────────┬─────────────────┘
                              │ REST / SSE
                              ▼
            ┌───────────────────────────────────┐
            │        FastAPI Backend            │
            │   (Auth, RBAC, Job Manager)       │
            └─────────────────┬─────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
     PostgreSQL/           Redis              Immutable
   Async SQLite        Queue/Broker          File Storage
   (ORM Models)               │             (storage/cases/)
                              ▼                   │
                          Celery                  │
                          Forensic                │
                          Workers                 │
                              │                   │
                              ▼                   │
                     ┌──────────────────┐         │
                     │ Forensic Pipeline│◄────────┘
                     └────────┬─────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
       Image Pipeline   Video Pipeline   Audio Pipeline
       - YuNet Detect   - Sampling       - FFmpeg Extract
       - ViT Inference  - Face Tracking  - STFT Spectrum
       - Saliency Map   - Temporal Drift - Pitch & Flatness
       - JPEG ELA & FFT - AV Sync Correl - Speech Checks
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                     Evidence Fusion Engine
                 (Confidence-Weighted Fusion
                    + Conflict Detection)
                              │
                              ▼
                     Traceable Findings &
                     PDF Report Engine
```

---

## 1. Frontend Layer
* **Framework**: Next.js 16 (App Router), React 19, TypeScript.
* **Styling**: Tailwind CSS v4 with custom forensic design tokens (`#0B0F14` background, `#111820` panel cards, `#FF6B00` forensic amber accent, `#00D1FF` cyan highlight).
* **Components**:
  * Case Workspace with 8 dedicated forensic tabs: Overview, Evidence, Analysis, Timeline, Findings, Chain of Custody, Reports, and Audit Log.
  * Live SSE stream monitor showing verified execution stages.
  * Interactive Recharts visualizations for multi-modal breakdown and temporal score trajectories.
  * Model Registry live state viewer.

---

## 2. Backend & API Layer
* **Framework**: Python FastAPI with asynchronous request handling.
* **Security & Auth**: OAuth2 Password Bearer with JWT tokens and bcrypt password hashing. Role-Based Access Control (`ADMIN`, `INVESTIGATOR`, `ANALYST`, `VIEWER`).
* **Real-Time Updates**: Server-Sent Events (SSE) `/api/analysis/{id}/events` streaming pipeline stage changes directly to client observers.
* **Background Tasks**: Asynchronous background jobs and Celery/Redis worker configuration.

---

## 3. Database Layer
* **ORM**: SQLAlchemy 2.0 Async ORM with Alembic migration compatibility.
* **Dialect Support**: Seamless compatibility with PostgreSQL (`asyncpg`) and SQLite (`aiosqlite`) for zero-configuration local development.
* **Relational Schemas**:
  * `User`: Credentials, names, roles, creation dates.
  * `Case`: Numbering format `CASE-YYYY-XXXX`, priority, status, ownership.
  * `Evidence`: Metadata, cryptographic SHA-256 hash, duration, width, height, fps, codec.
  * `Analysis`: Likelihood, confidence, assessment, conflict details, processing times.
  * `Finding`: Formal finding codes `FND-XXXX`, severity, category, bounding boxes, model provenance.
  * `ModelRegistryEntry`: Name, framework, task, verified status, limitations.
  * `AuditLog`: Immutable action logs with IP addresses and parameter details.
  * `Report`: Official reports with cryptographic report SHA-256 hash.

---

## 4. Storage Architecture
Evidence and generated artifacts reside outside the database in an isolated directory structure:
```
storage/
    cases/
        CASE-YYYY-XXXX/
            original/     <- Immutable original evidence (read-only)
            faces/        <- Extracted and aligned face crops
            frames/       <- Sampled video frame thumbnails
            heatmaps/     <- Gradient-based saliency heatmaps & overlays
            audio/        <- Extracted 16kHz uncompressed WAV audio
            reports/      <- Generated PDF forensic analysis reports
```
Original media bytes are never overwritten, satisfying forensic evidence integrity standards.
