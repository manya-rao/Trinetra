"""
Tests for POST /analyze in MOCK=1 mode, GET /passport/{id},
GET /p/{id}, and GET /passport/{id}/card.png.
"""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app
from app import config as cfg

@pytest.fixture(autouse=True)
def enable_mock_mode():
    old = cfg.MOCK_MODE
    cfg.MOCK_MODE = True
    yield
    cfg.MOCK_MODE = old

client = TestClient(app)


def create_dummy_image_bytes():
    buf = io.BytesIO()
    img = Image.new("RGB", (400, 400), color=(120, 150, 180))
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def test_mock_analyze_original():
    img_bytes = create_dummy_image_bytes()
    response = client.post(
        "/analyze",
        files={"image": ("my_archive_original_photo.jpg", img_bytes, "image/jpeg")},
        data={"lang": "en", "consent_external": "false"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "original"
    assert data["eyes"]["origin"] == "found"
    assert data["eyes"]["change"] == "none"
    assert data["demo_data"] is True


def test_mock_analyze_modified():
    img_bytes = create_dummy_image_bytes()
    response = client.post(
        "/analyze",
        files={"image": ("suspect_modified_scene.jpg", img_bytes, "image/jpeg")},
        data={"lang": "en", "consent_external": "true"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "modified"
    assert data["eyes"]["origin"] == "found"
    assert data["eyes"]["change"] == "found"
    assert data["diff"] is not None
    assert len(data["diff"]["changed_regions"]) > 0


def test_mock_analyze_ai_confirmed():
    img_bytes = create_dummy_image_bytes()
    response = client.post(
        "/analyze",
        files={"image": ("c2pa_ai_confirmed_test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "ai_confirmed"
    assert data["eyes"]["synthesis"] == "confirmed"
    assert data["c2pa"]["status"] == "valid"
    assert data["c2pa"]["ai_generated"] is True


def test_mock_analyze_likely_ai():
    img_bytes = create_dummy_image_bytes()
    response = client.post(
        "/analyze",
        files={"image": ("generated_portrait_likely_ai.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "likely_ai"
    assert data["eyes"]["synthesis"] == "likely"
    assert data["confidence_band"] in ("high", "medium", "low")


def test_mock_analyze_inconclusive_default():
    img_bytes = create_dummy_image_bytes()
    response = client.post(
        "/analyze",
        files={"image": ("random_blurry_inconclusive.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "inconclusive"
    assert data["eyes"]["synthesis"] in ("inconclusive", "none")


def test_passport_lifecycle_and_presentation():
    # 1. Analyze an image
    img_bytes = create_dummy_image_bytes()
    res = client.post(
        "/analyze",
        files={"image": ("sample_modified_event.jpg", img_bytes, "image/jpeg")}
    )
    assert res.status_code == 200
    passport_id = res.json()["id"]

    # 2. Retrieve via GET /passport/{id}
    res_get = client.get(f"/passport/{passport_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == passport_id

    # 3. Retrieve HTML view via GET /p/{id}
    res_html = client.get(f"/p/{passport_id}?lang=en")
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    assert "TRINETRA" in res_html.text
    assert passport_id in res_html.text

    # 4. Retrieve Share Card via GET /passport/{id}/card.png
    res_card = client.get(f"/passport/{passport_id}/card.png?lang=en")
    assert res_card.status_code == 200
    assert res_card.headers["content-type"] == "image/png"
    card_img = Image.open(io.BytesIO(res_card.content))
    assert card_img.size == (1080, 1350)


def test_match_hash_endpoint():
    # Known hash
    res_match = client.post("/match_hash", json={"phash": "demo_test_hash"})
    assert res_match.status_code == 200
    assert res_match.json()["matched"] is True
    assert res_match.json()["origin_summary"] is not None

    # Unknown hash
    res_nomatch = client.post("/match_hash", json={"phash": "1234567890abcdef"})
    assert res_nomatch.status_code == 200
    assert res_nomatch.json()["matched"] is False
    assert res_nomatch.json()["origin_summary"] is None


def test_static_files_serving():
    res = client.get("/files/thumb_demo_original.jpg")
    assert res.status_code == 200


def test_analyze_e2e_not_in_index():
    """(i) Image NOT in index -> AI lane result with origin=null and eyes.origin='none'."""
    buf = io.BytesIO()
    # Random pattern distinct from index
    img = Image.new("RGB", (320, 240), color=(34, 198, 221))
    img.save(buf, format="JPEG")
    res = client.post(
        "/analyze",
        files={"image": ("unseen_web_photo_xyz.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["origin"] is None
    assert data["eyes"]["origin"] == "none"
    assert data["eyes"]["synthesis"] in ("inconclusive", "likely", "none")
    # Clarification: reasons state image has no known origin in index
    reason_keys = [r["key"] for r in data["reasons"]]
    assert "no_origin_match" in reason_keys


def test_analyze_e2e_in_index_recompressed():
    """(ii) Image IN index (recompressed/screenshotted) -> origin lane."""
    from pathlib import Path
    demo_ref = Path(__file__).resolve().parents[1] / "data" / "demo_images" / "demo_ref_001.jpg"
    assert demo_ref.is_file(), "Demo reference image demo_ref_001.jpg must exist"
    
    img = Image.open(demo_ref).convert("RGB")
    buf = io.BytesIO()
    # Recompress slightly
    img.save(buf, format="JPEG", quality=75)
    
    res = client.post(
        "/analyze",
        files={"image": ("recompressed_query_from_chat.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["origin"] is not None
    assert data["eyes"]["origin"] == "found"
    assert "DEMO DATA" in data["origin"]["claim_en"]
    assert data["verdict"] in ("original", "modified")


def test_analyze_e2e_c2pa_ai_proof():
    """(iii) Image with C2PA AI proof -> ai_confirmed."""
    buf = io.BytesIO()
    img = Image.new("RGB", (200, 200), color=(90, 80, 110))
    img.save(buf, format="JPEG")
    res = client.post(
        "/analyze",
        files={"image": ("provenance_signed_ai_confirmed_c2pa.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] == "ai_confirmed"
    assert data["eyes"]["synthesis"] == "confirmed"
    assert data["c2pa"]["status"] == "valid"
    assert data["c2pa"]["ai_generated"] is True


def test_analyze_empty_or_missing_index_fallback():
    """Requirement 5: Index works when EMPTY or missing; every image goes to AI lane."""
    import backend.origin_match as om
    from pathlib import Path
    
    orig_db = om.INDEX_DB
    try:
        # Point to a non-existent sqlite db file
        om.INDEX_DB = Path("non_existent_empty_index.sqlite")
        buf = io.BytesIO()
        img = Image.new("RGB", (150, 150), color=(10, 20, 30))
        img.save(buf, format="JPEG")
        res = client.post(
            "/analyze",
            files={"image": ("standalone_test_image.jpg", buf.getvalue(), "image/jpeg")}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["origin"] is None
        assert data["eyes"]["origin"] == "none"
        assert data["eyes"]["synthesis"] in ("inconclusive", "likely", "none")
    finally:
        om.INDEX_DB = orig_db


