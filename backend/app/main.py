import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.db.init_db import init_db
from backend.app.services.model_registry import registry

from backend.app.api.auth import router as auth_router
from backend.app.api.cases import router as cases_router
from backend.app.api.evidence import router as evidence_router
from backend.app.api.analysis import router as analysis_router
from backend.app.api.findings import router as findings_router
from backend.app.api.timeline import router as timeline_router
from backend.app.api.models import router as models_router
from backend.app.api.reports import router as reports_router
from backend.app.api.audit import router as audit_router
from backend.app.api.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB & Seed registry
    print("[*] Starting DeepTrace AI Backend...")
    await init_db()
    # Initialize Model Registry
    registry.initialize()
    yield
    print("[*] Shutting down DeepTrace AI Backend...")

app = FastAPI(
    title="DeepTrace AI",
    description=(
        "AI-Powered Multimodal Deepfake Detection & Digital Forensic Investigation Platform API. "
        "Strictly operates on genuine AI inference, scientific forensic algorithms, and cryptographic integrity."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount storage directory for authenticated artifact previews (heatmaps, face crops)
os.makedirs(settings.STORAGE_PATH, exist_ok=True)
app.mount("/static/storage", StaticFiles(directory=settings.STORAGE_PATH), name="storage")

# Include API Routers
from backend.app.api.workspace import router as workspace_router
from backend.app.api.lab import router as lab_router
from backend.app.api.system import router as system_router

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(cases_router, prefix=settings.API_V1_STR)
app.include_router(evidence_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(findings_router, prefix=settings.API_V1_STR)
app.include_router(timeline_router, prefix=settings.API_V1_STR)
app.include_router(models_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(workspace_router, prefix=settings.API_V1_STR)
app.include_router(lab_router, prefix=settings.API_V1_STR)
app.include_router(system_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "service": "DeepTrace AI Backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
