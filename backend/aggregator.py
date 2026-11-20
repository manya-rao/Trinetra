import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Load strings (fallback if not present)
def _load_strings() -> Dict[str, Any]:
    from backend.app import config as cfg
    try:
        with open(cfg.SHARED_STRINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        with open(cfg.FALLBACK_STRINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

STRINGS = _load_strings()

# Reason keys as defined in the brief (must match the brief list)
REASON_KEYS = [
    "origin_match_exact",
    "origin_match_near",
    "diff_detected",
    "c2pa_valid",
    "c2pa_invalid",
    "ai_band_likely",
    "ai_band_inconclusive",
    "gate_triggered",
    "out_of_context",
]

def _reason_entry(key: str) -> Dict[str, str]:
    # Pull English/Hindi from strings or use placeholder
    entry = STRINGS.get("reasons", {}).get(key, {})
    return {
        "key": key,
        "en": entry.get("en", f"{key} (en placeholder)"),
        "hi": entry.get("hi", f"{key} (hi placeholder)"),
    }

def aggregate(
    *,
    phash_match: Optional[Dict[str, Any]],
    diff_result: Optional[Dict[str, Any]],
    c2pa: Optional[Dict[str, Any]],
    ml_output: Optional[Dict[str, Any]],
    claim_text: Optional[str] = None,
    consent_external: bool = False,
    demo_data: bool = False,
) -> Dict[str, Any]:
    """Apply the ladder aggregation rules to produce a Passport JSON dict.

    Parameters
    ----------
    phash_match: dict from origin_match (or None)
    diff_result: dict from diff.py (or None)
    c2pa: dict from c2pa_check (or None)
    ml_output: dict from ml.predict (or None)
    claim_text: optional claim string supplied by the user
    consent_external: whether the user consented to external Lens/Tineye links
    demo_data: flag indicating we are in demo mode (adds demo_data=True)
    """
    default_c2pa = {
        "status": "none",
        "issuer": None,
        "ai_generated": False,
        "history": []
    }
    active_c2pa = c2pa if c2pa else default_c2pa

    # Base passport skeleton
    passport: Dict[str, Any] = {
        "id": "",  # filled by caller
        "verdict": "inconclusive",
        "confidence_band": "low",
        "reasons": [],
        "eyes": {"origin": "none", "change": "n/a", "synthesis": "none"},
        "origin": None,
        "diff": None,
        "c2pa": active_c2pa,
        "suspicious_regions_url": None,
        "scope_note": {"en": "", "hi": ""},
        "external_search": {"lens": "https://lens.google.com/", "tineye": "https://tineye.com/"},
        "lang": {"en": "", "hi": ""},
        "demo_data": demo_data,
    }

    # 1. C2PA check – highest priority
    if active_c2pa and active_c2pa.get("status") == "valid" and active_c2pa.get("ai_generated"):
        passport["verdict"] = "ai_confirmed"
        passport["confidence_band"] = "high"
        passport["eyes"]["origin"] = "none"
        passport["eyes"]["change"] = "n/a"
        passport["eyes"]["synthesis"] = "confirmed"
        passport["c2pa"] = active_c2pa
        passport["reasons"].append(_reason_entry("c2pa_valid"))
        _set_verdict_lang(passport)
        return passport

    # 2. Origin match (phash_match)
    if phash_match:
        passport["origin"] = {
            "source": phash_match.get("source", ""),
            "date": phash_match.get("date", ""),
            "factcheck_url": phash_match.get("factcheck_url", ""),
            "claim_en": phash_match.get("claim_en", ""),
            "claim_hi": phash_match.get("claim_hi", ""),
            "thumb_url": phash_match.get("thumb_url", ""),
        }
        passport["eyes"]["origin"] = "found"
        passport["eyes"]["synthesis"] = "none"
        passport["confidence_band"] = "high"
        passport["reasons"].append(_reason_entry("origin_match_exact"))

        # 2a. Diff information
        if diff_result and diff_result.get("changed_regions"):
            passport["diff"] = {
                "heatmap_url": diff_result.get("heatmap_url") or diff_result.get("heatmap_path") or "",
                "aligned_url": diff_result.get("aligned_url") or diff_result.get("aligned_path") or "",
                "changed_regions": diff_result.get("changed_regions"),
            }
            passport["eyes"]["change"] = "found"
            passport["verdict"] = "modified"
            passport["reasons"].append(_reason_entry("diff_detected"))
        else:
            # No structural diff – original / recycled image
            passport["eyes"]["change"] = "none"
            passport["verdict"] = "original"
            passport["reasons"].append(_reason_entry("origin_match_near"))

        # 2b. Out‑of‑context detection (only when claim differs)
        if claim_text and passport["origin"].get("claim_en") and claim_text != passport["origin"]["claim_en"]:
            passport["verdict"] = "out_of_context"
            passport["eyes"]["change"] = "n/a"
            passport["reasons"].append(_reason_entry("out_of_context"))

        _set_verdict_lang(passport)
        return passport

    # 3. No origin match – Normal case: Eye 1 none, Eye 2 n/a, Eye 3 AI lane
    passport["eyes"]["origin"] = "none"
    passport["eyes"]["change"] = "n/a"
    passport["reasons"].append({
        "key": "no_origin_match",
        "en": "No match found in Trinetra fact-check reference index.",
        "hi": "त्रिनेत्र फैक्ट-चेक संदर्भ इंडेक्स में कोई मेल नहीं मिला।"
    })

    if ml_output:
        # gate_triggered forces inconclusive regardless of band
        if ml_output.get("gate_triggered"):
            passport["verdict"] = "inconclusive"
            passport["confidence_band"] = "low"
            passport["eyes"]["synthesis"] = "inconclusive"
            passport["reasons"].append(_reason_entry("gate_triggered"))
            _set_verdict_lang(passport)
            return passport

        band = ml_output.get("band")
        if band == "likely_ai":
            passport["verdict"] = "likely_ai"
            passport["confidence_band"] = ml_output.get("confidence", "medium")
            passport["eyes"]["synthesis"] = "likely"
            passport["reasons"].append(_reason_entry("ai_band_likely"))
        elif band == "likely_real_looking":
            passport["verdict"] = "likely_real_looking"
            passport["confidence_band"] = ml_output.get("confidence", "high")
            passport["eyes"]["synthesis"] = "none"
            passport["reasons"].append(_reason_entry("ai_band_inconclusive"))
        else:  # "inconclusive"
            passport["verdict"] = "inconclusive"
            passport["confidence_band"] = "low"
            passport["eyes"]["synthesis"] = "inconclusive"
            passport["reasons"].append(_reason_entry("ai_band_inconclusive"))

        for rk in ml_output.get("reasons", []):
            if isinstance(rk, str):
                passport["reasons"].append(_reason_entry(rk))
            elif isinstance(rk, dict):
                passport["reasons"].append(rk)

        _set_verdict_lang(passport)
        return passport

    # 4. Fallback – no data
    passport["verdict"] = "inconclusive"
    passport["confidence_band"] = "low"
    passport["eyes"]["synthesis"] = "inconclusive"
    passport["reasons"].append(_reason_entry("ai_band_inconclusive"))
    _set_verdict_lang(passport)
    return passport

def _set_verdict_lang(passport: Dict[str, Any]):
    verdict = passport.get("verdict", "inconclusive")
    entry = STRINGS.get("verdicts", {}).get(verdict, {})
    en_text = entry.get("headline", {}).get("en") or entry.get("detail", {}).get("en") or f"Verdict: {verdict}"
    hi_text = entry.get("headline", {}).get("hi") or entry.get("detail", {}).get("hi") or f"निर्णय: {verdict}"
    passport["lang"] = {"en": en_text, "hi": hi_text}

# Helper for endpoint to fill ID and external links
def finalize_passport(passport: Dict[str, Any], passport_id: str, consent_external: bool) -> Dict[str, Any]:
    passport["id"] = passport_id
    if consent_external:
        passport["external_search"]["lens"] = "https://lens.google.com/uploadbyurl"
        passport["external_search"]["tineye"] = "https://tineye.com/search"
    else:
        passport["external_search"]["lens"] = "https://lens.google.com/"
        passport["external_search"]["tineye"] = "https://tineye.com/"
    # Scope note from strings (fallback if missing)
    scope = STRINGS.get("scope_note", {"en": "Matched against Trinetra index. For a wider web search, tap here.", "hi": "त्रिनेत्र इंडेक्स से मिलान किया गया। व्यापक खोज के लिए यहाँ टैप करें।"})
    passport["scope_note"] = scope
    return passport

