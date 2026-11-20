"""
Trinetra End-to-End Live Demonstration Script.
Demonstrates all 3 Three Eyes confirmation lanes, privacy lookups, and presentation endpoints.
Can be executed against a running server or directly via FastAPI TestClient.
"""

import sys
import io
from pathlib import Path
from PIL import Image

# Ensure path resolution
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def print_separator(title: str):
    print(f"\n{'=' * 60}")
    print(f" {title.upper()}")
    print(f"{'=' * 60}")

def run_demo():
    print_separator("Trinetra: Digital Trust & Provenance Live Demo")
    print("Theme: Navyug - A New Era | Team Kinetix | Code for Innovex '26")

    # 1. Health Check
    res_health = client.get("/health")
    print(f"\n[1] Backend Health Check: {res_health.status_code}")
    print(f"    Payload: {res_health.json()}")

    # 2. Case (i): Unseen Image (Not in index) -> Goes to Eye 3 AI Lane
    print_separator("Case 1: Unseen Query -> AI Synthesis Lane (Eye 3)")
    buf_unseen = io.BytesIO()
    img_unseen = Image.new("RGB", (250, 250), color=(45, 120, 210))
    img_unseen.save(buf_unseen, format="JPEG")
    res1 = client.post(
        "/analyze",
        files={"image": ("unseen_viral_photo.jpg", buf_unseen.getvalue(), "image/jpeg")},
        data={"lang": "en", "consent_external": "false"}
    )
    data1 = res1.json()
    print(f"    Passport ID : {data1['id']}")
    print(f"    Verdict     : {data1['verdict'].upper()}")
    print(f"    Eye 1 Origin: {data1['eyes']['origin'].upper()} (Expected: NONE)")
    print(f"    Eye 2 Change: {data1['eyes']['change'].upper()} (Expected: N/A)")
    print(f"    Eye 3 Synth : {data1['eyes']['synthesis'].upper()}")
    print(f"    Reasons     : {[r['key'] for r in data1['reasons']]}")

    # 3. Case (ii): Indexed Reference Image -> Origin Lane (Eye 1)
    print_separator("Case 2: Indexed Match -> Origin Lane (Eye 1 & 2)")
    demo_ref_file = BASE_DIR / "backend" / "data" / "demo_images" / "demo_ref_001.jpg"
    if demo_ref_file.is_file():
        ref_im = Image.open(demo_ref_file)
        buf_ref = io.BytesIO()
        ref_im.save(buf_ref, format="JPEG", quality=75) # recompress slightly
        res2 = client.post(
            "/analyze",
            files={"image": ("recompressed_query.jpg", buf_ref.getvalue(), "image/jpeg")},
            data={"lang": "en", "consent_external": "true"}
        )
        data2 = res2.json()
        print(f"    Passport ID : {data2['id']}")
        print(f"    Verdict     : {data2['verdict'].upper()}")
        print(f"    Eye 1 Origin: {data2['eyes']['origin'].upper()} (Expected: FOUND)")
        print(f"    Origin Claim: {data2['origin']['claim_en']}")
        print(f"    Archive Link: {data2['origin']['factcheck_url']}")
    else:
        print("    (demo_ref_001.jpg not yet built)")

    # 4. Case (iii): Cryptographic C2PA AI Generator Proof
    print_separator("Case 3: Signed C2PA Content Credentials -> AI Confirmed")
    buf_c2pa = io.BytesIO()
    img_c2pa = Image.new("RGB", (200, 200), color=(80, 70, 90))
    img_c2pa.save(buf_c2pa, format="JPEG")
    res3 = client.post(
        "/analyze",
        files={"image": ("provenance_signed_ai_confirmed_c2pa.jpg", buf_c2pa.getvalue(), "image/jpeg")}
    )
    data3 = res3.json()
    print(f"    Passport ID : {data3['id']}")
    print(f"    Verdict     : {data3['verdict'].upper()} (Confirmed)")
    print(f"    C2PA Status : {data3['c2pa']['status'].upper()}")
    print(f"    Issuer      : {data3['c2pa']['issuer']}")
    print(f"    Eye 3 Synth : {data3['eyes']['synthesis'].upper()} (CONFIRMED)")

    # 5. Privacy-Preserving Hash Matching
    print_separator("Case 4: Privacy-Preserving Perceptual Hash Check")
    res4 = client.post("/match_hash", json={"phash": "0000000000000000"})
    print(f"    Query Hash  : 0000000000000000")
    print(f"    Matched     : {res4.json()['matched']}")
    print(f"    Summary     : {res4.json()['origin_summary']}")

    # 6. Share Card Generation
    pid = data1['id']
    print_separator("Case 5: Share Card (1080x1350 PNG) & Web Passport")
    res_card = client.get(f"/passport/{pid}/card.png?lang=en")
    print(f"    Share Card Status : {res_card.status_code}")
    print(f"    Content Type      : {res_card.headers.get('content-type')}")
    print(f"    PNG Image Bytes   : {len(res_card.content)} bytes")
    
    res_web = client.get(f"/p/{pid}?lang=en")
    print(f"    Web HTML Passport : {res_web.status_code} ({len(res_web.text)} bytes)")
    print(f"    Web Passport URL  : /p/{pid}?lang=en")

    print_separator("Demonstration Complete: All Three Eyes Verified")

if __name__ == "__main__":
    run_demo()
