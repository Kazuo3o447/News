"""
Health-Check Endpunkt für Azure App Service
"""
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "IT News Hub API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
