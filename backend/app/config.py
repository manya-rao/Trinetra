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
MOCK_MODE = os.getenv("MOCK", "0").lower() in ("1", "true", "yes")
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

# Gate & Quality Thresholds (unified frozen contract shared with ML)
MIN_IMAGE_DIM = 256                   # Images with min(w, h) < 256 gated to inconclusive
HEAVY_COMPRESSION_JPEG_QUALITY = 75.0 # JPEG Q <= 75 gated to inconclusive

# Untuned CV & Diff Thresholds (named constants, untuned)
DIFF_WORKING_LONG_SIDE = 640          # Common working long side for diff (untuned)
DIFF_BLUR_KERNEL_SIZE = 5             # Pre-SSIM Gaussian blur kernel size (untuned)
DIFF_BLUR_SIGMA = 1.0                 # Pre-SSIM Gaussian blur sigma (untuned)
SSIM_DIFF_THRESHOLD = 0.65            # SSIM similarity below which change is flagged (untuned)
HOMOGRAPHY_MIN_INLIERS = 8            # Minimum homography inliers for reliable alignment (untuned)
HOMOGRAPHY_MIN_INLIER_RATIO = 0.25    # Minimum homography inlier ratio (untuned)
DIFF_MAX_CHANGED_FRACTION = 0.65      # Changed area fraction above which diff is unreliable (untuned)
DIFF_MIN_REGION_BOUNDS = 10           # Minimum box width/height in px for a sane region (untuned)
