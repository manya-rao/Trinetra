"""
Health check endpoint for Trinetra backend.
"""

from fastapi import APIRouter
from app.schemas import HealthResponse
from app.config import MOCK_MODE

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        service="trinetra-backend",
        version="0.1.0",
        mock_mode=MOCK_MODE
    )
