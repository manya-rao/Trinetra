"""
Reason Generator for Eye 3 (Synthesis Engine)
Translates forensic signals into standardized EN and HI reason dictionaries
strictly adhering to the shared/strings.json contract.
"""
import json
from pathlib import Path
from typing import List, Dict
from ml.config import STRINGS_PATH, VALID_REASONS

_STRINGS_CACHE = None

def load_strings() -> Dict:
    global _STRINGS_CACHE
    if _STRINGS_CACHE is None:
        if not STRINGS_PATH.exists():
            # Fallback path if running from subfolder
            alt_path = Path(__file__).resolve().parent.parent / "shared" / "strings.json"
            if alt_path.exists():
                with open(alt_path, "r", encoding="utf-8") as f:
                    _STRINGS_CACHE = json.load(f)
            else:
                raise FileNotFoundError(f"Strings file not found at {STRINGS_PATH}")
        else:
            with open(STRINGS_PATH, "r", encoding="utf-8") as f:
                _STRINGS_CACHE = json.load(f)
    return _STRINGS_CACHE

def make_reason(key: str) -> Dict[str, str]:
    """Return a single standardized reason dict."""
    if key not in VALID_REASONS:
        raise ValueError(f"Unknown reason key: {key}. Must be one of {VALID_REASONS}")
    strings = load_strings()
    reason_strings = strings.get("reasons", {}).get(key, {})
    return {
        "key": key,
        "en": reason_strings.get("en", "Evidence detected."),
        "hi": reason_strings.get("hi", "संबंधित साक्ष्य प्राप्त हुआ।")
    }

def format_reasons(keys: List[str]) -> List[Dict[str, str]]:
    """Format a list of valid reason keys into localized reason objects."""
    result = []
    seen = set()
    for k in keys:
        if k in VALID_REASONS and k not in seen:
            result.append(make_reason(k))
            seen.add(k)
    return result
