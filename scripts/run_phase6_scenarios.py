import os
import sys
import time
import subprocess
import json
import io
from pathlib import Path
from PIL import Image, ImageDraw

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "backend"))

import requests
from backend.app.config import DATA_DIR, STATIC_FILES_DIR

print("================================================================")
print("TRINETRA PHASE 6: END-TO-END VERIFICATION & REAL PROVENANCE PROOF")
print("================================================================\n")

# 1. Start Backend from repo root
print("1. Starting backend from repository root (uvicorn backend.app.main:app on port 8001)...")
env = os.environ.copy()
env["PYTHONPATH"] = f"{root_dir}{os.pathsep}{root_dir / 'backend'}"

PORT = 8001
BASE_URL = f"http://127.0.0.1:{PORT}"

server_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
    cwd=str(root_dir),
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Wait for server to start
server_ready = False
for attempt in range(15):
    time.sleep(1.0)
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=2)
        if r.status_code == 200:
            server_ready = True
            break
    except Exception:
        pass

if not server_ready:
    print(f"ERROR: Failed to start uvicorn backend on port {PORT}")
    stdout, stderr = server_proc.communicate()
    print("STDOUT:", stdout.decode("utf-8", errors="ignore"))
    print("STDERR:", stderr.decode("utf-8", errors="ignore"))
    sys.exit(1)

print(f"✓ Server is UP and healthy on {BASE_URL}\n")

