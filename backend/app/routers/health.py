"""
Health check endpoint for Trinetra backend.
"""

from fastapi import APIRouter
from app.schemas import HealthResponse
from app.config import MOCK_MODE

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    ml_avail = False
    try:
        from ml.predict import predict
        ml_avail = True
    except Exception:
        ml_avail = False

    c2pa_avail = False
    try:
        import c2pa
        c2pa_avail = True
    except Exception:
        c2pa_avail = False

    return HealthResponse(
        status="ok",
        service="trinetra-backend",
        version="0.1.0",
        mock_mode=MOCK_MODE,
        ml_available=ml_avail,
        c2pa_available=c2pa_avail,
    )
