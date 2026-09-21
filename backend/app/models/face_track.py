import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class FaceTrack(Base):
    __tablename__ = "face_tracks"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True, index=True)
    
    track_id_code = Column(String(64), nullable=False, index=True)  # e.g., "Track #07"
    start_time = Column(Float, nullable=False, default=0.0)
    end_time = Column(Float, nullable=False, default=0.0)
    frames_count = Column(Integer, nullable=False, default=1)
    
    bounding_boxes = Column(JSON, nullable=False)  # list of {time, frame_idx, bbox, landmarks, score}
    avg_confidence = Column(Float, nullable=False, default=0.9)
    representative_frame_path = Column(String(512), nullable=True)
    
    # Forensic consistency scores
    geometry_stability = Column(String(32), nullable=False, default="Stable")  # Stable, Slight jitter, Anomalous
    texture_consistency = Column(String(32), nullable=False, default="Consistent")  # Consistent, Anomalous
    lighting_consistency = Column(String(32), nullable=False, default="Consistent")  # Consistent, Inconsistent
    boundary_anomaly_score = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    embedding_vector = Column(JSON, nullable=True)  # normalized face descriptor vector
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    evidence = relationship("Evidence", back_populates="face_tracks")
    subject = relationship("Subject", back_populates="face_tracks")
