"""
Configuration for Trinetra backend.
Centralizes all environment variables, paths, and computer-vision thresholds.
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
FIXTURES_DIR = REPO_ROOT / "shared" / "fixtures"
SHARED_STRINGS_PATH = REPO_ROOT / "shared" / "strings.json"
FALLBACK_STRINGS_PATH = BASE_DIR / "app" / "resources" / "strings_fallback.json"
STATIC_FILES_DIR = BASE_DIR / "static" / "files"
DATA_DIR = BASE_DIR / "data"

# Environment
MOCK_MODE = os.getenv("MOCK", "1").lower() in ("1", "true", "yes")
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
ML_PATH = os.getenv("ML_PATH", str(REPO_ROOT / "ml"))

# CORS
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "*"  # Allows browser extension and local dev
]

# Detection & CV Thresholds (frozen contract)
PHASH_HAMMING_THRESHOLD = 10          # 10/64 bit flips for near duplicates
CLIP_COSINE_THRESHOLD = 0.85          # Cosine similarity for visual embedding match
MAX_IMAGE_LONG_SIDE = 1600            # Downscale max for SIFT/SSIM; keep original for hash/meta
SSIM_SCORE_THRESHOLD = 0.85           # SSIM similarity below which diff detected
HOMOGRAPHY_RANSAC_REPROJ = 3.0        # RANSAC reprojection error threshold (px)
MIN_CONTOUR_AREA_PX = 150             # Minimum changed region area to suppress noise
