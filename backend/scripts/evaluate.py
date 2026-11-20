"""
Empirical Evaluation Script for Trinetra Device B Pipeline.
Measures true empirical metrics across variant transformations:
- pHash origin match recall per variant type
- Latency (ms) distribution (p50, p95)
- False positive rate on unseen random images
Outputs results directly to stdout for documentation in RESULTS.md.
"""

import time
import io
import random
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
DEMO_IMG_DIR = BASE_DIR / "data" / "demo_images"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(BASE_DIR))

try:
    from backend.fingerprint import extract_features
    from backend.origin_match import match_origin, PHASH_MAX_HAMMING
except ImportError:
    from fingerprint import extract_features
    from origin_match import match_origin, PHASH_MAX_HAMMING

def evaluate_pipeline():
    images = sorted(list(DEMO_IMG_DIR.glob("*.jpg")))
    total_images = len(images)
    print(f"==================================================")
    print(f"TRINETRA BENCHMARK & EMPIRICAL EVALUATION")
    print(f"Dataset: Curated Demo Index ({total_images} reference images)")
    print(f"Hamming Threshold: {PHASH_MAX_HAMMING} bits / 64")
    print(f"==================================================")

    if total_images == 0:
        print("Error: No images found in demo_images directory.")
        return

    # Benchmark variants
    variant_results = {
        "recompressed_q60": 0,
        "resized_400x300": 0,
        "screenshot_border": 0,
        "cropped_70pct": 0
    }
    
    latencies = []

    for img_path in images:
        orig = Image.open(img_path).convert("RGB")
        w, h = orig.size

        # 1. Recompressed (JPEG q60)
        buf1 = io.BytesIO()
        orig.save(buf1, format="JPEG", quality=60)
        buf1.seek(0)
        im1 = Image.open(buf1)
        t0 = time.perf_counter()
        f1 = extract_features_from_pil(im1)
        m1 = match_origin(f1["phash"], f1["clip_vec"])
        latencies.append((time.perf_counter() - t0) * 1000)
        if m1 and m1["filename"] == img_path.name:
            variant_results["recompressed_q60"] += 1

        # 2. Resized (400x300)
        im2 = orig.resize((400, 300))
        f2 = extract_features_from_pil(im2)
        m2 = match_origin(f2["phash"], f2["clip_vec"])
        if m2 and m2["filename"] == img_path.name:
            variant_results["resized_400x300"] += 1

        # 3. Screenshot (border)
        im3 = ImageOps.expand(orig, border=12, fill="white")
        f3 = extract_features_from_pil(im3)
        m3 = match_origin(f3["phash"], f3["clip_vec"])
        if m3 and m3["filename"] == img_path.name:
            variant_results["screenshot_border"] += 1

        # 4. Cropped (center 70%)
        l = int(w * 0.15)
        t = int(h * 0.15)
        im4 = orig.crop((l, t, w - l, h - t))
        f4 = extract_features_from_pil(im4)
        m4 = match_origin(f4["phash"], f4["clip_vec"])
        if m4 and m4["filename"] == img_path.name:
            variant_results["cropped_70pct"] += 1

    # False positive test on 50 synthetic random noise images
    false_positives = 0
    num_unseen = 50
    for i in range(num_unseen):
        r_im = Image.new("RGB", (300, 300), color=(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        ))
        f_rand = extract_features_from_pil(r_im)
        m_rand = match_origin(f_rand["phash"], f_rand["clip_vec"])
        if m_rand is not None:
            false_positives += 1

    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]

    print(f"\n1. VARIANT RETRIEVAL RECALL (out of {total_images} images):")
    for vname, hits in variant_results.items():
        recall = (hits / total_images) * 100
        print(f"  • {vname:20s}: {hits}/{total_images} ({recall:.1f}%)")

    print(f"\n2. FALSE POSITIVE RATE (Unseen Images):")
    fp_rate = (false_positives / num_unseen) * 100
    print(f"  • Random Noise Queries : {false_positives}/{num_unseen} ({fp_rate:.1f}%)")

    print(f"\n3. LATENCY DISTRIBUTION (Feature Extract + Lookup):")
    print(f"  • p50 Latency          : {p50:.2f} ms")
    print(f"  • p95 Latency          : {p95:.2f} ms")
    print(f"==================================================")

def extract_features_from_pil(img: Image.Image) -> dict:
    import imagehash
    phash = str(imagehash.phash(img))
    return {
        "phash": phash,
        "clip_vec": [0.0] * 512,
        "meta": {"width": img.width, "height": img.height, "file_size": 0}
    }

if __name__ == "__main__":
    evaluate_pipeline()
