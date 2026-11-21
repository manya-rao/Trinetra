import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "backend"))

from fastapi.testclient import TestClient
from app.main import app
from PIL import Image
import io

print("--- TESTING BACKEND IN-PROCESS ASGI PIPELINE ---")
client = TestClient(app)

# 1. Health check
res = client.get("/health")
print("1. GET /health ->", res.status_code, res.json())

# 2. Analyze round trip with JPEG image
img = Image.new("RGB", (300, 300), color=(100, 150, 200))
buf = io.BytesIO()
img.save(buf, format="JPEG", quality=90)
buf.seek(0)

files = {"image": ("test_verify_phase4.jpg", buf.getvalue(), "image/jpeg")}
data = {"lang": "en", "hash_only": "false", "consent_external": "false"}

print("2. POST /analyze (in-process real ASGI pipeline)...")
res = client.post("/analyze", files=files, data=data)
print("Analyze HTTP Status:", res.status_code)
passport = res.json()
print("Passport ID:", passport.get("id"))
print("Verdict:", passport.get("verdict"))
print("Confidence Band:", passport.get("confidence_band"))
print("Eyes Status:", passport.get("eyes"))
print("Reasons:", passport.get("reasons"))
print("Scope Note:", passport.get("scope_note"))
print("External Search:", passport.get("external_search"))
print("Demo Data Flag:", passport.get("demo_data"))

assert res.status_code == 200, "Expected status 200"
assert "id" in passport, "Expected passport id in response"
assert "verdict" in passport, "Expected verdict in response"
print("\n✓ SUCCESS: In-process ASGI /analyze round trip verified successfully!")