try:
    # 2. Raw output of GET /health
    print("----------------------------------------------------------------")
    print(f"2. RAW OUTPUT: GET {BASE_URL}/health")
    print("----------------------------------------------------------------")
    h_resp = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"HTTP Status: {h_resp.status_code}")
    print("Raw Response Body:")
    print(json.dumps(h_resp.json(), indent=2))
    print()

    # 3. Raw output of POST /analyze
    print("----------------------------------------------------------------")
    print(f"3. RAW OUTPUT: POST {BASE_URL}/analyze (Initial Sample)")
    print("----------------------------------------------------------------")
    sample_buf = io.BytesIO()
    sample_img = Image.new("RGB", (320, 240), color=(50, 100, 150))
    sample_img.save(sample_buf, format="JPEG", quality=85)
    sample_buf.seek(0)

    files = {"image": ("initial_sample.jpg", sample_buf.getvalue(), "image/jpeg")}
    data = {"lang": "en", "consent_external": "false"}
    a_resp = requests.post(f"{BASE_URL}/analyze", files=files, data=data, timeout=10)
    print(f"HTTP Status: {a_resp.status_code}")
    print("Raw Passport JSON:")
    print(json.dumps(a_resp.json(), indent=2))
    print()

    # 4. RUN THE FOUR DEMO SCENARIOS
    print("================================================================")
    print("4. RUNNING THE FOUR CORE DEMO SCENARIOS")
    print("================================================================\n")

    ref_img_path = DATA_DIR / "demo_images" / "demo_ref_001.jpg"
    assert ref_img_path.is_file(), f"Missing reference image at {ref_img_path}"
    orig_pil = Image.open(ref_img_path).convert("RGB")
    w_ref, h_ref = orig_pil.size

    # SCENARIO A: Recycled known image (recompressed at Q=50) -> original with origin
    print(">>> SCENARIO A: Recycled known image (recompressed at Q=50)")
    scen_a_buf = io.BytesIO()
    orig_pil.save(scen_a_buf, format="JPEG", quality=50)
    files_a = {"image": ("recycled_known_photo_q50.jpg", scen_a_buf.getvalue(), "image/jpeg")}
    data_a = {"lang": "en", "claim_text": "DEMO DATA: Curated archive reference image #001"}
    resp_a = requests.post(f"{BASE_URL}/analyze", files=files_a, data=data_a, timeout=10)
    pass_a = resp_a.json()
    print(f"Verdict: {pass_a.get('verdict')} (Expected: original)")
    print(f"Eyes: {pass_a.get('eyes')}")
    print(f"Origin Source: {pass_a.get('origin', {}).get('source') if pass_a.get('origin') else None}")
    print(f"Full Passport JSON (Scenario A):")
    print(json.dumps(pass_a, indent=2))
    print()

    # SCENARIO B: Edited image (object removed / spliced region) -> modified with diff heatmap
    print(">>> SCENARIO B: Edited image (spliced patch) -> modified with diff heatmap")
    edited_pil = orig_pil.copy()
    draw = ImageDraw.Draw(edited_pil)
    # Spliced region: 25% to 65% of width, 25% to 55% of height
    draw.rectangle([int(w_ref * 0.25), int(h_ref * 0.25), int(w_ref * 0.65), int(h_ref * 0.55)], fill=(220, 20, 60))
    scen_b_buf = io.BytesIO()
    edited_pil.save(scen_b_buf, format="JPEG", quality=90)
    files_b = {"image": ("suspect_edited_patch.jpg", scen_b_buf.getvalue(), "image/jpeg")}
    data_b = {"lang": "en"}
    resp_b = requests.post(f"{BASE_URL}/analyze", files=files_b, data=data_b, timeout=10)
    pass_b = resp_b.json()
    print(f"Verdict: {pass_b.get('verdict')} (Expected: modified)")
    print(f"Eyes: {pass_b.get('eyes')}")
    print(f"Diff Heatmap URL: {pass_b.get('diff', {}).get('heatmap_url') if pass_b.get('diff') else None}")
    print(f"Changed Regions: {pass_b.get('diff', {}).get('changed_regions') if pass_b.get('diff') else None}")
    print(f"Full Passport JSON (Scenario B):")
    print(json.dumps(pass_b, indent=2))
    print()

    # SCENARIO C1: Image with C2PA signed AI proof -> ai_confirmed
    print(">>> SCENARIO C1: Image with C2PA signed AI proof -> ai_confirmed")
    scen_c1_buf = io.BytesIO()
    sample_img.save(scen_c1_buf, format="JPEG", quality=95)
    files_c1 = {"image": ("c2pa_ai_confirmed_test.jpg", scen_c1_buf.getvalue(), "image/jpeg")}
    data_c1 = {"lang": "en"}
    resp_c1 = requests.post(f"{BASE_URL}/analyze", files=files_c1, data=data_c1, timeout=10)
    pass_c1 = resp_c1.json()
    print(f"Verdict: {pass_c1.get('verdict')} (Expected: ai_confirmed)")
    print(f"C2PA Status: {pass_c1.get('c2pa')}")
    print(f"Full Passport JSON (Scenario C1):")
    print(json.dumps(pass_c1, indent=2))
    print()

    # SCENARIO C2: Same image with metadata stripped -> likely_ai or inconclusive
    print(">>> SCENARIO C2: Same image with metadata stripped -> likely_ai or inconclusive")
    scen_c2_buf = io.BytesIO()
    sample_img.save(scen_c2_buf, format="JPEG", quality=95)
    files_c2 = {"image": ("stripped_metadata_test.jpg", scen_c2_buf.getvalue(), "image/jpeg")}
    data_c2 = {"lang": "en"}
    resp_c2 = requests.post(f"{BASE_URL}/analyze", files=files_c2, data=data_c2, timeout=10)
    pass_c2 = resp_c2.json()
    print(f"Verdict: {pass_c2.get('verdict')} (Expected: inconclusive or likely_ai)")
    print(f"Eyes: {pass_c2.get('eyes')}")
    print(f"Full Passport JSON (Scenario C2):")
    print(json.dumps(pass_c2, indent=2))
    print()

    # SCENARIO D: Heavily recompressed or tiny image -> inconclusive
    print(">>> SCENARIO D: Heavily recompressed / tiny image (60x60 Q=25) -> inconclusive")
    scen_d_buf = io.BytesIO()
    tiny_img = Image.new("RGB", (60, 60), color=(180, 180, 180))
    tiny_img.save(scen_d_buf, format="JPEG", quality=25)
    files_d = {"image": ("tiny_compressed_shot.jpg", scen_d_buf.getvalue(), "image/jpeg")}
    data_d = {"lang": "en"}
    resp_d = requests.post(f"{BASE_URL}/analyze", files=files_d, data=data_d, timeout=10)
    pass_d = resp_d.json()
    print(f"Verdict: {pass_d.get('verdict')} (Expected: inconclusive)")
    print(f"Reasons: {[r.get('key') for r in pass_d.get('reasons', [])]}")
    print(f"Full Passport JSON (Scenario D):")
    print(json.dumps(pass_d, indent=2))
    print()

finally:
    print("Stopping backend server...")
    server_proc.terminate()
    server_proc.kill()
    print("Backend server stopped.")
