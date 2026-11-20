import os
import sys
from pathlib import Path
import tempfile
import unittest
from PIL import Image

# Ensure project root is on PYTHONPATH for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.fingerprint import extract_features

class TestFingerprint(unittest.TestCase):
    def test_extract_features_basic(self):
        # create a temporary image
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            img = Image.new('RGB', (800, 600), color='gray')
            img.save(tmp.name, format='JPEG')
            tmp_path = tmp.name
        try:
            feats = extract_features(tmp_path)
            # required keys
            self.assertIn('phash', feats)
            self.assertIn('clip_vec', feats)
            self.assertIn('meta', feats)
            # phash should be a 16‑char hex string (64‑bit)
            self.assertEqual(len(feats['phash']), 16)
            # clip_vec length should be 512 (or fallback zero vector)
            self.assertEqual(len(feats['clip_vec']), 512)
            # meta fields
            meta = feats['meta']
            self.assertIn('width', meta)
            self.assertIn('height', meta)
            self.assertIn('file_size', meta)
        finally:
            os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
