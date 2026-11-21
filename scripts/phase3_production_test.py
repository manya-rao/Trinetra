"""
Phase 3 production test: run predict() on misflagged_01.jpg and on a copy
with EXIF stripped, using the freshly retrained model (ml/models/ai_lane.joblib).

Prints:
  - ml.predict() output for the EXIF-carrying original
  - ml.predict() output for the EXIF-stripped copy
  - New safety thresholds (from metadata.json)
"""
import io
import os
import json
import sys
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent

def main():
    # --- Load metadata / new thresholds ---
    meta_path = BASE_DIR / "ml" / "models" / "metadata.json"
    with open(meta_path, encoding="utf-8") as f:
        meta_json = json.load(f)
    new_lower = meta_json["thresholds"]["lower_real_band"]
    new_upper = meta_json["thresholds"]["upper_ai_band"]
    print(f"=== New Safety Thresholds (from metadata.json, retrained with crop-normalised extractors) ===")
    print(f"  VOID (old): lower_real=0.0366, upper_ai=0.9728")
    print(f"  NEW:        lower_real={new_lower:.4f}, upper_ai={new_upper:.4f}")
    print()

    target = BASE_DIR / "ml" / "data" / "user" / "misflagged_01.jpg"
    if not target.exists():
        print(f"ERROR: {target} not found.")
        sys.exit(1)

    from ml.predict import predict

    # =========================================================================
    # Test 1: Original EXIF-carrying photo
    # =========================================================================
    print("=" * 70)
    print("TEST 1: Original misflagged_01.jpg  (Canon EOS 200D II, full EXIF)")
    print("=" * 70)
    with Image.open(target) as img:
        img.load()  # keep EXIF in memory
        result = predict(img)
    print(f"  Band:          {result['band']}")
    print(f"  Gate:          {result['gate_triggered']}")
    print(f"  Score:         {result.get('score')}")
    print(f"  Reasons:       {[r['key'] for r in result.get('reasons', [])]}")
    print()

    # =========================================================================
    # Test 2: EXIF-stripped copy (pixel path only)
    # =========================================================================
    print("=" * 70)
    print("TEST 2: misflagged_01.jpg with EXIF stripped (pixel classifier path)")
    print("=" * 70)
    with Image.open(target) as img:
        img_rgb = img.convert("RGB")
        # Strip EXIF: save to BytesIO without exif, reload
        buf = io.BytesIO()
        img_rgb.save(buf, format="JPEG", quality=95)
        buf.seek(0)
        stripped_img = Image.open(buf)
        stripped_img.load()

    result_stripped = predict(stripped_img)
    print(f"  Band:          {result_stripped['band']}")
    print(f"  Gate:          {result_stripped['gate_triggered']}")
    print(f"  Score:         {result_stripped.get('score')}")
    print(f"  Reasons:       {[r['key'] for r in result_stripped.get('reasons', [])]}")
    print()

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    t1_verdict = result['band']
    t2_verdict = result_stripped['band']
    t1_safe = t1_verdict != "likely_ai"
    t2_safe = t2_verdict != "likely_ai"
    print(f"  Test 1 (EXIF present):  band={t1_verdict}  {'[SAFE - no false accusation]' if t1_safe else '[FALSE ACCUSATION!]'}")
    print(f"  Test 2 (EXIF stripped): band={t2_verdict}  {'[SAFE]' if t2_safe else '[FLAGGED - pixel classifier only]'}")

if __name__ == "__main__":
    main()
