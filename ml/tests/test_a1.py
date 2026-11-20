"""
Unit tests for Milestone A0/A1:
- Shared strings JSON contract validation
- Fixed reason keys
- Gate logic
- Stub predict() interface adherence
- No percentage leak guarantee
"""
import json
import numpy as np
from PIL import Image
from ml.config import STRINGS_PATH, VALID_REASONS
from ml.gate import evaluate_gate
from ml.reasons import format_reasons, load_strings
from ml.predict import predict
from ml.features.frequency import extract_frequency_features
from ml.features.noise import extract_noise_features
from ml.features.metadata import extract_metadata_features

def test_shared_strings_contract():
    strings = load_strings()
    assert "verdicts" in strings
    assert "reasons" in strings
    assert "ui" in strings
    
    # 7 frozen verdicts
    expected_verdicts = {
        "original", "modified", "out_of_context",
        "ai_confirmed", "likely_ai", "likely_real_looking", "inconclusive"
    }
    assert set(strings["verdicts"].keys()) == expected_verdicts
    
    # Check dual language (EN / HI) on verdicts
    for v_key, v_val in strings["verdicts"].items():
        assert "headline" in v_val
        assert "en" in v_val["headline"] and len(v_val["headline"]["en"]) > 0
        assert "hi" in v_val["headline"] and len(v_val["headline"]["hi"]) > 0

    # Fixed reasons
    assert set(strings["reasons"].keys()) == VALID_REASONS
    for r_key, r_val in strings["reasons"].items():
        assert "en" in r_val and len(r_val["en"]) > 0
        assert "hi" in r_val and len(r_val["hi"]) > 0

def test_no_percentage_in_strings():
    with open(STRINGS_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    assert "%" not in text, "Percentage symbol '%' found in shared/strings.json! Bare percentages are forbidden."

def test_no_bare_percentage_in_predictions_and_mocks():
    """
    Enforces the core confirmation ladder rule:
    No bare percentage may ever appear in prediction output strings or mock fixtures.
    """
    from pathlib import Path
    
    # 1. Test mock fixtures
    mocks_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "mocks"
    for mock_file in mocks_dir.glob("*.json"):
        with open(mock_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Check verdict, confidence_band, reasons, scope_note, lang
        assert "%" not in data.get("verdict", "")
        assert "%" not in data.get("confidence_band", "")
        for r in data.get("reasons", []):
            assert "%" not in r.get("en", "")
            assert "%" not in r.get("hi", "")
        if "scope_note" in data and isinstance(data["scope_note"], dict):
            assert "%" not in data["scope_note"].get("en", "")
            assert "%" not in data["scope_note"].get("hi", "")
        if "lang" in data and isinstance(data["lang"], dict):
            assert "%" not in data["lang"].get("en", "")
            assert "%" not in data["lang"].get("hi", "")

    # 2. Test predict() output across diverse conditions
    test_cases = [
        (Image.new("RGB", (300, 300), color=(100, 150, 200)), {"jpeg_quality": 85.0}),
        (Image.new("RGB", (150, 150), color=(50, 50, 50)), {"jpeg_quality": 90.0}), # low-res
        (Image.new("RGB", (400, 400), color=(200, 200, 200)), {"jpeg_quality": 40.0}), # heavy-comp
        (Image.new("RGB", (350, 350), color=(128, 128, 128)), {"generator_tag": "midjourney"}),
    ]
    for img, meta in test_cases:
        res = predict(img, meta)
        assert "%" not in res["band"]
        for r in res["reasons"]:
            assert "%" not in r["en"]
            assert "%" not in r["hi"]

def test_gate_rules():
    # Min dim < 256 triggers low_resolution
    triggered, reasons = evaluate_gate(width=200, height=300)
    assert triggered is True
    assert "low_resolution" in reasons
    
    # Low jpeg quality triggers heavy_compression
    triggered, reasons = evaluate_gate(width=512, height=512, jpeg_quality=40.0)
    assert triggered is True
    assert "heavy_compression" in reasons
    
    # Valid high-res clean image does not trigger gate
    triggered, reasons = evaluate_gate(width=512, height=512, jpeg_quality=95.0)
    assert triggered is False
    assert len(reasons) == 0

def test_predict_interface_contract():
    # Generate dummy test image 300x300
    img = Image.new("RGB", (300, 300), color=(120, 150, 180))
    meta = {
        "width": 300,
        "height": 300,
        "file_size": 45000,
        "jpeg_quality": 85.0,
        "has_exif": True,
        "generator_tag": None
    }
    result = predict(img, meta)
    
    # Verify contract keys and types
    assert "band" in result
    assert result["band"] in ["likely_real_looking", "inconclusive", "likely_ai"]
    assert "reasons" in result
    assert isinstance(result["reasons"], list)
    for r in result["reasons"]:
        assert "key" in r and r["key"] in VALID_REASONS
        assert "en" in r and "hi" in r
    assert "gate_triggered" in result
    assert isinstance(result["gate_triggered"], bool)
    assert "suspicious_map_png" in result
    
    # Verify no bare percentage in any text field
    assert "%" not in result["band"]
    for r in result["reasons"]:
        assert "%" not in r["en"]
        assert "%" not in r["hi"]

def test_feature_extraction_shapes():
    img = Image.new("RGB", (256, 256), color=(100, 100, 100))
    freq = extract_frequency_features(img)
    assert isinstance(freq, np.ndarray)
    assert len(freq.shape) == 1
    
    noise = extract_noise_features(img)
    assert isinstance(noise, np.ndarray)
    assert len(noise.shape) == 1
    
    meta_feat = extract_metadata_features(img)
    assert isinstance(meta_feat, np.ndarray)
    assert len(meta_feat.shape) == 1
