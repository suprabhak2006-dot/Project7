import enum
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class FindingCategory(str, enum.Enum):
    AI_MODEL = "AI_MODEL"
    FORENSIC_ALGORITHM = "FORENSIC_ALGORITHM"
    METADATA_ANALYSIS = "METADATA_ANALYSIS"
    SIGNAL_ANALYSIS = "SIGNAL_ANALYSIS"
    TEMPORAL_ANALYSIS = "TEMPORAL_ANALYSIS"
    FUSION = "FUSION"

class FindingSeverity(str, enum.Enum):
    INFO = "INFO"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DISPUTED = "DISPUTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    finding_code = Column(String(64), index=True, nullable=False)
    category = Column(Enum(FindingCategory), nullable=False)
    severity = Column(Enum(FindingSeverity), default=FindingSeverity.MODERATE, nullable=False)
    
    # Strictly separated confidence vs score
    confidence = Column(Float, nullable=False)  # Detection confidence (e.g. 0.0 - 1.0)
    score = Column(Float, nullable=False)       # Forensic anomaly score (e.g. 0.0 - 1.0)
    description = Column(Text, nullable=False)
    
    timestamp = Column(Float, nullable=True)
    frame_number = Column(Integer, nullable=True)
    bounding_box = Column(JSON, nullable=True)  # [x, y, w, h] or landmarks
    
    model_name = Column(String(128), nullable=False)
    model_version = Column(String(32), nullable=False)
    raw_output = Column(JSON, nullable=True)
    
    # Investigator Review Workflow (AI provenance is immutable)
    review_status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    analysis = relationship("Analysis", back_populates="findings")
    reviewer = relationship("User")
