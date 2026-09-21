from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from backend.app.services.model_registry import registry
from backend.app.models.user import User
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/models", tags=["Models"])

@router.get("/status")
async def get_models_status(current_user: User = Depends(get_current_user)):
    """
    Returns actual health check state, device, and limitations for registered models.
    """
    status_data = registry.get_status()
    return {"models": status_data}
