import os
import sqlite3
import json
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

# Optional FAISS import – fallback stub
try:
    import faiss
    _faiss_available = True
except Exception:
    _faiss_available = False

BASE_DIR = Path(__file__).resolve().parent  # backend/
INDEX_DB = BASE_DIR / "data" / "index.sqlite"
FAISS_IDX = BASE_DIR / "data" / "faiss.idx"
FAISS_IDS = FAISS_IDX.with_name(FAISS_IDX.name + ".ids")

# Thresholds (as per spec)
PHASH_MAX_HAMMING = 10  # out of 64 bits
CLIP_MIN_SIM = 0.85  # cosine similarity (inner product after L2 norm)

def _phash_hamming(ph1: str, ph2: str) -> int:
    try:
        i1 = int(ph1, 16)
        i2 = int(ph2, 16)
        return bin(i1 ^ i2).count('1')
    except Exception:
        return 64

def _load_faiss_index():
    if not _faiss_available or not FAISS_IDX.is_file():
        return None, []
    try:
        index = faiss.read_index(str(FAISS_IDX))
        ids = []
        if FAISS_IDS.is_file():
            with open(FAISS_IDS, "r", encoding="utf-8") as f:
                for line in f:
                    ids.append(line.strip())
        return index, ids
    except Exception:
        return None, []

def _query_sqlite(phash: str) -> list[Dict[str, Any]]:
    if not INDEX_DB.is_file():
        return []
    try:
        conn = sqlite3.connect(INDEX_DB)
        cur = conn.cursor()
        cur.execute("SELECT id, filename, phash, clip_vec, meta FROM images")
        rows = []
        for row in cur.fetchall():
            try:
                meta = json.loads(row[4]) if row[4] else {}
            except Exception:
                meta = {}
            clip_bytes = row[3]
            try:
                clip_list = json.loads(clip_bytes.decode('utf-8') if isinstance(clip_bytes, bytes) else clip_bytes)
            except Exception:
                clip_list = [0.0] * 512
            rec = {
                "id": row[0],
                "filename": row[1],
                "phash": row[2],
                "clip_vec": clip_list,
                "meta": meta,
                "source": meta.get("source", "Trinetra Curated Index (DEMO DATA)"),
                "date": meta.get("date", "2023-01-01"),
                "factcheck_url": meta.get("factcheck_url", "https://commons.wikimedia.org/wiki/File:DEMO_Archive.jpg"),
                "claim_en": meta.get("claim_en", "DEMO DATA: Curated reference source"),
                "claim_hi": meta.get("claim_hi", "डेमो डेटा: क्यूरेटेड संदर्भ स्रोत"),
                "thumb_url": meta.get("thumb_url", f"/files/{row[1]}"),
            }
            rows.append(rec)
        conn.close()
        return rows
    except Exception:
        return []

def match_origin(phash: str, clip_vec: list[float]) -> Optional[Dict[str, Any]]:
    """Return the best matching image record or ``None`` if no match.

    Matching criteria:
      * pHash Hamming distance <= ``PHASH_MAX_HAMMING``
      * CLIP cosine similarity >= ``CLIP_MIN_SIM`` (skipped if clip_vec is all zeros)
    No match is the normal case and returns None safely.
    """
    candidates = _query_sqlite(phash)
    if not candidates:
        return None

    # Phase 1 – pHash filter
    phash_hits = []
    for rec in candidates:
        dist = _phash_hamming(phash, rec["phash"])
        if dist <= PHASH_MAX_HAMMING:
            phash_hits.append((dist, rec))
    if not phash_hits:
        return None

    phash_hits.sort(key=lambda x: x[0])

    # Phase 2 – CLIP similarity (skip if query vector is zero)
    query_vec = np.array(clip_vec, dtype='float32') if clip_vec else np.zeros(512, dtype='float32')
    query_norm = np.linalg.norm(query_vec)
    if query_norm < 1e-6:
        # Zero vector -> return best pHash hit directly
        return phash_hits[0][1]

    best_score = -1.0
    best_rec = None
    for _, rec in phash_hits:
        vec = np.array(rec["clip_vec"], dtype='float32')
        vec_norm = np.linalg.norm(vec)
        if vec_norm < 1e-6:
            if best_rec is None:
                best_rec = rec
            continue
        score = float(np.dot(query_vec, vec) / (query_norm * vec_norm))
        if score >= CLIP_MIN_SIM and score > best_score:
            best_score = score
            best_rec = rec
    return best_rec or phash_hits[0][1]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Match an image against the demo index")
    parser.add_argument("phash", help="64‑bit pHash hex string")
    parser.add_argument("clip_vec", help="JSON list of CLIP embedding floats")
    args = parser.parse_args()
    result = match_origin(args.phash, json.loads(args.clip_vec))
    print(json.dumps(result, indent=2) if result else "No match")
