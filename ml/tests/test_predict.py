"""
Integration Tests for Eye 3 (predict interface contract)
Ensures full compliance with the shared contract before integration with Device B.
"""
import io
import pytest
from PIL import Image
from ml.predict import predict
from ml.config import VALID_REASONS

def test_predict_full_contract():
    img = Image.new("RGB", (384, 384), color=(140, 160, 180))
    meta = {
        "width": 384,
        "height": 384,
        "file_size": 85000,
        "jpeg_quality": 90.0,
        "has_exif": True,
        "generator_tag": None
    }
    result = predict(img, meta)
    
    assert "band" in result
    assert result["band"] in ["likely_real_looking", "inconclusive", "likely_ai"]
    assert "%" not in result["band"]
    
    assert "reasons" in result
    assert isinstance(result["reasons"], list)
    for r in result["reasons"]:
        assert r["key"] in VALID_REASONS
        assert "%" not in r["en"]
        assert "%" not in r["hi"]
        
    assert "gate_triggered" in result
    assert isinstance(result["gate_triggered"], bool)
    
    assert "suspicious_map_png" in result
    if result["suspicious_map_png"] is not None:
        assert isinstance(result["suspicious_map_png"], bytes)
        # Verify valid PNG
        over = Image.open(io.BytesIO(result["suspicious_map_png"]))
        assert over.format == "PNG"

def test_predict_small_image_gate():
    # 200x200 should trigger gate
    img = Image.new("RGB", (200, 200), color=(100, 100, 100))
    meta = {
        "width": 200,
        "height": 200,
        "file_size": 25000,
        "jpeg_quality": 85.0,
        "has_exif": True,
        "generator_tag": None
    }
    result = predict(img, meta)
    assert result["gate_triggered"] is True
    assert result["band"] == "inconclusive"
    assert any(r["key"] == "low_resolution" for r in result["reasons"])

def test_predict_heavy_compression_gate():
    img = Image.new("RGB", (400, 400), color=(100, 100, 100))
    meta = {
        "width": 400,
        "height": 400,
        "file_size": 25000,
        "jpeg_quality": 45.0,
        "has_exif": True,
        "generator_tag": None
    }
    result = predict(img, meta)
    assert result["gate_triggered"] is True
    assert result["band"] == "inconclusive"
    assert any(r["key"] == "heavy_compression" for r in result["reasons"])

def test_predict_generator_tag():
    img = Image.new("RGB", (384, 384), color=(100, 100, 100))
    meta = {
        "width": 384,
        "height": 384,
        "file_size": 55000,
        "jpeg_quality": 90.0,
        "has_exif": False,
        "generator_tag": "Midjourney v6"
    }
    result = predict(img, meta)
    reasons_keys = [r["key"] for r in result["reasons"]]
    assert "generator_tag_found" in reasons_keys
    assert "no_camera_metadata" in reasons_keys

def test_camera_exif_image_can_never_be_likely_ai():
    """Requirement: An image carrying genuine camera EXIF can NEVER be likely_ai."""
    from pathlib import Path
    img_path = Path("ml/data/user/misflagged_01.jpg")
    assert img_path.exists(), "Test camera image must exist"
    img = Image.open(img_path)
    meta = {
        "width": img.width,
        "height": img.height,
        "file_size": img_path.stat().st_size,
        "jpeg_quality": 100.0,
        "has_exif": True,
        "generator_tag": None
    }
    result = predict(img, meta)
    assert result["band"] != "likely_ai", "Camera EXIF image was falsely flagged as likely_ai!"
    assert result["band"] == "inconclusive"
    reasons = [r["key"] for r in result["reasons"]]
    assert "camera_metadata_present" in reasons

def test_large_full_res_and_downscaled_copy_give_consistent_bands():
    """Requirement: Large full-resolution image and its downscaled copy give consistent bands."""
    from pathlib import Path
    img_path = Path("ml/data/user/misflagged_01.jpg")
    assert img_path.exists()
    img_large = Image.open(img_path)
    meta_large = {
        "width": img_large.width,
        "height": img_large.height,
        "file_size": img_path.stat().st_size,
        "jpeg_quality": 100.0,
        "has_exif": True,
    }
    res_large = predict(img_large, meta_large)

    img_downscaled = img_large.resize((384, 384), Image.Resampling.BICUBIC)
    meta_downscaled = {
        "width": 384,
        "height": 384,
        "file_size": 85000,
        "jpeg_quality": 95.0,
        "has_exif": True,
    }
    res_downscaled = predict(img_downscaled, meta_downscaled)

    # Both must produce the exact same band
    assert res_large["band"] == res_downscaled["band"], f"Inconsistent bands: {res_large['band']} vs {res_downscaled['band']}"
    assert res_large["band"] == "inconclusive"

