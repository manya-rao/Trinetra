"""
Canonical feature extraction pipeline for Trinetra Eye 3.
Ensures training (extract_cache / ingest_user) and inference (predict)
share the exact same feature extraction implementation.
"""
from typing import Tuple, Dict, Any, Optional
import numpy as np
from PIL import Image

from ml.features.clip_features import extract_clip_embedding
from ml.features.frequency import extract_frequency_features
from ml.features.noise import extract_noise_features
from ml.features.metadata import extract_metadata_features


def extract_all_features(image: Image.Image, meta: Optional[Dict[str, Any]] = None) -> Dict[str, np.ndarray]:
    """
    Extracts all multimodal features for a given PIL Image:
    1. OpenCLIP ViT-B-32 embedding (512-dim, L2-normalized)
    2. Azimuthal FFT frequency spectrum (70-dim, 384x384 crop-averaged)
    3. Noise residual & ELA statistics (15-dim, 384x384 crop-averaged)
    4. Metadata heuristic features (3-dim)

    Returns a dict with keys: 'clip', 'frequency', 'noise', 'metadata'.
    """
    img_rgb = image.convert("RGB")
    
    clip_emb = extract_clip_embedding(img_rgb)
    freq_feat = extract_frequency_features(img_rgb)
    noise_feat = extract_noise_features(img_rgb)
    meta_feat = extract_metadata_features(img_rgb, meta=meta)
    
    return {
        "clip": clip_emb,
        "frequency": freq_feat,
        "noise": noise_feat,
        "metadata": meta_feat
    }
