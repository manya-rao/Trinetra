"""
Trinetra ML Configuration (Eye 3: Synthesis Engine)
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CACHE_DIR = DATA_DIR / "cache"
MODELS_DIR = BASE_DIR / "models"
STRINGS_PATH = REPO_ROOT / "shared" / "strings.json"

MODEL_FILE = MODELS_DIR / "ai_lane.joblib"
METADATA_FILE = MODELS_DIR / "metadata.json"

# OpenCLIP Backbone
# Defaulting to ViT-B-32 with openai weights for fast download & strict <3s CPU inference budget
CLIP_MODEL_NAME = "ViT-B-32"
CLIP_PRETRAINED = "laion2b_e16"

# Gate & Quality thresholds
MIN_IMAGE_DIM = 256
MAX_IMAGE_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
# Images compressed below this JPEG quality threshold are gated to 'inconclusive'.
# Heavy re-encoding (Q<=75) dramatically alters frequency residuals, causing false accusations
# against real images processed by WhatsApp/Telegram compression (typically Q=72-85).
# We conservatively gate Q<=75 to prevent false accusations on social-media-processed images.
# Decision rationale: verified on WhatsApp-style robustness suite (see RESULTS.md).
HEAVY_COMPRESSION_JPEG_QUALITY = 75.0

# Probability Band Thresholds for calibrated fusion score (p_ai in [0, 1])
# Calibrated on training generators validation set to keep FPR <= 1%
PROB_LOWER_REAL_BAND = 0.35  # Below this -> likely_real_looking
PROB_UPPER_AI_BAND = 0.70    # Above this -> likely_ai
# Between [0.35, 0.70] -> inconclusive

# Feature dimensions
FFT_AZIMUTHAL_BINS = 64
NOISE_GRID_PATCHES = 8       # 8x8 grid of patches
NOISE_FEATURE_DIM = 36       # 8x8 stats + global kurtosis/std + ELA variance

# Reason keys frozen contract
VALID_REASONS = {
    "origin_match_exact",
    "origin_match_near",
    "diff_detected",
    "no_origin_match",
    "c2pa_valid",
    "c2pa_invalid",
    "ai_band_likely",
    "ai_band_inconclusive",
    "gate_triggered",
    "out_of_context",
    "no_ai_signs_found",
    "spectrum_peaks",
    "noise_uniform",
    "no_camera_metadata",
    "clip_ai_signal",
    "low_resolution",
    "heavy_compression",
    "signals_disagree",
    "generator_tag_found"
}

# Known generator tags in EXIF / XMP / Software metadata
KNOWN_GENERATOR_KEYWORDS = [
    "midjourney",
    "stable diffusion",
    "stablediffusion",
    "dall-e",
    "dalle",
    "firefly",
    "adobe firefly",
    "comfyui",
    "automatic1111",
    "invokeai",
    "flux.1",
    "imagen",
    "novelai",
    "leonardo.ai"
]
