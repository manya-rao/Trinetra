import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Load strings (fallback if not present)
def _load_strings() -> Dict[str, Any]:
    try:
        from app import config as cfg
    except ImportError:
        from backend.app import config as cfg
    try:
        with open(cfg.SHARED_STRINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        try:
            with open(cfg.FALLBACK_STRINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

STRINGS = _load_strings()

# Reason keys as defined in the brief
REASON_KEYS = [
    "origin_match_exact",
    "origin_match_near",
    "diff_detected",
    "no_origin_match",
    "c2pa_valid",
    "c2pa_invalid",
    "ai_band_likely",
    "ai_band_inconclusive",
    "gate_triggered",
    "out_of_context",
    "no_ai_signs_found",
]


def _reason_entry(key: str) -> Dict[str, str]:
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
    input_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Apply the ladder aggregation rules to produce a Passport JSON dict.

    Follows strict Confirmation Ladder:
    - L1 signed C2PA / watermark -> ai_confirmed ("AI-generated (confirmed)")
    - L2 match to real original + reliable diff -> modified ("Modified")
    - L3 fusion signals agree -> likely_ai ("Likely AI")
    - L4 weak / conflicting / unedited original / low-res -> original or inconclusive
    - "likely_real_looking" is NEVER emitted as a verdict; mapped to "inconclusive".
    """
    try:
        from app import config as cfg
    except ImportError:
        from backend.app import config as cfg

    default_c2pa = {
        "status": "none",
        "issuer": None,
        "ai_generated": False,
        "history": []
    }
    active_c2pa = c2pa if c2pa else default_c2pa

    passport: Dict[str, Any] = {
        "id": "",
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

    # 1. C2PA check - highest priority (L1)
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

        # Check if input is very low-res or heavily compressed using unified config thresholds
        min_dim = getattr(cfg, "MIN_IMAGE_DIM", 256)
        heavy_q = getattr(cfg, "HEAVY_COMPRESSION_JPEG_QUALITY", 75.0)
        is_low_quality = False
        if input_meta:
            w = input_meta.get("width", 1000)
            h = input_meta.get("height", 1000)
            jq = input_meta.get("jpeg_quality")
            if min(w, h) < min_dim or (jq is not None and jq <= heavy_q):
                is_low_quality = True
        if ml_output and ml_output.get("gate_triggered"):
            is_low_quality = True

        # Check diff reliability and sane bounds
        diff_reliable = bool(diff_result.get("reliable", True)) if diff_result else True
        raw_regions = diff_result.get("changed_regions", []) if diff_result else []

        sane_regions = []
        for r in raw_regions:
            rw = r.get("w", 0)
            rh = r.get("h", 0)
            if rw >= cfg.DIFF_MIN_REGION_BOUNDS and rh >= cfg.DIFF_MIN_REGION_BOUNDS:
                sane_regions.append(r)

        # Origin match reason: return exactly ONE of origin_match_exact or origin_match_near, never both
        input_phash = input_meta.get("phash", "") if input_meta else ""
        ref_phash = phash_match.get("phash", "")
        if input_phash and ref_phash and input_phash != ref_phash:
            origin_reason_key = "origin_match_near"
        else:
            origin_reason_key = "origin_match_exact"

        if not diff_reliable:
            # Matched + unreliable diff -> "inconclusive" (never falsely accuse as modified)
            passport["verdict"] = "inconclusive"
            passport["confidence_band"] = "low"
            passport["eyes"]["change"] = "inconclusive"
            passport["reasons"].append(_reason_entry(origin_reason_key))
            passport["reasons"].append(_reason_entry("ai_band_inconclusive"))
        elif sane_regions and not is_low_quality:
            # Matched + reliable + significant sane regions -> "modified"
            passport["diff"] = {
                "heatmap_url": diff_result.get("heatmap_url") or diff_result.get("heatmap_path") or "",
                "aligned_url": diff_result.get("aligned_url") or diff_result.get("aligned_path") or "",
                "changed_regions": sane_regions,
            }
            passport["eyes"]["change"] = "found"
            passport["verdict"] = "modified"
            passport["confidence_band"] = "high"
            passport["reasons"].append(_reason_entry(origin_reason_key))
            passport["reasons"].append(_reason_entry("diff_detected"))
        elif sane_regions and is_low_quality:
            # Matched + regions detected but quality is too low to be reliable -> "inconclusive"
            passport["verdict"] = "inconclusive"
            passport["confidence_band"] = "low"
            passport["eyes"]["change"] = "inconclusive"
            passport["reasons"].append(_reason_entry(origin_reason_key))
            passport["reasons"].append(_reason_entry("heavy_compression" if (input_meta and input_meta.get("jpeg_quality") and input_meta.get("jpeg_quality") <= heavy_q) else "low_resolution"))
        else:
            # Matched + reliable + no regions -> "original" (recycled copy shown with origin)
            passport["eyes"]["change"] = "none"
            passport["verdict"] = "original"
            passport["confidence_band"] = "high"
            passport["reasons"].append(_reason_entry(origin_reason_key))

        # 2b. Out-of-context detection (only when claim differs)
        if claim_text and passport["origin"].get("claim_en") and claim_text != passport["origin"]["claim_en"]:
            passport["verdict"] = "out_of_context"
            passport["eyes"]["change"] = "n/a"
            passport["reasons"].append(_reason_entry("out_of_context"))

        _set_verdict_lang(passport)
        return passport

    # 3. No origin match - Normal case: Eye 1 none, Eye 2 n/a, Eye 3 AI lane
    passport["eyes"]["origin"] = "none"
    passport["eyes"]["change"] = "n/a"
    passport["reasons"].append(_reason_entry("no_origin_match"))

    if ml_output:
        # gate_triggered forces inconclusive regardless of band
        if ml_output.get("gate_triggered"):
            passport["verdict"] = "inconclusive"
            passport["confidence_band"] = "low"
            passport["eyes"]["synthesis"] = "inconclusive"
            passport["reasons"].append(_reason_entry("gate_triggered"))
            # Append specific gate rule that fired
            for rk in ml_output.get("reasons", []):
                rk_key = rk.get("key") if isinstance(rk, dict) else rk
                if rk_key in ("low_resolution", "heavy_compression", "signals_disagree", "camera_metadata_present"):
                    passport["reasons"].append(_reason_entry(rk_key))
            _set_verdict_lang(passport)
            return passport

        band = ml_output.get("band")
        if band == "likely_ai":
            passport["verdict"] = "likely_ai"
            passport["confidence_band"] = ml_output.get("confidence", "medium")
            passport["eyes"]["synthesis"] = "likely"
            passport["reasons"].append(_reason_entry("ai_band_likely"))
        elif band == "likely_real_looking":
            # Never emit likely_real_looking as verdict. Map to inconclusive with quiet reason text.
            passport["verdict"] = "inconclusive"
            passport["confidence_band"] = "low"
            passport["eyes"]["synthesis"] = "none"
            passport["reasons"].append(_reason_entry("no_ai_signs_found"))
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

    # 4. Fallback - no data
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


def finalize_passport(passport: Dict[str, Any], passport_id: str, consent_external: bool) -> Dict[str, Any]:
    passport["id"] = passport_id
    if consent_external:
        passport["external_search"]["lens"] = "https://lens.google.com/uploadbyurl"
        passport["external_search"]["tineye"] = "https://tineye.com/search"
    else:
        passport["external_search"]["lens"] = "https://lens.google.com/"
        passport["external_search"]["tineye"] = "https://tineye.com/"

    scope_dict = STRINGS.get("scope_note", {})
    if passport.get("origin"):
        # Match found in index
        scope = scope_dict.get("matched", {
            "en": "Matched against the Trinetra index. For a wider web search, tap here.",
            "hi": "त्रिनेत्र इंडेक्स से मिलान किया गया। व्यापक खोज के लिए यहाँ टैप करें。"
        })
    else:
        # Checked against index, no match
        scope = scope_dict.get("checked", {
            "en": "Checked against the Trinetra index. For a wider web search, tap here.",
            "hi": "त्रिनेत्र इंडेक्स में जांच की गई। व्यापक खोज के लिए यहाँ टैप करें।"
        })
    passport["scope_note"] = scope
    return passport
