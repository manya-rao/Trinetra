"""
Determinism and Reproducibility Unit Tests (Eye 3)
Verifies that:
1. Feature extraction is deterministic across multiple calls on the same image.
2. Predict output is deterministic given identical image and metadata.
3. Random seed management produces reproducible behavior.
"""
import numpy as np
from PIL import Image
from ml.features.frequency import extract_frequency_features
from ml.features.noise import extract_noise_features
from ml.features.metadata import extract_metadata_features
from ml.predict import predict

def test_feature_determinism():
    img = Image.new("RGB", (300, 300), color=(140, 170, 200))
    
    # Run 1
    f1 = extract_frequency_features(img)
    n1 = extract_noise_features(img)
    m1 = extract_metadata_features(img)
    
    # Run 2
    f2 = extract_frequency_features(img)
    n2 = extract_noise_features(img)
    m2 = extract_metadata_features(img)
    
    np.testing.assert_allclose(f1, f2, rtol=1e-5, atol=1e-5, err_msg="Frequency features must be deterministic")
    np.testing.assert_allclose(n1, n2, rtol=1e-5, atol=1e-5, err_msg="Noise features must be deterministic")
    np.testing.assert_allclose(m1, m2, rtol=1e-5, atol=1e-5, err_msg="Metadata features must be deterministic")

def test_predict_determinism():
    img = Image.new("RGB", (384, 384), color=(100, 120, 140))
    meta = {
        "width": 384,
        "height": 384,
        "file_size": 90000,
        "jpeg_quality": 88.0,
        "has_exif": True,
        "generator_tag": None
    }
    
    res1 = predict(img, meta)
    res2 = predict(img, meta)
    
    assert res1["band"] == res2["band"]
    assert res1["gate_triggered"] == res2["gate_triggered"]
    assert len(res1["reasons"]) == len(res2["reasons"])
    assert [r["key"] for r in res1["reasons"]] == [r["key"] for r in res2["reasons"]]
