"""
User Data Ingestion Pipeline for Trinetra Eye 3.
Ingests user-supplied datasets from:
  - ml/data/user/real/
  - ml/data/user/real_whatsapp/
  - ml/data/user/ai/<generator>/

Enforces:
1. Exact counting and reporting per folder.
2. If a folder is empty or has fewer than 100 images, explicitly logs that without fabrication or duplication.
3. Groups images by source photo so that a photo and its WhatsApp copy share the same source split.
4. Uses the canonical extract_all_features pipeline.
"""
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
USER_DATA_DIR = BASE_DIR / "data" / "user"
CACHE_DIR = BASE_DIR / "data" / "cache"

from ml.features.pipeline import extract_all_features


def get_source_id(filename: str) -> str:
    """
    Derives canonical source photo ID from filename.
    Strips WhatsApp / compression suffixes and extensions.
    Example: 'IMG_2026_wa.jpg' -> 'IMG_2026'
    """
    stem = Path(filename).stem
    # Remove common whatsapp / copy suffixes
    cleaned = re.sub(r'(_whatsapp|_wa|_compressed|_copy|\(\d+\))$', '', stem, flags=re.IGNORECASE)
    return cleaned


def scan_user_folders() -> Dict[str, Dict[str, Any]]:
    """
    Scans the user directories:
      - ml/data/user/real/
      - ml/data/user/real_whatsapp/
      - ml/data/user/ai/<generator>/
      - ml/data/user/*.jpg (root files like misflagged_01.jpg)
    """
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    real_dir = USER_DATA_DIR / "real"
    real_wa_dir = USER_DATA_DIR / "real_whatsapp"
    ai_dir = USER_DATA_DIR / "ai"

    real_dir.mkdir(exist_ok=True)
    real_wa_dir.mkdir(exist_ok=True)
    ai_dir.mkdir(exist_ok=True)

    folder_stats = {}

    # 1. Real photos
    real_files = list(real_dir.glob("*.jpg")) + list(real_dir.glob("*.png")) + list(real_dir.glob("*.jpeg"))
    # Also check root user folder for standalone files like misflagged_01.jpg
    root_files = [f for f in USER_DATA_DIR.glob("*.jpg") if f.is_file()] + [f for f in USER_DATA_DIR.glob("*.png") if f.is_file()]
    all_reals = list(set(real_files + root_files))
    folder_stats["real"] = {
        "path": str(real_dir),
        "files": all_reals,
        "count": len(all_reals),
        "type": "real",
        "generator": "real"
    }

    # 2. Real WhatsApp photos
    wa_files = list(real_wa_dir.glob("*.jpg")) + list(real_wa_dir.glob("*.png")) + list(real_wa_dir.glob("*.jpeg"))
    folder_stats["real_whatsapp"] = {
        "path": str(real_wa_dir),
        "files": wa_files,
        "count": len(wa_files),
        "type": "real",
        "generator": "real"
    }

    # 3. AI generator folders
    ai_subdirs = [d for d in ai_dir.iterdir() if d.is_dir()]
    if not ai_subdirs:
        folder_stats["ai"] = {
            "path": str(ai_dir),
            "files": [],
            "count": 0,
            "type": "ai",
            "generator": "unspecified"
        }
    else:
        for sub in ai_subdirs:
            gen_name = sub.name
            files = list(sub.glob("*.jpg")) + list(sub.glob("*.png")) + list(sub.glob("*.jpeg"))
            folder_stats[f"ai/{gen_name}"] = {
                "path": str(sub),
                "files": files,
                "count": len(files),
                "type": "ai",
                "generator": gen_name
            }

    return folder_stats


def ingest_user_data() -> Dict[str, Any]:
    """
    Ingests all available user data.
    Logs explicit counts and notices for any folders with < 100 images.
    Returns extracted feature arrays and metadata with source_ids for grouping.
    """
    folder_stats = scan_user_folders()
    print("=== INGEST USER DATA REPORT ===")
    
    total_images = 0
    all_clip = []
    all_freq = []
    all_noise = []
    all_meta = []
    all_labels = []
    all_generators = []
    all_sources = []
    all_paths = []

    for name, stat in folder_stats.items():
        count = stat["count"]
        status_note = ""
        if count == 0:
            status_note = "(EMPTY - No images found. No fabrication or duplication applied)"
        elif count < 100:
            status_note = f"(FEWER THAN 100 IMAGES: {count} images found. No fabrication or duplication applied)"
        else:
            status_note = f"({count} images found)"
            
        print(f"  * {name:<22}: {count:>4} images  {status_note}")
        total_images += count

        for p in stat["files"]:
            try:
                with Image.open(p) as img:
                    feats = extract_all_features(img)
                    source_id = get_source_id(p.name)
                    label = 0 if stat["type"] == "real" else 1

                    all_clip.append(feats["clip"])
                    all_freq.append(feats["frequency"])
                    all_noise.append(feats["noise"])
                    all_meta.append(feats["metadata"])
                    all_labels.append(label)
                    all_generators.append(stat["generator"])
                    all_sources.append(source_id)
                    all_paths.append(str(p))
            except Exception as e:
                print(f"    [WARN] Failed to process {p}: {e}")

    print(f"Total user images ingested: {total_images}")
    print("================================")

    res = {
        "folder_stats": folder_stats,
        "total_count": total_images,
        "clip": np.array(all_clip, dtype=np.float32) if all_clip else np.empty((0, 512)),
        "frequency": np.array(all_freq, dtype=np.float32) if all_freq else np.empty((0, 70)),
        "noise": np.array(all_noise, dtype=np.float32) if all_noise else np.empty((0, 15)),
        "metadata": np.array(all_meta, dtype=np.float32) if all_meta else np.empty((0, 3)),
        "labels": np.array(all_labels, dtype=np.int32) if all_labels else np.empty((0,)),
        "generators": np.array(all_generators, dtype=object) if all_generators else np.empty((0,)),
        "sources": np.array(all_sources, dtype=object) if all_sources else np.empty((0,)),
        "paths": np.array(all_paths, dtype=object) if all_paths else np.empty((0,))
    }
    return res


if __name__ == "__main__":
    ingest_user_data()
