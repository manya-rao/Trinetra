"""
Crop Normalisation Utility for Trinetra Eye 3 (ai_lane).
Extracts fixed-size crops at training resolution (384x384) to achieve scale-invariance.
Ensures a 12-megapixel camera photo and a 384px training image produce comparable features.
"""
from typing import List
from PIL import Image

def get_fixed_crops(image: Image.Image, crop_size: int = 384, max_crops: int = 5) -> List[Image.Image]:
    """
    Extracts fixed-size crops (crop_size x crop_size) from an image.
    If image is smaller than crop_size in either dimension, scales proportionally
    and center-crops to (crop_size, crop_size).
    For larger images, extracts center crop and 4 quadrant crops.
    """
    w, h = image.size

    # 1. Image smaller than or equal to crop_size in either dimension
    if w <= crop_size or h <= crop_size:
        scale = max(crop_size / w, crop_size / h)
        new_w = max(crop_size, int(round(w * scale)))
        new_h = max(crop_size, int(round(h * scale)))
        resized = image.resize((new_w, new_h), Image.Resampling.BICUBIC)
        left = (new_w - crop_size) // 2
        top = (new_h - crop_size) // 2
        return [resized.crop((left, top, left + crop_size, top + crop_size))]

    crops = []
    # 2. Center crop
    cx = (w - crop_size) // 2
    cy = (h - crop_size) // 2
    crops.append(image.crop((cx, cy, cx + crop_size, cy + crop_size)))

    # 3. Four quadrant crops (offset by 15% from borders)
    qx1 = max(0, int(w * 0.15))
    qy1 = max(0, int(h * 0.15))
    qx2 = min(w - crop_size, int(w * 0.85 - crop_size))
    qy2 = min(h - crop_size, int(h * 0.85 - crop_size))

    if qx2 > qx1 and qy2 > qy1:
        crops.append(image.crop((qx1, qy1, qx1 + crop_size, qy1 + crop_size)))
        crops.append(image.crop((qx2, qy1, qx2 + crop_size, qy1 + crop_size)))
        crops.append(image.crop((qx1, qy2, qx1 + crop_size, qy2 + crop_size)))
        crops.append(image.crop((qx2, qy2, qx2 + crop_size, qy2 + crop_size)))

    return crops[:max_crops]
