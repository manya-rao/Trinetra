"""
Strings loader for Trinetra.
Reads shared/strings.json (owned by Device A) if present,
falling back to the local placeholder if shared/strings.json has not been created yet.
"""

import json
import logging
from typing import Dict, Any
from app.config import SHARED_STRINGS_PATH, FALLBACK_STRINGS_PATH

logger = logging.getLogger(__name__)

_cached_strings: Dict[str, Any] = {}


def load_strings() -> Dict[str, Any]:
    global _cached_strings
    if SHARED_STRINGS_PATH.exists():
        try:
            with open(SHARED_STRINGS_PATH, "r", encoding="utf-8") as f:
                _cached_strings = json.load(f)
                return _cached_strings
        except Exception as e:
            logger.warning(f"Failed to read {SHARED_STRINGS_PATH}: {e}. Falling back.")

    if FALLBACK_STRINGS_PATH.exists():
        with open(FALLBACK_STRINGS_PATH, "r", encoding="utf-8") as f:
            _cached_strings = json.load(f)
            return _cached_strings

    return {}


def get_strings() -> Dict[str, Any]:
    if not _cached_strings:
        load_strings()
    return _cached_strings


def get_verdict_strings(verdict_key: str) -> Dict[str, Any]:
    data = get_strings()
    return data.get("verdicts", {}).get(
        verdict_key,
        {
            "headline": {"en": verdict_key, "hi": verdict_key},
            "detail": {"en": "", "hi": ""}
        }
    )


def get_reason_string(reason_key: str) -> Dict[str, str]:
    data = get_strings()
    return data.get("reasons", {}).get(
        reason_key,
        {"en": reason_key, "hi": reason_key}
    )


def get_scope_note() -> Dict[str, str]:
    data = get_strings()
    return data.get(
        "scope_note",
        {
            "en": "Matched against the Trinetra fact-check index. For a wider web search, tap here.",
            "hi": "त्रिनेत्र फैक्ट-चेक इंडेक्स से मिलान किया गया। व्यापक वेब खोज के लिए, यहाँ टैप करें।"
        }
    )
