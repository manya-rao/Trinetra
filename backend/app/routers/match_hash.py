"""
Match hash endpoint for lightweight opt-in lookups.
POST /match_hash {phash} -> {matched, origin_summary|null}
"""

from fastapi import APIRouter
from app.schemas import MatchHashRequest, MatchHashResponse
from app.config import MOCK_MODE

router = APIRouter(tags=["Match Hash"])


@router.post("/match_hash", response_model=MatchHashResponse)
async def match_hash(payload: MatchHashRequest):
    """
    POST /match_hash:
    Opt-in privacy-preserving lookup using perceptual hash.
    Used by browser extension or chat checks without transmitting raw image bytes.
    """
    phash = payload.phash.strip()
    
    # In mock mode, if hash equals dummy known hash or starts with 'demo_', return match
    if MOCK_MODE:
        if phash.startswith("demo_") or phash in ("0000000000000000", "ffffffffffffffff"):
            return MatchHashResponse(
                matched=True,
                origin_summary={
                    "source": "Trinetra Curated Index (DEMO DATA)",
                    "date": "2021-08-15",
                    "factcheck_url": "https://commons.wikimedia.org/wiki/File:Demo_Monsoon_Flooding_Archive.jpg",
                    "claim_short": "DEMO DATA: Flooding archive photo from August 2021"
                }
            )
        return MatchHashResponse(matched=False, origin_summary=None)

    # Real origin index matching will query SQLite index in milestone B2
    return MatchHashResponse(matched=False, origin_summary=None)
