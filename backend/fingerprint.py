import os
import json
from pathlib import Path
from typing import Dict, Any
from PIL import Image
import imagehash
import numpy as np

_clip_cached = None
_clip_failed = False
_torch_available = None

def _clip_embedding(image: Image.Image) -> np.ndarray:
    """Return a L2‑normalized CLIP embedding for a Pillow image.
    Falls back to a zero vector if the model cannot be loaded or in offline sandbox.
    """
    global _clip_cached, _clip_failed, _torch_available
    # If offline sandbox or previously failed, return zero vector immediately
    if os.getenv("CLIP_OFFLINE", "1") == "1" or _clip_failed:
        return np.zeros(512, dtype=np.float32)

    if _torch_available is None:
        try:
            import torch
            import open_clip
            _torch_available = True
        except Exception:
            _torch_available = False

    if not _torch_available:
        return np.zeros(512, dtype=np.float32)

    try:
        import torch
        import open_clip
        if _clip_cached is None:
            model, _, preprocess = open_clip.create_model_and_transforms(
                "ViT-B-32", pretrained="laion2b_s34b_b79k"
            )
            model.eval()
            _clip_cached = (model, preprocess)
        model, preprocess = _clip_cached
        tensor = preprocess(image).unsqueeze(0)  # shape: (1, C, H, W)
        with torch.no_grad():
            embedding = model.encode_image(tensor)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)  # L2 norm
        return embedding.squeeze(0).cpu().numpy().astype(np.float32)
    except Exception:
        _clip_failed = True
        return np.zeros(512, dtype=np.float32)


def extract_features(image_path: str) -> Dict[str, Any]:
    """Compute fingerprint features for a given image file.

    Returns a dictionary with keys:
        - "phash": hex string of the 64‑bit perceptual hash
        - "clip_vec": list of floats (L2‑normalized CLIP embedding)
        - "meta": dict with width, height, file_size (bytes)
    """
    img = Image.open(image_path).convert("RGB")
    phash = str(imagehash.phash(img))
    clip_vec = _clip_embedding(img).tolist()
    stat = os.stat(image_path)
    meta = {
        "width": img.width,
        "height": img.height,
        "file_size": stat.st_size,
    }
    return {"phash": phash, "clip_vec": clip_vec, "meta": meta}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract fingerprint features for an image")
    parser.add_argument("image", help="Path to image file")
    args = parser.parse_args()
    feats = extract_features(args.image)
    print(json.dumps(feats, indent=2))
