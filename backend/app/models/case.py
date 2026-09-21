import enum
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class CaseStatus(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    ANALYSIS_IN_PROGRESS = "ANALYSIS_IN_PROGRESS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

class CasePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.OPEN, nullable=False)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    creator = relationship("User", back_populates="cases")
    evidence = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="case", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="case", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="case", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="case", cascade="all, delete-orphan")
    events = relationship("CaseEvent", back_populates="case", cascade="all, delete-orphan")
