"""
Metadata Feature Extractor (Eye 3)
Extracts:
1. camera EXIF present (bool)
2. known generator tags (unsigned string match in software/make/model/comment)
3. missing metadata (bool)
"""
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image
from ml.config import KNOWN_GENERATOR_KEYWORDS

def inspect_metadata(image: Image.Image, meta: Dict[str, Any] = None) -> Tuple[bool, bool, str]:
    """
    Returns:
        has_camera_exif: bool
        generator_tag_found: bool
        detected_generator_tag: str
    """
    if meta is None:
        meta = {}
        
    has_exif = meta.get("has_exif")
    explicit_gen_tag = meta.get("generator_tag")
    
    # If not provided in meta, try extracting directly from image EXIF
    if has_exif is None or explicit_gen_tag is None:
        raw_exif = image.getexif()
        if raw_exif is not None and len(raw_exif) > 0:
            if has_exif is None:
                has_exif = True
            # Scan EXIF tags (0x0131: Software, 0x010f: Make, 0x0110: Model, 0x9286: UserComment)
            software_tags = []
            for tag_id in [0x0131, 0x010f, 0x0110, 0x9286, 0x013b]:
                val = raw_exif.get(tag_id)
                if val:
                    software_tags.append(str(val).lower())
            joined = " ".join(software_tags)
            for kw in KNOWN_GENERATOR_KEYWORDS:
                if kw in joined:
                    explicit_gen_tag = kw
                    break
        else:
            if has_exif is None:
                has_exif = False

    has_camera_exif = bool(has_exif)
    gen_tag_str = str(explicit_gen_tag) if explicit_gen_tag else ""
    generator_tag_found = len(gen_tag_str) > 0
    
    return has_camera_exif, generator_tag_found, gen_tag_str

def extract_metadata_features(image: Image.Image, meta: Dict[str, Any] = None) -> np.ndarray:
    """
    Returns a 1D vector of shape (3,):
    [has_camera_exif_float, missing_metadata_float, generator_tag_flag_float]
    """
    has_cam, gen_found, _ = inspect_metadata(image, meta)
    missing_meta = not has_cam
    return np.array([
        1.0 if has_cam else 0.0,
        1.0 if missing_meta else 0.0,
        1.0 if gen_found else 0.0
    ], dtype=np.float32)
