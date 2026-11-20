import os
import csv
import json
import sqlite3
from pathlib import Path
from typing import List
from PIL import Image, ImageDraw

# Optional FAISS import – fallback to stub
try:
    import faiss
    import numpy as np
    _faiss_available = True
except Exception:
    _faiss_available = False

BASE_DIR = Path(__file__).resolve().parent  # backend/
DEMO_IMG_DIR = BASE_DIR / "data" / "demo_images"
DEMO_CSV = BASE_DIR / "data" / "demo_index.csv"
INDEX_DB = BASE_DIR / "data" / "index.sqlite"
FAISS_IDX = BASE_DIR / "data" / "faiss.idx"

def _ensure_dirs():
    DEMO_IMG_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DB.parent.mkdir(parents=True, exist_ok=True)

def _ensure_db():
    _ensure_dirs()
    conn = sqlite3.connect(INDEX_DB)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            phash TEXT NOT NULL,
            clip_vec BLOB NOT NULL,
            meta TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn

def _generate_demo_images_if_needed(count: int = 64):
    """
    Generate neutral demo images with deterministic shapes/colors
    if demo_images directory has fewer than count images.
    """
    _ensure_dirs()
    existing = list(DEMO_IMG_DIR.glob("*.jpg"))
    if len(existing) >= count:
        return

    csv_rows = []
    for i in range(1, count + 1):
        fn = f"demo_ref_{i:03d}.jpg"
        img_path = DEMO_IMG_DIR / fn
        if not img_path.exists():
            # Generate deterministic distinct pattern
            r = (i * 37) % 256
            g = (i * 73) % 256
            b = (i * 109) % 256
            img = Image.new("RGB", (800, 600), color=(r, g, b))
            draw = ImageDraw.Draw(img)
            # Draw shapes to give varied pHash
            draw.rectangle([(50, 50), (250, 250)], fill=((r + 80) % 256, (g + 40) % 256, (b + 120) % 256))
            draw.ellipse([(350, 200), (550, 400)], fill=((r + 150) % 256, (g + 180) % 256, (b + 60) % 256))
            draw.polygon([(600, 500), (700, 300), (750, 550)], fill=((r + 40) % 256, (g + 110) % 256, (b + 200) % 256))
            img.save(img_path, format="JPEG", quality=90)

        csv_rows.append({
            "filename": fn,
            "source_url": f"https://commons.wikimedia.org/wiki/File:DEMO_Archive_{i:03d}.jpg",
            "license": "CC0 (DEMO DATA)",
            "claim_en": f"DEMO DATA: Curated archive reference image #{i:03d}",
            "claim_hi": f"डेमो डेटा: क्यूरेटेड संग्रह संदर्भ छवि #{i:03d}",
            "first_seen_date": f"2023-{(i % 12) + 1:02d}-15",
            "demo": "True"
        })

    with open(DEMO_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "filename", "source_url", "license", "claim_en", "claim_hi", "first_seen_date", "demo"
        ])
        writer.writeheader()
        writer.writerows(csv_rows)

def _store_image(conn, img_id: str, filename: str, phash: str, clip_vec: List[float], meta: dict):
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO images (id, filename, phash, clip_vec, meta) VALUES (?, ?, ?, ?, ?)",
        (img_id, filename, phash, json.dumps(clip_vec).encode('utf-8'), json.dumps(meta)),
    )
    conn.commit()

def _build_faiss(embeddings: List[List[float]]):
    if not _faiss_available or not embeddings:
        return None
    import numpy as np
    dim = len(embeddings[0])
    index = faiss.IndexFlatIP(dim)
    index.add(np.array(embeddings, dtype='float32'))
    return index

def main():
    from fingerprint import extract_features

    _generate_demo_images_if_needed(count=64)
    conn = _ensure_db()
    embeddings = []
    ids = []

    # Map CSV metadata
    csv_meta = {}
    if DEMO_CSV.is_file():
        with open(DEMO_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_meta[row["filename"].strip()] = row

    for img_path in sorted(DEMO_IMG_DIR.glob("*.jpg")):
        filename = img_path.name
        try:
            feats = extract_features(str(img_path))
        except Exception as e:
            print(f"Skipping {filename}: {e}")
            continue

        row_info = csv_meta.get(filename, {})
        merged_meta = dict(feats["meta"])
        merged_meta.update({
            "source": row_info.get("source_url", "Wikimedia Commons (Public Domain / CC - DEMO DATA)"),
            "date": row_info.get("first_seen_date", "2023-01-01"),
            "factcheck_url": row_info.get("source_url", "https://commons.wikimedia.org/wiki/File:DEMO_Archive.jpg"),
            "claim_en": row_info.get("claim_en", f"DEMO DATA: Verified source photo ({filename})"),
            "claim_hi": row_info.get("claim_hi", f"डेमो डेटा: सत्यापित स्रोत फ़ोटो ({filename})"),
            "thumb_url": f"/files/{filename}"
        })

        img_id = f"demo-{filename}"
        _store_image(conn, img_id, filename, feats["phash"], feats["clip_vec"], merged_meta)
        embeddings.append(feats["clip_vec"])
        ids.append(img_id)

    conn.close()

    # Build FAISS index if possible
    if _faiss_available and embeddings:
        try:
            index = _build_faiss(embeddings)
            if index is not None:
                faiss.write_index(index, str(FAISS_IDX))
                with open(str(FAISS_IDX) + ".ids", "w", encoding="utf-8") as idfile:
                    for i in ids:
                        idfile.write(i + "\n")
                print(f"FAISS index written to {FAISS_IDX}")
        except Exception as e:
            print(f"FAISS build skipped: {e}")
    else:
        print("FAISS not available or skipped.")

    print(f"SQLite index successfully populated at {INDEX_DB} with {len(ids)} demo records.")

if __name__ == "__main__":
    main()
