"""
Trinetra: Provenance Passport JSON Schema
Frozen contract between Device A and Device B.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VerdictEnum(str, Enum):
    original = "original"
    modified = "modified"
    out_of_context = "out_of_context"
    ai_confirmed = "ai_confirmed"
    likely_ai = "likely_ai"
    likely_real_looking = "likely_real_looking"
    inconclusive = "inconclusive"


class ConfidenceBandEnum(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    na = "n/a"


class OriginEyeEnum(str, Enum):
    found = "found"
    none = "none"
    inconclusive = "inconclusive"


class ChangeEyeEnum(str, Enum):
    found = "found"
    none = "none"
    na = "n/a"


class SynthesisEyeEnum(str, Enum):
    confirmed = "confirmed"
    likely = "likely"
    none = "none"
    inconclusive = "inconclusive"


class ReasonItem(BaseModel):
    key: str
    en: str
    hi: str


class EyesStatus(BaseModel):
    origin: OriginEyeEnum
    change: ChangeEyeEnum
    synthesis: SynthesisEyeEnum


class OriginDetail(BaseModel):
    source: str
    date: str
    factcheck_url: str
    claim_en: str
    claim_hi: str
    thumb_url: str


class ChangedRegion(BaseModel):
    x: int
    y: int
    w: int
    h: int


class DiffDetail(BaseModel):
    heatmap_url: str
    aligned_url: str
    changed_regions: List[ChangedRegion]


class C2PADetail(BaseModel):
    status: str = Field(..., description="none|valid|invalid")
    issuer: Optional[str] = None
    ai_generated: bool = False
    history: List[Dict[str, Any]] = Field(default_factory=list)


class LocalizedString(BaseModel):
    en: str
    hi: str


class ExternalSearch(BaseModel):
    lens: str
    tineye: str


class PassportResponse(BaseModel):
    id: str
    verdict: VerdictEnum
    confidence_band: ConfidenceBandEnum
    reasons: List[ReasonItem]
    eyes: EyesStatus
    origin: Optional[OriginDetail] = None
    diff: Optional[DiffDetail] = None
    c2pa: C2PADetail
    suspicious_regions_url: Optional[str] = None
    scope_note: LocalizedString
    external_search: ExternalSearch
    lang: LocalizedString
    demo_data: bool = True


class MatchHashRequest(BaseModel):
    phash: str


class MatchHashResponse(BaseModel):
    matched: bool
    origin_summary: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    mock_mode: bool
