import enum
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class AnnotationType(str, enum.Enum):
    NOTE = "NOTE"
    BOOKMARK = "BOOKMARK"
    HIGHLIGHT = "HIGHLIGHT"

class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    type = Column(Enum(AnnotationType), default=AnnotationType.NOTE, nullable=False)
    timestamp = Column(Float, nullable=True)  # timestamp in media if applicable
    region_coords = Column(JSON, nullable=True)  # {x, y, width, height} or polygon
    content = Column(Text, nullable=False)
    tags = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    case = relationship("Case", back_populates="annotations")
    evidence = relationship("Evidence", back_populates="annotations")
    user = relationship("User")
