# DeepTrace AI

> **Detect. Analyze. Explain. Preserve.**

AI-Powered Multimodal Deepfake Detection & Digital Forensic Investigation Platform.

---

## Overview

**DeepTrace AI** is an enterprise-grade digital forensic investigation platform engineered to detect synthetic and manipulated multimedia (images, videos, speech, and audiovisual streams).

Unlike prototype or heuristic demonstration tools, **DeepTrace AI executes genuine deep learning neural architectures and scientific signal forensic algorithms on every uploaded piece of evidence**. The platform operates under an **Absolute No-Mock Policy**: if a model is unloaded or fails, the platform explicitly reports `MODEL UNAVAILABLE` with full technical reasons rather than fabricating a score.

---

## Key Features

* **Real Vision AI Inference**: Vision Transformer (`dima806/deepfake_vs_real_image_detection`) classification combined with OpenCV YuNet ONNX 5-point facial landmark geometry and face alignment.
* **Explainable Forensics**: Gradient-based saliency heatmaps, Error Level Analysis (ELA), 2D Fast Fourier Transform (FFT) azimuthal power-spectrum decay profiling, and directional illumination gradient disparity.
* **Video & Temporal Forensics**: Frame sampling (Fast/Balanced/Deep), multi-face tracking across frames, normalized inter-frame landmark drift measurement, score volatility, and anomaly spike interval identification.
* **Audio Forensics & Synthetic Speech**: Short-Time Fourier Transform (STFT), Mel spectrograms, autocorrelation pitch tracking (f0), spectral flatness, spectral rolloff, and zero-crossing rate. Transparent separation between genuine signal acoustics and AI speech classification.
* **Audio-Visual Synchronization**: Cross-correlation between vertical facial mouth aperture velocity and speech audio energy envelope to calculate synchronization lag and anomalous desynchronized intervals.
* **Evidence Fusion & Conflict Detection**: Calibrated multi-signal aggregation with confidence weighting that automatically flags `EVIDENCE CONFLICT DETECTED` when modalities contradict each other.
* **Cryptographic Evidence Integrity**: Automated SHA-256 calculation at ingestion, immutable byte storage in isolated directories, and on-demand SHA-256 tamper verification.
* **Professional Forensic Reports**: Automated generation of official PDF analysis reports with executive summaries, methodology disclosure, finding codes, and cryptographic PDF SHA-256 integrity hashes.
* **Auditable Model Registry**: Transparent hardware device reporting (CUDA/CPU), model licenses, checkpoint verification status, and documented limitations.

---

## Quick Start

### 1. Prerequisites
* Python 3.10+ (tested on Python 3.11 - 3.14)
* Node.js 18+ & npm
* FFmpeg (auto-resolved via `imageio-ffmpeg` or system binary)

### 2. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Download and verify AI models (YuNet + ViT Deepfake Detector)
python scripts/setup_models.py

# Initialize database and seed initial models
python -m backend.app.db.init_db

# Run automated test suite
python -m pytest backend/tests/ -v

# Run backend API server (port 8000)
uvicorn backend.app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend

# Install UI dependencies
npm install

# Run Next.js development server (port 3000)
npm run dev
```

Visit **http://localhost:3000** in your browser.

---

## Running Verification & Benchmarks

* **End-to-End Investigation Verification**:
  ```bash
  python scripts/verify_e2e.py
  ```
* **Model Evaluation Benchmark**:
  ```bash
  python scripts/evaluate_models.py
  ```

---

## Default Development Credentials
* **Admin**: `admin@deeptrace.ai` / `Admin@DeepTrace2026!`
* **Investigator**: `investigator@deeptrace.ai` / `Investigator@DeepTrace2026!`

---

## Technical Documentation
* [System Architecture](ARCHITECTURE.md)
* [API Reference & Endpoints](API.md)
* [Machine Learning Pipeline](ML_PIPELINE.md)
* [Forensic Methodology](FORENSIC_METHODOLOGY.md)
* [Security & Threat Model](SECURITY.md)
* [Production Deployment](DEPLOYMENT.md)
