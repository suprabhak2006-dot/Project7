import enum
import datetime
from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class MediaType(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    evidence_number = Column(String(64), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(128), nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    storage_path = Column(String(512), nullable=False)
    
    duration = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    codec = Column(String(64), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    case = relationship("Case", back_populates="evidence")
    uploader = relationship("User", back_populates="evidence_items")
    analyses = relationship("Analysis", back_populates="evidence", cascade="all, delete-orphan")
    face_tracks = relationship("FaceTrack", back_populates="evidence", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="evidence", cascade="all, delete-orphan")
