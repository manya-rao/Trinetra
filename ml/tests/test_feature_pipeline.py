"""
Test feature pipeline consistency between training and inference.
Verifies that training (extract_cache / ingest_user) and inference (predict)
use the exact same extraction code path, and asserts failure if they diverge.
"""
import inspect
import numpy as np
import pytest
from PIL import Image

import ml.predict
import ml.features.extract_cache
import ml.data.ingest_user
from ml.features.pipeline import extract_all_features


def test_training_and_inference_use_same_pipeline_function():
    """
    Assert that predict, extract_cache, and ingest_user all import
    and reference the exact canonical extract_all_features function.
    """
    assert hasattr(ml.predict, "extract_all_features"), "predict.py does not import extract_all_features"
    assert hasattr(ml.features.extract_cache, "extract_all_features"), "extract_cache.py does not import extract_all_features"
    assert hasattr(ml.data.ingest_user, "extract_all_features"), "ingest_user.py does not import extract_all_features"

    assert ml.predict.extract_all_features is extract_all_features, "predict.py uses a divergent extract_all_features"
    assert ml.features.extract_cache.extract_all_features is extract_all_features, "extract_cache.py uses a divergent extract_all_features"
    assert ml.data.ingest_user.extract_all_features is extract_all_features, "ingest_user.py uses a divergent extract_all_features"


def test_feature_shapes_and_values_are_deterministic_and_identical():
    """
    Verifies that calling extract_all_features produces exact matching shapes
    and deterministic numerical values across multiple calls on the same image.
    """
    # Create test image with non-trivial pattern
    img = Image.new("RGB", (384, 384), color=(100, 150, 200))
    for x in range(0, 384, 16):
        for y in range(0, 384, 16):
            img.putpixel((x, y), (255, 0, 0))

    feat1 = extract_all_features(img)
    feat2 = extract_all_features(img)

    assert set(feat1.keys()) == {"clip", "frequency", "noise", "metadata"}

    # Dimensions
    assert feat1["clip"].shape == (512,), f"Expected CLIP shape (512,), got {feat1['clip'].shape}"
    assert feat1["frequency"].shape == (70,), f"Expected frequency shape (70,), got {feat1['frequency'].shape}"
    assert feat1["noise"].shape == (15,), f"Expected noise shape (15,), got {feat1['noise'].shape}"
    assert feat1["metadata"].shape == (3,), f"Expected metadata shape (3,), got {feat1['metadata'].shape}"

    # Numerical equivalence across runs
    np.testing.assert_allclose(feat1["clip"], feat2["clip"], rtol=1e-5, err_msg="CLIP embeddings diverge across calls")
    np.testing.assert_allclose(feat1["frequency"], feat2["frequency"], rtol=1e-5, err_msg="Frequency features diverge across calls")
    np.testing.assert_allclose(feat1["noise"], feat2["noise"], rtol=1e-5, err_msg="Noise features diverge across calls")
    np.testing.assert_allclose(feat1["metadata"], feat2["metadata"], rtol=1e-5, err_msg="Metadata features diverge across calls")
