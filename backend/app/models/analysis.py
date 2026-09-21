import enum
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class AnalysisStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"

class AnalysisAssessment(str, enum.Enum):
    LOW_MANIPULATION_LIKELIHOOD = "LOW_MANIPULATION_LIKELIHOOD"
    MODERATE_MANIPULATION_LIKELIHOOD = "MODERATE_MANIPULATION_LIKELIHOOD"
    HIGH_MANIPULATION_LIKELIHOOD = "HIGH_MANIPULATION_LIKELIHOOD"
    INCONCLUSIVE = "INCONCLUSIVE"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.QUEUED, nullable=False)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time = Column(Float, nullable=True)
    inference_device = Column(String(64), default="CPU", nullable=False)
    pipeline_version = Column(String(32), default="1.0.0", nullable=False)
    
    final_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    assessment = Column(Enum(AnalysisAssessment), default=AnalysisAssessment.INCONCLUSIVE, nullable=True)
    
    evidence_conflict = Column(Boolean, default=False, nullable=False)
    conflict_details = Column(Text, nullable=True)
    
    limitations = Column(Text, nullable=True)
    fusion_details = Column(JSON, nullable=True)
    timeline_data = Column(JSON, nullable=True)
    av_sync_data = Column(JSON, nullable=True)
    signal_data = Column(JSON, nullable=True)
    
    evidence = relationship("Evidence", back_populates="analyses")
    findings = relationship("Finding", back_populates="analysis", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="analysis", cascade="all, delete-orphan")
