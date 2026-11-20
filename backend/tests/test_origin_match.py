import os
import sys
import unittest
import tempfile
from pathlib import Path
import json

# Add project root to PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.build_index import main as build_index_main
from backend.origin_match import match_origin
from backend.fingerprint import extract_features

class TestOriginMatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Build the index once for all tests
        build_index_main()
        # Locate a demo image (placeholder if download failed)
        demo_img_dir = Path(PROJECT_ROOT) / "backend" / "data" / "demo_images"
        cls.sample_img = next(demo_img_dir.glob("*.jpg"))
        cls.sample_feats = extract_features(str(cls.sample_img))

    def test_match_same_image(self):
        result = match_origin(self.sample_feats['phash'], self.sample_feats['clip_vec'])
        self.assertIsNotNone(result)
        # The returned record should refer to the same filename
        self.assertEqual(result['filename'], self.sample_img.name)

    def test_no_match_random(self):
        # Create a fake phash far away and a random vector
        fake_phash = 'ffffffffffffffff'  # all bits set
        fake_vec = [0.0] * 512
        result = match_origin(fake_phash, fake_vec)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
