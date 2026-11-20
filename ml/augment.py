"""
WhatsApp-Style Realistic Image Degradation & Augmentation Pipeline (Eye 3)
Simulates social media recompression, messaging downscales, screenshots, and camera noise:
1. JPEG recompression: quality 90, 70, 50
2. Downscale: 50%, 25% (with bicubic upsample back)
3. Center & edge crops
4. Screenshot-style: padded borders + resample
5. Mild Gaussian blur
6. Additive sensor noise
"""
import io
import random
import numpy as np
from PIL import Image, ImageFilter, ImageOps
from typing import List, Callable

def apply_jpeg_compression(img: Image.Image, quality: int) -> Image.Image:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")

def apply_downscale_upscale(img: Image.Image, scale: float) -> Image.Image:
    w, h = img.size
    dw = max(32, int(w * scale))
    dh = max(32, int(h * scale))
    down = img.resize((dw, dh), resample=Image.Resampling.BILINEAR)
    return down.resize((w, h), resample=Image.Resampling.BICUBIC)

def apply_crop(img: Image.Image, crop_fraction: float = 0.85, mode: str = "center") -> Image.Image:
    w, h = img.size
    cw, ch = int(w * crop_fraction), int(h * crop_fraction)
    if mode == "center":
        left = (w - cw) // 2
        top = (h - ch) // 2
    else:  # edge / corner crop
        left = random.choice([0, w - cw])
        top = random.choice([0, h - ch])
    cropped = img.crop((left, top, left + cw, top + ch))
    return cropped.resize((w, h), resample=Image.Resampling.BICUBIC)

def apply_screenshot_effect(img: Image.Image) -> Image.Image:
    """Simulates taking a mobile screenshot with border padding and recompression."""
    w, h = img.size
    border_px = max(8, int(min(w, h) * 0.05))
    padded = ImageOps.expand(img, border=border_px, fill=(18, 18, 22))
    resampled = padded.resize((w, h), resample=Image.Resampling.BILINEAR)
    return apply_jpeg_compression(resampled, quality=75)

def apply_blur(img: Image.Image, radius: float = 1.0) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius=radius))

def apply_mild_noise(img: Image.Image, std: float = 6.0) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    noise = np.random.normal(0, std, arr.shape)
    noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy)

# Benchmark evaluation transformations (for robustness testing in evaluate.py)
DEGRADATION_SUITE = {
    "clean": lambda img: img,
    "jpeg_q90": lambda img: apply_jpeg_compression(img, 90),
    "jpeg_q70": lambda img: apply_jpeg_compression(img, 70),
    "jpeg_q50": lambda img: apply_jpeg_compression(img, 50),
    "downscale_50": lambda img: apply_downscale_upscale(img, 0.50),
    "downscale_25": lambda img: apply_downscale_upscale(img, 0.25),
    "crop_center": lambda img: apply_crop(img, 0.80, "center"),
    "crop_edge": lambda img: apply_crop(img, 0.80, "edge"),
    "screenshot": apply_screenshot_effect,
    "blur": lambda img: apply_blur(img, 1.2),
    "sensor_noise": lambda img: apply_mild_noise(img, 6.0)
}

def random_augment(img: Image.Image) -> Image.Image:
    """Randomly applies 1 or 2 WhatsApp-style degradations for training data augmentation."""
    ops = [
        lambda x: apply_jpeg_compression(x, random.choice([85, 75, 60])),
        lambda x: apply_downscale_upscale(x, random.uniform(0.4, 0.8)),
        lambda x: apply_crop(x, random.uniform(0.75, 0.95), random.choice(["center", "edge"])),
        lambda x: apply_blur(x, random.uniform(0.5, 1.2)),
        lambda x: apply_mild_noise(x, random.uniform(3.0, 7.0)),
        apply_screenshot_effect
    ]
    # 50% chance of applying 1 degradation, 25% chance of applying 2, 25% left clean
    roll = random.random()
    if roll < 0.25:
        return img
    elif roll < 0.75:
        return random.choice(ops)(img)
    else:
        op1, op2 = random.sample(ops, 2)
        return op2(op1(img))
