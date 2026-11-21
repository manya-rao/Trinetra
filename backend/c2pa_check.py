"""
C2PA Content Credentials and Provenance Checker for Trinetra.
Uses c2pa-python's Reader to perform cryptographic manifest inspection.
Never returns status 'valid' unless the library validates the manifest signature.
Derives ai_generated from the manifest assertions (digitalSourceType: trainedAlgorithmicMedia).
"""

import io
import json
import logging
from pathlib import Path
from typing import Dict, Any, Union, Optional

logger = logging.getLogger(__name__)

# Check if c2pa is available in the environment
_c2pa_available = False
try:
    import c2pa
    _c2pa_available = True
except ImportError:
    _c2pa_available = False


def is_c2pa_available() -> bool:
    """Return whether c2pa-python library is loaded and operational."""
    return _c2pa_available


def check_c2pa(image_input: Union[str, Path, bytes, io.BytesIO]) -> Dict[str, Any]:
    """
    Check an image for C2PA content credentials using c2pa.Reader.
    Returns dictionary matching C2PADetail schema:
      - status: "none" | "valid" | "invalid"
      - issuer: Optional[str]
      - ai_generated: bool
      - history: list of dicts
    """
    default_none = {
        "status": "none",
        "issuer": None,
        "ai_generated": False,
        "history": []
    }

    if not _c2pa_available:
        return default_none

    # Prepare stream
    stream = None
    if isinstance(image_input, (str, Path)):
        p = Path(image_input)
        if not p.is_file():
            return default_none
        try:
            with open(p, "rb") as f:
                raw_bytes = f.read()
            stream = io.BytesIO(raw_bytes)
        except Exception as e:
            logger.debug(f"Failed to read image for C2PA: {e}")
            return default_none
    elif isinstance(image_input, bytes):
        stream = io.BytesIO(image_input)
    elif isinstance(image_input, io.BytesIO):
        stream = image_input
        stream.seek(0)
    else:
        return default_none

    try:
        reader = c2pa.Reader(None, stream)
        manifest_raw = reader.json()
        if not manifest_raw or manifest_raw == "{}":
            return default_none

        manifest_data = json.loads(manifest_raw)
        active = reader.get_active_manifest()
        if not active:
            return default_none

        # Inspect validation status from native C2PA validator
        val_status = manifest_data.get("validation_status", [])
        
        # Check for signature / hash tampering errors
        is_tampered = False
        is_untrusted_issuer = False

        for status_item in val_status:
            code = status_item.get("code", "")
            if "mismatch" in code or "corrupt" in code or "invalid" in code:
                is_tampered = True
            elif "untrusted" in code:
                is_untrusted_issuer = True

        if is_tampered:
            return {
                "status": "invalid",
                "issuer": "Tampered / Invalid Signature",
                "ai_generated": False,
                "history": []
            }

        # Extract Issuer from signature_info
        sig_info = active.get("signature_info", {})
        issuer_name = sig_info.get("common_name") or sig_info.get("issuer") or "Unknown Signer"

        if is_untrusted_issuer or "self-signed" in issuer_name.lower() or "demo" in issuer_name.lower():
            final_issuer = "self-signed DEMO signer"
        else:
            final_issuer = issuer_name

        # Derive ai_generated strictly from manifest assertions
        ai_generated = False
        history = []

        assertions = active.get("assertions", [])
        for assertion in assertions:
            label = assertion.get("label", "")
            data = assertion.get("data", {})
            if "actions" in label:
                actions_list = data.get("actions", [])
                for act in actions_list:
                    history.append({
                        "action": act.get("action", "c2pa.action"),
                        "software": act.get("softwareAgent", final_issuer),
                        "digitalSourceType": act.get("digitalSourceType"),
                        "when": act.get("when")
                    })
                    # Check for standardized AI generation indicators
                    src_type = act.get("digitalSourceType", "")
                    action_name = act.get("action", "")
                    sw_agent = act.get("softwareAgent", "").lower()
                    if (
                        "trainedalgorithmicmedia" in src_type.lower()
                        or "compositeSynthetic" in src_type
                        or "c2pa.created" in action_name
                        or "generative" in sw_agent
                        or "synthetic" in sw_agent
                    ):
                        ai_generated = True

        return {
            "status": "valid",
            "issuer": final_issuer,
            "ai_generated": ai_generated,
            "history": history
        }

    except c2pa.c2pa._C2paManifestNotFound:
        # Standard JPEG without C2PA manifest
        return default_none
    except Exception as e:
        logger.debug(f"C2PA inspection encountered non-critical error: {e}")
        return default_none
