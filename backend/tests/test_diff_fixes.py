"""
Tests for diff, reliability, and aggregation fixes.
Contract:
- identical copy of demo_ref_001.jpg -> original
- same image with a red rectangle drawn over about a quarter -> modified, with a region roughly around the rectangle, not the full frame
- same image resized to 120x90 at JPEG quality 30, no edit -> NOT modified
- two consecutive requests give different heatmap URLs
- no verdict is ever likely_real_looking
"""

import io
import tempfile
from pathlib import Path
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from app.main import app
from app.config import DATA_DIR, STATIC_FILES_DIR
from backend.diff import diff_images
from backend.aggregator import aggregate, finalize_passport

client = TestClient(app)
REF_PATH = DATA_DIR / "demo_images" / "demo_ref_001.jpg"


def test_identical_copy_of_demo_ref_001_gives_original(tmp_path):
    """Identical copy of demo_ref_001.jpg must evaluate to original."""
    assert REF_PATH.exists(), f"Reference file not found at {REF_PATH}"
    
    # 1. Unit level diff and aggregation
    diff_out = diff_images(REF_PATH, REF_PATH, tmp_path, request_id="unit_identical")
    assert diff_out["reliable"] is True
    assert len(diff_out["changed_regions"]) == 0
    
    phash_match = {
        "filename": "demo_ref_001.jpg",
        "source": "Wikimedia Commons (DEMO DATA)",
        "phash": "1111111111111111"
    }
    result = aggregate(
        phash_match=phash_match,
        diff_result=diff_out,
        c2pa=None,
        ml_output=None,
        demo_data=True
    )
    result = finalize_passport(result, "pass_ident", consent_external=False)
    assert result["verdict"] == "original"
    assert result["eyes"]["change"] == "none"

    # 2. Integration level via POST /analyze
    with open(REF_PATH, "rb") as f:
        img_bytes = f.read()
    
    response = client.post(
        "/analyze",
        files={"image": ("demo_ref_001.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "original"
    assert data["eyes"]["change"] == "none"


def test_red_rectangle_quarter_gives_modified(tmp_path):
    """Same image with a red rectangle over ~quarter -> modified, roughly around rectangle, not full frame."""
    assert REF_PATH.exists()
    img = Image.open(REF_PATH).convert("RGB")
    w, h = img.size

    # Draw a red rectangle over roughly a quarter of the image
    mod_img = img.copy()
    draw = ImageDraw.Draw(mod_img)
    x0, y0 = int(w * 0.25), int(h * 0.25)
    x1, y1 = int(w * 0.75), int(h * 0.50)
    draw.rectangle([x0, y0, x1, y1], fill=(255, 0, 0))

    mod_path = tmp_path / "red_rect.jpg"
    mod_img.save(mod_path, format="JPEG", quality=95)

    # Run diff
    diff_out = diff_images(REF_PATH, mod_path, tmp_path, request_id="unit_modified")
    assert diff_out["reliable"] is True
    assert len(diff_out["changed_regions"]) > 0

    # Ensure changed region is roughly around the rectangle and NOT the full frame
    total_area = w * h
    for r in diff_out["changed_regions"]:
        box_area = r["w"] * r["h"]
        assert box_area < 0.85 * total_area, "Changed region should not encompass the full frame"

    # Aggregator verdict
    phash_match = {
        "filename": "demo_ref_001.jpg",
        "source": "Wikimedia Commons (DEMO DATA)",
        "phash": "0000000000000000"  # modified hash
    }
    result = aggregate(
        phash_match=phash_match,
        diff_result=diff_out,
        c2pa=None,
        ml_output=None,
        demo_data=True
    )
    result = finalize_passport(result, "pass_mod", consent_external=False)
    assert result["verdict"] == "modified"
    assert result["eyes"]["change"] == "found"


def test_resized_to_120x90_q30_not_modified(tmp_path):
    """Same image resized to 120x90 at JPEG quality 30, no edit -> NOT modified."""
    assert REF_PATH.exists()
    img = Image.open(REF_PATH).convert("RGB")
    tiny_img = img.resize((120, 90), Image.Resampling.LANCZOS)
    
    tiny_path = tmp_path / "tiny_q30.jpg"
    tiny_img.save(tiny_path, format="JPEG", quality=30)

    diff_out = diff_images(REF_PATH, tiny_path, tmp_path, request_id="unit_tiny")

    # Aggregator with low resolution / compressed meta
    meta = {"width": 120, "height": 90, "jpeg_quality": 30.0}
    phash_match = {
        "filename": "demo_ref_001.jpg",
        "source": "Wikimedia Commons (DEMO DATA)",
        "phash": "1111111111111111"
    }
    result = aggregate(
        phash_match=phash_match,
        diff_result=diff_out,
        c2pa=None,
        ml_output=None,
        demo_data=True,
        input_meta=meta
    )
    result = finalize_passport(result, "pass_tiny", consent_external=False)
    assert result["verdict"] != "modified", "Degraded / resized image must NEVER be flagged as modified"
    assert result["verdict"] in ("inconclusive", "original")


def test_two_consecutive_requests_give_different_heatmap_urls(tmp_path):
    """Two consecutive requests must yield different unique heatmap and aligned URLs."""
    img_bytes = create_dummy_jpeg()

    res1 = client.post(
        "/analyze",
        files={"image": ("edited_sample_1.jpg", img_bytes, "image/jpeg")}
    )
    assert res1.status_code == 200
    data1 = res1.json()

    res2 = client.post(
        "/analyze",
        files={"image": ("edited_sample_2.jpg", img_bytes, "image/jpeg")}
    )
    assert res2.status_code == 200
    data2 = res2.json()

    assert data1["id"] != data2["id"]
    if data1.get("diff") and data2.get("diff"):
        assert data1["diff"]["heatmap_url"] != data2["diff"]["heatmap_url"]
        assert data1["diff"]["aligned_url"] != data2["diff"]["aligned_url"]


def test_no_verdict_is_ever_likely_real_looking():
    """Ensure likely_real_looking is NEVER emitted from aggregator or API."""
    bands_to_test = [
        {"band": "likely_real_looking", "confidence": "high", "reasons": []},
        {"band": "likely_ai", "confidence": "high", "reasons": []},
        {"band": "inconclusive", "confidence": "low", "reasons": []},
    ]

    for ml_out in bands_to_test:
        res = aggregate(
            phash_match=None,
            diff_result=None,
            c2pa=None,
            ml_output=ml_out,
            demo_data=True
        )
        assert res["verdict"] != "likely_real_looking", f"Failed for ml_output {ml_out}"
        if ml_out["band"] == "likely_real_looking":
            assert res["verdict"] == "inconclusive"
            reason_keys = [r["key"] for r in res["reasons"]]
            assert "no_ai_signs_found" in reason_keys


def create_dummy_jpeg() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (320, 240), color=(180, 200, 220))
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
