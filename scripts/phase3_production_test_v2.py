"""
Phase 3 production test: run predict() on misflagged_01.jpg and on a copy
with EXIF stripped. Verifies the camera-EXIF guardrail is active after retraining.
"""
import io, json, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from ml.predict import predict
from PIL import Image

meta_path = BASE / "ml" / "models" / "metadata.json"
meta_json = json.loads(meta_path.read_text())
new_lower = meta_json["thresholds"]["lower_real_band"]
new_upper = meta_json["thresholds"]["upper_ai_band"]
print("=== New Safety Thresholds (retrained with crop-normalised extractors) ===")
print(f"  VOID (old): lower_real=0.0366, upper_ai=0.9728")
print(f"  NEW:        lower_real={new_lower:.4f}, upper_ai={new_upper:.4f}")
print()

target = BASE / "ml" / "data" / "user" / "misflagged_01.jpg"
if not target.exists():
    print(f"ERROR: {target} not found.")
    sys.exit(1)

# TEST 1: original with EXIF
print("=" * 70)
print("TEST 1: misflagged_01.jpg  (Canon EOS 200D II, full EXIF)")
print("=" * 70)
with Image.open(target) as img:
    img.load()
    result = predict(img)
print(f"  Band:    {result['band']}")
print(f"  Gate:    {result['gate_triggered']}")
print(f"  Score:   {result.get('score')}")
reasons1 = [r["key"] for r in result.get("reasons", [])]
print(f"  Reasons: {reasons1}")
print()

# TEST 2: EXIF stripped copy
print("=" * 70)
print("TEST 2: misflagged_01.jpg  EXIF stripped (pixel classifier only)")
print("=" * 70)
with Image.open(target) as img:
    img_rgb = img.convert("RGB")
    buf = io.BytesIO()
    img_rgb.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    stripped = Image.open(buf)
    stripped.load()
result2 = predict(stripped)
print(f"  Band:    {result2['band']}")
print(f"  Gate:    {result2['gate_triggered']}")
print(f"  Score:   {result2.get('score')}")
reasons2 = [r["key"] for r in result2.get("reasons", [])]
print(f"  Reasons: {reasons2}")
print()

# SUMMARY
print("=" * 70)
print("SUMMARY")
print("=" * 70)
t1 = result["band"]
t2 = result2["band"]
safe1 = "SAFE - no false accusation" if t1 != "likely_ai" else "FALSE ACCUSATION!"
safe2 = "SAFE" if t2 != "likely_ai" else "FLAGGED - pixel classifier only"
print(f"  Test 1 (EXIF present):  band={t1}  [{safe1}]")
print(f"  Test 2 (EXIF stripped): band={t2}  [{safe2}]")
