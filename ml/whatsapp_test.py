"""
WhatsApp-style Verification Test for Trinetra Eye 3 (predict)
Demonstrates production-path verification on 3 authentic photographic images
degraded with WhatsApp-style messaging pipeline (JPEG Q70 + downscale).
"""
import io
import json
from pathlib import Path
from PIL import Image

from ml.predict import predict
from ml.eval_meta import build_meta

BASE_DIR = Path(__file__).resolve().parent
REAL_DIR = BASE_DIR / "data" / "raw" / "real"

def apply_whatsapp_simulation(img: Image.Image, scale: float = 0.70, quality: int = 70) -> Image.Image:
    """Simulates WhatsApp messaging recompression: downscale + JPEG Q70."""
    w, h = img.size
    dw = max(128, int(w * scale))
    dh = max(128, int(h * scale))
    down = img.resize((dw, dh), resample=Image.Resampling.BILINEAR)
    
    buf = io.BytesIO()
    down.convert("RGB").save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")

def run_whatsapp_test():
    real_images = sorted(list(REAL_DIR.glob("*.jpg")))[:3]
    print("=" * 70)
    print("TRINETRA EYE 3: WHATSAPP RECOMPRESSION VERIFICATION TEST")
    print("=" * 70)
    print(f"Testing {len(real_images)} authentic photographic images through WhatsApp pipeline:")
    print("Transformation: Bilinear downscale (70%) + JPEG Q70 re-encoding")
    print("-" * 70)

    for i, img_path in enumerate(real_images, 1):
        with Image.open(img_path) as orig_img:
            orig_w, orig_h = orig_img.size
            wa_img = apply_whatsapp_simulation(orig_img, scale=0.70, quality=70)
            wa_w, wa_h = wa_img.size
            
            # Production-path metadata extraction from the received file
            meta = build_meta(wa_img, jpeg_quality_hint=70.0)
            
            res = predict(wa_img, meta)
            
            print(f"\n[Test Image {i}]: {img_path.name}")
            print(f"  Original Resolution : {orig_w}x{orig_h} px")
            print(f"  WhatsApp Resolution : {wa_w}x{wa_h} px")
            print(f"  Estimated JPEG Q    : {meta['jpeg_quality']}")
            print(f"  Gate Triggered      : {res['gate_triggered']}")
            print(f"  Assigned Band       : {res['band'].upper()}")
            print(f"  Reason Keys         : {[r['key'] for r in res['reasons']]}")
            for r in res['reasons']:
                print(f"    - {r['key']}: \"{r['en']}\"")
            print(f"  Safety Guarantee    : {'SAFE (No false accusation)' if res['band'] != 'likely_ai' else 'VIOLATION'}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    run_whatsapp_test()
