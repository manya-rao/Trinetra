"""
Analyze router for Trinetra.
Provides POST /analyze with mock fixture matching and real pipeline integration.
"""

import json
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from app.config import FIXTURES_DIR, MOCK_MODE
from app.schemas import PassportResponse
from app.storage import save_passport

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analyze"])


def load_fixture(fixture_name: str, new_id: Optional[str] = None) -> PassportResponse:
    fixture_path = FIXTURES_DIR / f"{fixture_name}.json"
    if not fixture_path.exists():
        raise HTTPException(status_code=500, detail=f"Fixture {fixture_name}.json not found at {fixture_path}")
    
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if new_id:
        data["id"] = new_id
    
    return PassportResponse(**data)


@router.post("/analyze", response_model=PassportResponse)
async def analyze_image(
    image: UploadFile = File(..., description="Image file to analyze for provenance"),
    lang: Optional[str] = Form("en"),
    hash_only: Optional[bool] = Form(False),
    consent_external: Optional[bool] = Form(False),
    claim_text: Optional[str] = Form(None)
):
    """
    POST /analyze:
    Multipart upload of image. Returns Provenance Passport JSON.
    When MOCK=1, returns fixture matching keyword in uploaded filename,
    defaulting to inconclusive.
    """
    filename = (image.filename or "").lower()
    passport_id = f"pass_{uuid.uuid4().hex[:12]}"

    if MOCK_MODE:
        logger.info(f"Mock mode active. Analyzing filename '{filename}' (ID: {passport_id})")
        
        if "original" in filename:
            fixture_key = "original"
        elif "modified" in filename or "edited" in filename:
            fixture_key = "modified"
        elif "ai_confirmed" in filename or "confirmed" in filename:
            fixture_key = "ai_confirmed"
        elif "likely_ai" in filename:
            fixture_key = "likely_ai"
        else:
            fixture_key = "inconclusive"

        passport = load_fixture(fixture_key, new_id=passport_id)
        
        # If user didn't consent to external search, remove direct external search queries or set to base
        if not consent_external:
            passport.external_search.lens = "https://lens.google.com/"
            passport.external_search.tineye = "https://tineye.com/"

        # Save passport for subsequent GET /passport/{id} or /p/{id}
        save_passport(passport)
        return passport

    # Real analysis pipeline will be plugged in here in subsequent milestones
    # For now, if MOCK_MODE is disabled before pipeline is ready, fallback to inconclusive
    passport = load_fixture("inconclusive", new_id=passport_id)
    save_passport(passport)
    return passport
