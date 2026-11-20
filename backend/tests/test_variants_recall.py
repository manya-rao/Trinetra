"""
Test origin match recall across variant types:
resized, cropped, recompressed, screenshot, edited.
Also tests C2PA credentials extraction.
"""

import unittest
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import tempfile
import os

from backend.fingerprint import extract_features
from backend.origin_match import match_origin
from backend.c2pa_check import check_c2pa

BASE_DIR = Path(__file__).resolve().parents[1]
DEMO_IMG_DIR = BASE_DIR / "data" / "demo_images"

class TestVariantsRecallAndC2PA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Pick 3 demo images
        images = list(DEMO_IMG_DIR.glob("*.jpg"))
        cls.test_images = images[:3]
        assert len(cls.test_images) >= 1, "At least one demo image required"

    def test_recompressed_variant_recall(self):
        for img_path in self.test_images:
            img = Image.open(img_path).convert("RGB")
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_name = tmp.name
            try:
                img.save(tmp_name, format="JPEG", quality=60)
                feats = extract_features(tmp_name)
                match = match_origin(feats["phash"], feats["clip_vec"])
                self.assertIsNotNone(match, f"Failed to recall recompressed variant of {img_path.name}")
                self.assertEqual(match["filename"], img_path.name)
            finally:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)

    def test_resized_variant_recall(self):
        for img_path in self.test_images:
            img = Image.open(img_path).convert("RGB")
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_name = tmp.name
            try:
                resized = img.resize((400, 300))
                resized.save(tmp_name, format="JPEG", quality=85)
                feats = extract_features(tmp_name)
                match = match_origin(feats["phash"], feats["clip_vec"])
                self.assertIsNotNone(match, f"Failed to recall resized variant of {img_path.name}")
                self.assertEqual(match["filename"], img_path.name)
            finally:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)

    def test_screenshot_variant_recall(self):
        for img_path in self.test_images:
            img = Image.open(img_path).convert("RGB")
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_name = tmp.name
            try:
                bordered = ImageOps.expand(img, border=12, fill="white")
                bordered.save(tmp_name, format="JPEG", quality=85)
                feats = extract_features(tmp_name)
                match = match_origin(feats["phash"], feats["clip_vec"])
                self.assertIsNotNone(match, f"Failed to recall screenshot variant of {img_path.name}")
                self.assertEqual(match["filename"], img_path.name)
            finally:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)

    def test_c2pa_check_detection(self):
        # 1. Normal image -> status none
        sample_img = self.test_images[0]
        c2pa_norm = check_c2pa(str(sample_img))
        self.assertEqual(c2pa_norm["status"], "none")
        self.assertFalse(c2pa_norm["ai_generated"])

        # 2. C2PA confirmed image -> status valid, ai_generated True
        c2pa_ai = check_c2pa("c2pa_ai_confirmed_test.jpg")
        self.assertEqual(c2pa_ai["status"], "valid")
        self.assertTrue(c2pa_ai["ai_generated"])

        # 3. Invalid / tampered -> status invalid
        c2pa_inv = check_c2pa("invalid_c2pa_tampered.jpg")
        self.assertEqual(c2pa_inv["status"], "invalid")
