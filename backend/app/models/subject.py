import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    label = Column(String(128), nullable=False)  # e.g., "Subject #001", "Unknown Person #001"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    case = relationship("Case", back_populates="subjects")
    face_tracks = relationship("FaceTrack", back_populates="subject")
