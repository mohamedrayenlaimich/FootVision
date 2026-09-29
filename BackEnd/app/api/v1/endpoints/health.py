from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", summary="Health Check")
def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
