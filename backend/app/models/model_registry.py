import enum
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Boolean
from backend.app.db.session import Base

class ModelTask(str, enum.Enum):
    IMAGE_DEEPFAKE = "IMAGE_DEEPFAKE"
    FACE_DETECTION = "FACE_DETECTION"
    VIDEO_TEMPORAL = "VIDEO_TEMPORAL"
    AUDIO_DEEPFAKE = "AUDIO_DEEPFAKE"
    AUDIO_SIGNAL = "AUDIO_SIGNAL"
    AV_SYNC = "AV_SYNC"

class ModelFramework(str, enum.Enum):
    PYTORCH = "PYTORCH"
    ONNX = "ONNX"
    OPENCV = "OPENCV"
    SCIPY = "SCIPY"
    FFMPEG = "FFMPEG"

class ModelStatus(str, enum.Enum):
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"

class ModelRegistryEntry(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, index=True, nullable=False)
    version = Column(String(32), nullable=False)
    task = Column(Enum(ModelTask), nullable=False)
    framework = Column(Enum(ModelFramework), nullable=False)
    checkpoint_path = Column(String(512), nullable=True)
    source = Column(String(255), nullable=True)
    license = Column(String(64), nullable=True)
    status = Column(Enum(ModelStatus), default=ModelStatus.READY, nullable=False)
    device = Column(String(32), default="CPU", nullable=False)
    checkpoint_verified = Column(Boolean, default=False, nullable=False)
    input_format = Column(String(128), nullable=True)
    output_format = Column(String(128), nullable=True)
    limitations = Column(Text, nullable=True)
    last_health_check = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
