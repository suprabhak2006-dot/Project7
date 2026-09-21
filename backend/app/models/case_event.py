import enum
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class EventType(str, enum.Enum):
    EVIDENCE_ACQUIRED = "EVIDENCE_ACQUIRED"
    INTEGRITY_VERIFIED = "INTEGRITY_VERIFIED"
    FACE_DETECTED = "FACE_DETECTED"
    TEMPORAL_ANOMALY = "TEMPORAL_ANOMALY"
    AUDIO_ANOMALY = "AUDIO_ANOMALY"
    AV_SYNC_MISMATCH = "AV_SYNC_MISMATCH"
    HIGH_AI_SCORE = "HIGH_AI_SCORE"
    INVESTIGATOR_NOTE = "INVESTIGATOR_NOTE"
    STATUS_CHANGE = "STATUS_CHANGE"
    REPORT_EXPORTED = "REPORT_EXPORTED"

class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=True, index=True)
    
    event_type = Column(Enum(EventType), nullable=False)
    timestamp_in_media = Column(Float, nullable=True)  # seconds e.g. 01:14
    wall_clock_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(32), default="INFO", nullable=False)  # INFO, LOW, MODERATE, HIGH, CRITICAL
    metadata_json = Column(JSON, nullable=True)

    case = relationship("Case", back_populates="events")
    evidence = relationship("Evidence")
