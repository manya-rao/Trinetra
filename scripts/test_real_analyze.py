import subprocess
import time
import sys
import requests
from PIL import Image
import io

print("1. Starting backend server from repo root...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

time.sleep(3.5)

try:
    print("2. Probing GET http://127.0.0.1:8000/health...")
    h_res = requests.get("http://127.0.0.1:8000/health", timeout=5)
    print("Health Status:", h_res.status_code, h_res.json())

    print("3. Testing real POST /analyze round trip with generated test image...")
    img = Image.new("RGB", (300, 300), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)

    files = {"image": ("test_verify_phase4.jpg", buf, "image/jpeg")}
    data = {"lang": "en"}
    res = requests.post("http://127.0.0.1:8000/analyze", files=files, data=data, timeout=10)
    print("Analyze Status:", res.status_code)
    passport = res.json()
    print("Passport ID:", passport.get("id"))
    print("Verdict:", passport.get("verdict"))
    print("Confidence Band:", passport.get("confidence_band"))
    print("Eyes Status:", passport.get("eyes"))
    print("Scope Note:", passport.get("scope_note"))
    print("Reasons count:", len(passport.get("reasons", [])))

    if res.status_code == 200 and "id" in passport and "verdict" in passport:
        print("\nSUCCESS: Real /analyze round trip completed against backend!")
    else:
        print("\nFAILURE: Unexpected response")

finally:
    proc.terminate()
    proc.kill()
