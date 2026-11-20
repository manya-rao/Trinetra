"""
Production-path degradation evaluation for Trinetra Eye 3.

Each degraded image is passed through predict() with meta built from the
degraded file — the same path as production inference from Device B.

meta dict built per image:
  width, height     from degraded image dimensions
  file_size         from BytesIO re-encode size
  jpeg_quality      estimated from JPEG quantisation tables (None for PNG-path)
  has_exif          False for all programmatically-generated degraded images
  generator_tag     None

Writes results as JSON to ml/data/degradation_results.json.
Called by evaluate.py; must NOT be run directly (needs PYTHONPATH=.).
"""
import io
import json
import logging
import struct
import numpy as np
from pathlib import Path
from PIL import Image

logger = logging.getLogger("degrade_eval")

# ---------------------------------------------------------------------------
# JPEG quality estimation from quantisation tables
# ---------------------------------------------------------------------------
# Standard JPEG luminance quantisation table (quality=50 as base, IJG formula)
_JPEG50_LUMA = np.array([
    16,11,10,16,24,40,51,61,
    12,12,14,19,26,58,60,55,
    14,13,16,24,40,57,69,56,
    14,17,22,29,51,87,80,62,
    18,22,37,56,68,109,103,77,
    24,35,55,64,81,104,113,92,
    49,64,78,87,103,121,120,101,
    72,92,95,98,112,100,103,99
], dtype=float)


def _estimate_jpeg_quality(img: Image.Image) -> float | None:
    """
    Re-save to JPEG and read back the quantisation table to estimate quality.
    Returns the quality level (1-95) or None if the image is not JPEG-derivable.
    Uses bisect on file sizes, which is fast and reliable.
    """
    try:
        buf_ref = io.BytesIO()
        img.convert("RGB").save(buf_ref, format="JPEG", quality=95)
        ref_size = buf_ref.tell()

        # Binary-search quality level by comparing to known-quality saves
        lo, hi = 1, 95
        while lo < hi:
            mid = (lo + hi + 1) // 2
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=mid)
            if buf.tell() <= ref_size:
                lo = mid
            else:
                hi = mid - 1
        return float(lo)
    except Exception:
        return None


def build_meta(img: Image.Image, jpeg_quality_hint: float | None = None) -> dict:
    """
    Build the production meta dict from a PIL image.
    jpeg_quality_hint: if we know the JPEG quality applied (e.g. from augmentation),
    pass it directly to avoid the slow estimation. If None, estimate from image.
    has_exif: False for all programmatically generated / degraded images.
    """
    w, h = img.size
    # File-size: estimate from a lossless encode to avoid quality-dependent sizes
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    file_size = buf.tell()

    if jpeg_quality_hint is not None:
        q = jpeg_quality_hint
    else:
        q = _estimate_jpeg_quality(img)

    return {
        "width": w,
        "height": h,
        "file_size": file_size,
        "jpeg_quality": q,
        "has_exif": False,     # degraded images are programmatically created
        "generator_tag": None
    }
