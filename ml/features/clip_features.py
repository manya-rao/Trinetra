"""
OpenCLIP Visual Feature Extractor (Eye 3)
Extracts L2-normalized image embeddings using frozen OpenCLIP ViT-B-32.
Loads model and weights once. Runs on CPU (or GPU if detected).
"""
import torch
import numpy as np
from PIL import Image
from typing import Optional
from pathlib import Path
from ml.config import CLIP_MODEL_NAME, CLIP_PRETRAINED, BASE_DIR

WEIGHTS_PATH = BASE_DIR / "models" / "weights" / "vit_b_32-laion2b_e16.pth"

_CLIP_MODEL = None
_CLIP_PREPROCESS = None
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

import functools

# PyTorch 2.6+ compatibility: ensure weights_only=False for OpenCLIP checkpoint loading
_orig_torch_load = torch.load
@functools.wraps(_orig_torch_load)
def _safe_torch_load(*args, **kwargs):
    if "weights_only" not in kwargs:
        kwargs["weights_only"] = False
    return _orig_torch_load(*args, **kwargs)

def get_clip_model():
    global _CLIP_MODEL, _CLIP_PREPROCESS
    if _CLIP_MODEL is None:
        import open_clip
        # Apply load compatibility patch
        torch.load = _safe_torch_load
        try:
            if WEIGHTS_PATH.exists():
                model, _, preprocess = open_clip.create_model_and_transforms(
                    "ViT-B-32",
                    pretrained=str(WEIGHTS_PATH),
                    device=_DEVICE
                )
            else:
                model, _, preprocess = open_clip.create_model_and_transforms(
                    CLIP_MODEL_NAME,
                    pretrained=CLIP_PRETRAINED,
                    device=_DEVICE
                )
        finally:
            torch.load = _orig_torch_load
        model.eval()
        for p in model.parameters():
            p.requires_grad = False
        _CLIP_MODEL = model
        _CLIP_PREPROCESS = preprocess
    return _CLIP_MODEL, _CLIP_PREPROCESS, _DEVICE

def extract_clip_embedding(image: Image.Image) -> np.ndarray:
    """
    Extracts L2-normalized 512-dimensional CLIP embedding from PIL Image.
    """
    model, preprocess, device = get_clip_model()
    img_rgb = image.convert("RGB")
    tensor = preprocess(img_rgb).unsqueeze(0).to(device)
    
    with torch.no_grad():
        features = model.encode_image(tensor)
        # L2-normalize
        features /= features.norm(dim=-1, keepdim=True)
        embedding = features.squeeze(0).cpu().numpy().astype(np.float32)
        
    return embedding
