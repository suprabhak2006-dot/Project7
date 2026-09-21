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
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    finding_code = Column(String(64), index=True, nullable=False)
    category = Column(Enum(FindingCategory), nullable=False)
    severity = Column(Enum(FindingSeverity), default=FindingSeverity.MEDIUM, nullable=False)
    
    confidence = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    
    timestamp = Column(Float, nullable=True)
    frame_number = Column(Integer, nullable=True)
    bounding_box = Column(JSON, nullable=True)  # [x, y, w, h] or landmarks
    
    model_name = Column(String(128), nullable=False)
    model_version = Column(String(32), nullable=False)
    raw_output = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    analysis = relationship("Analysis", back_populates="findings")
