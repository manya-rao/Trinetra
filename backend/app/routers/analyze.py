"""
Analyze router for Trinetra.
Provides POST /analyze with real pipeline integration:
C2PA -> Origin Match (pHash + CLIP) -> Alignment & Diff -> ML Synthesis Lane -> Ladder Aggregator.
"""

import json
import uuid
import logging
import sys
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image
from fastapi import APIRouter, File, UploadFile, Form, HTTPException

# Ensure both repo root and backend directory are on sys.path
_backend_dir = Path(__file__).resolve().parent.parent.parent
_repo_root = _backend_dir.parent
for _p in [str(_repo_root), str(_backend_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.config import FIXTURES_DIR, STATIC_FILES_DIR, DATA_DIR
from app import config as cfg
from app.schemas import PassportResponse
from app.storage import save_passport

try:
    from fingerprint import extract_features
    from origin_match import match_origin
    from diff import diff_images
    from c2pa_check import check_c2pa
    from aggregator import aggregate, finalize_passport
except ImportError:
    from backend.fingerprint import extract_features
    from backend.origin_match import match_origin
    from backend.diff import diff_images
    from backend.c2pa_check import check_c2pa
    from backend.aggregator import aggregate, finalize_passport

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
    Follows strict Three Eyes Confirmation Ladder:
    1. C2PA verification (Eye 3 confirmed)
    2. Indexed Origin match (Eye 1 origin + Eye 2 change diff)
    3. AI Lane classifier (Eye 3 likely_ai / inconclusive)
    """
    filename = (image.filename or "").lower()
    passport_id = f"pass_{uuid.uuid4().hex[:12]}"
    
    # Save uploaded file temporarily for inspection
    STATIC_FILES_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = STATIC_FILES_DIR / f"upload_{passport_id}_{image.filename or 'upload.jpg'}"
    contents = await image.read()
    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        # Step 1: C2PA / Content Credentials Check
        c2pa_data = check_c2pa(temp_path)
        if cfg.MOCK_MODE and ("c2pa" in filename or "ai_confirmed" in filename) and c2pa_data.get("status") == "none":
            c2pa_data = {
                "status": "valid",
                "ai_generated": True,
                "manifest_found": True,
                "issuer": "self-signed DEMO signer",
                "is_trusted": False
            }
        if c2pa_data.get("status") == "valid" and c2pa_data.get("ai_generated"):
            passport_dict = aggregate(
                phash_match=None,
                diff_result=None,
                c2pa=c2pa_data,
                ml_output=None,
                claim_text=claim_text,
                consent_external=consent_external,
                demo_data=True
            )
            passport_dict = finalize_passport(passport_dict, passport_id, consent_external)
            passport = PassportResponse(**passport_dict)
            save_passport(passport)
            return passport

        # Open PIL Image and construct honest metadata (no invented values)
        pil_img = Image.open(temp_path)
        img_w, img_h = pil_img.size
        file_size = len(contents)
        raw_exif = pil_img.getexif()
        has_exif = bool(raw_exif and len(raw_exif) > 0)

        # Estimate JPEG quality from quantization tables: PNG -> None; unknown -> None
        is_png = (pil_img.format == "PNG") or filename.endswith(".png")
        jpeg_quality = None
        if not is_png and pil_img.format == "JPEG":
            qt = getattr(pil_img, "quantization", None)
            if qt and 0 in qt:
                try:
                    val = qt[0][0]
                    if val <= 1:
                        jpeg_quality = 100.0
                    elif val >= 16:
                        jpeg_quality = float(np.clip(round(800.0 / val), 1, 50))
                    else:
                        jpeg_quality = float(np.clip(round((200.0 - (val / 0.16)) / 2.0), 51, 99))
                except Exception:
                    jpeg_quality = None

        meta = {
            "width": img_w,
            "height": img_h,
            "file_size": file_size,
            "jpeg_quality": jpeg_quality,
            "has_exif": has_exif,
            "generator_tag": None,
        }

        # Step 2: Fingerprint extraction (pHash and CLIP)
        feats = extract_features(str(temp_path))
        phash = feats["phash"]
        clip_vec = feats["clip_vec"]
        meta["phash"] = phash

        # Step 3: Origin matching against curated reference index
        phash_match = match_origin(phash, clip_vec)
        diff_res = None

        # Handle mock fixture filename fallbacks when MOCK_MODE is enabled
        if cfg.MOCK_MODE and not phash_match:
            if "original" in filename:
                phash_match = {
                    "filename": "demo_ref_001.jpg",
                    "source": "Wikimedia Commons (DEMO DATA)",
                    "date": "2021-08-15",
                    "factcheck_url": "https://commons.wikimedia.org/wiki/File:DEMO_Archive.jpg",
                    "claim_en": "DEMO DATA: Flooding archive photo from August 2021 news report",
                    "claim_hi": "डेमो डेटा: अगस्त 2021 की समाचार रिपोर्ट से बाढ़ संग्रह फोटो",
                    "thumb_url": "/files/thumb_demo_original.jpg",
                    "phash": phash
                }
            elif "modified" in filename or "edited" in filename:
                phash_match = {
                    "filename": "demo_ref_001.jpg",
                    "source": "Wikimedia Commons (DEMO DATA)",
                    "date": "2021-08-15",
                    "factcheck_url": "https://commons.wikimedia.org/wiki/File:DEMO_Archive.jpg",
                    "claim_en": "DEMO DATA: Flooding archive photo from August 2021 news report",
                    "claim_hi": "डेमो डेटा: अगस्त 2021 की समाचार रिपोर्ट से बाढ़ संग्रह फोटो",
                    "thumb_url": "/files/thumb_demo_original.jpg",
                    "phash": "0000000000000000"
                }
                diff_res = {
                    "reliable": True,
                    "reliability_reason": "Mock fixture match",
                    "heatmap_url": f"/files/{passport_id}_heatmap.png",
                    "aligned_url": f"/files/{passport_id}_aligned.png",
                    "changed_regions": [{"x": 120, "y": 80, "w": 180, "h": 140}]
                }

        # Step 4: If match found in index, check for modifications via diff
        if phash_match and diff_res is None:
            ref_filename = phash_match.get("filename")
            ref_path = DATA_DIR / "demo_images" / ref_filename if ref_filename else None
            if ref_path and ref_path.is_file():
                # Run diff when perceptual hash indicates difference or verification needed
                if phash != phash_match.get("phash"):
                    try:
                        diff_out = diff_images(ref_path, temp_path, STATIC_FILES_DIR, request_id=passport_id)
                        if diff_out:
                            diff_res = {
                                "reliable": diff_out.get("reliable", True),
                                "reliability_reason": diff_out.get("reliability_reason", ""),
                                "inlier_count": diff_out.get("inlier_count", 0),
                                "inlier_ratio": diff_out.get("inlier_ratio", 0.0),
                                "changed_area_fraction": diff_out.get("changed_area_fraction", 0.0),
                                "heatmap_url": f"/files/{passport_id}_heatmap.png" if diff_out.get("heatmap_path") else "",
                                "aligned_url": f"/files/{passport_id}_aligned.png" if diff_out.get("aligned_path") else "",
                                "changed_regions": diff_out.get("changed_regions", [])
                            }
                    except Exception as e:
                        logger.warning(f"Diff execution failed: {e}")

        # Step 5: If no origin match, invoke AI Synthesis Lane (Eye 3)
        ml_output = None
        if not phash_match:
            if hash_only:
                # Privacy guarantee: in hash-only mode, no pixel data is evaluated by AI lane
                ml_output = {
                    "band": "inconclusive",
                    "confidence": "low",
                    "reasons": ["no_origin_match"],
                    "gate_triggered": False
                }
            elif cfg.MOCK_MODE and any(k in filename for k in ["likely_ai", "likely_real", "inconclusive"]):
                # Explicit mock mode test filenames
                if "likely_ai" in filename:
                    ml_output = {
                        "band": "likely_ai",
                        "confidence": "medium",
                        "reasons": ["spectrum_peaks", "noise_uniform"],
                        "gate_triggered": False
                    }
                elif "likely_real" in filename:
                    ml_output = {
                        "band": "likely_real_looking",
                        "confidence": "low",
                        "reasons": [],
                        "gate_triggered": False
                    }
                else:
                    ml_output = {
                        "band": "inconclusive",
                        "confidence": "low",
                        "reasons": ["heavy_compression"],
                        "gate_triggered": False
                    }
            else:
                try:
                    from ml.predict import predict as ml_predict
                    ml_output = ml_predict(pil_img, meta)
                except Exception as e:
                    logger.warning(f"ML lane invocation failed: {e}")
                    ml_output = {
                        "band": "inconclusive",
                        "confidence": "low",
                        "reasons": ["ai_band_inconclusive"],
                        "gate_triggered": False
                    }

        # Step 6: Ladder aggregation & finalization
        passport_dict = aggregate(
            phash_match=phash_match,
            diff_result=diff_res,
            c2pa=c2pa_data,
            ml_output=ml_output,
            claim_text=claim_text,
            consent_external=consent_external,
            demo_data=True,
            input_meta=meta
        )
        passport_dict = finalize_passport(passport_dict, passport_id, consent_external)

        passport = PassportResponse(**passport_dict)
        save_passport(passport)
        return passport

    finally:
        # Rule 5: Uploaded raw originals are ALWAYS deleted after processing
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
