import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DeepTrace AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "deeptrace-secret-key-328947239487293847239487239847")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./storage/deeptrace.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    STORAGE_PATH: str = os.path.join(BASE_DIR, "storage")
    MODEL_PATH: str = os.path.join(BASE_DIR, "models")
    REPORT_PATH: str = os.path.join(BASE_DIR, "reports")
    
    MAX_UPLOAD_SIZE_MB: int = 500
    ENABLE_GPU: bool = os.getenv("ENABLE_GPU", "true").lower() in ("true", "1")
    
    YUNET_MODEL_PATH: str = os.path.join(MODEL_PATH, "checkpoints", "face_detection_yunet_2023mar.onnx")
    VIT_DEEPFAKE_MODEL_ID: str = "dima806/deepfake_vs_real_image_detection"

    class Config:
        case_sensitive = True

settings = Settings()
