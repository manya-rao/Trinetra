"""
In-memory and cached passport storage for Trinetra.
Supports TTL expiration and retrieval by passport ID.
"""

import time
from typing import Dict, Optional, Any
from app.schemas import PassportResponse

# In-memory dictionary for active passports with expiration timestamps
_STORE: Dict[str, Dict[str, Any]] = {}
DEFAULT_TTL_SECONDS = 3600  # 1 hour TTL for demo/hackathon uploads


def save_passport(passport: PassportResponse, ttl: int = DEFAULT_TTL_SECONDS) -> None:
    _STORE[passport.id] = {
        "data": passport,
        "expires_at": time.time() + ttl
    }


def get_passport(passport_id: str) -> Optional[PassportResponse]:
    record = _STORE.get(passport_id)
    if not record:
        return None
    if time.time() > record["expires_at"]:
        del _STORE[passport_id]
        return None
    return record["data"]
