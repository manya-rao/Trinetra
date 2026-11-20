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
