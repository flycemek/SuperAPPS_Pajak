"""
API Routes
Mendefinisikan endpoint HTTP dasar untuk microservice OCR
"""
from fastapi import APIRouter
from app.core.config import settings
import logging
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/")
async def root():
    """
    Endpoint root untuk health check
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def health_check():
    """
    Endpoint health check untuk monitoring
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "timestamp": datetime.now().isoformat()
    }
