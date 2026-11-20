import os
import csv
import random
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import shutil

BASE_DIR = Path(__file__).resolve().parents[2]
IMG_DIR = BASE_DIR / "backend" / "data" / "demo_images"
VAR_DIR = BASE_DIR / "backend" / "data" / "variants"
GT_PATH = BASE_DIR / "backend" / "data" / "ground_truth.csv"

def ensure_dirs():
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    GT_PATH.parent.mkdir(parents=True, exist_ok=True)

def save_image(img: Image.Image, out_path: Path, quality: int = 90):
    img.save(out_path, format="JPEG", quality=quality)

def create_variants():
    ensure_dirs()
    gt_rows = []
    for img_file in IMG_DIR.iterdir():
        if img_file.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        img = Image.open(img_file).convert("RGB")
        name = img_file.stem
        # 1. resized (800px long side)
        resized = ImageOps.contain(img, (800, 800))
        save_image(resized, VAR_DIR / f"{name}_resized.jpg", quality=90)
        # 2. cropped (center 70% area)
        w, h = img.size
        left = int(w * 0.15)
        top = int(h * 0.15)
        right = int(w * 0.85)
        bottom = int(h * 0.85)
        cropped = img.crop((left, top, right, bottom))
        save_image(cropped, VAR_DIR / f"{name}_cropped.jpg", quality=90)
        # 3. recompressed (quality 70)
        save_image(img, VAR_DIR / f"{name}_recompress_q70.jpg", quality=70)
        # 4. screenshot‑style (add white border, downscale)
        bordered = ImageOps.expand(img, border=10, fill="white")
        screenshot = ImageOps.contain(bordered, (600, 600))
        save_image(screenshot, VAR_DIR / f"{name}_screenshot.jpg", quality=85)
        # 5. edited version – simple synthetic edit: draw a red rectangle
        edited = img.copy()
        draw = ImageDraw.Draw(edited)
        rect_w, rect_h = int(w * 0.2), int(h * 0.2)
        x0, y0 = random.randint(0, w - rect_w), random.randint(0, h - rect_h)
        x1, y1 = x0 + rect_w, y0 + rect_h
        draw.rectangle([x0, y0, x1, y1], outline="red", width=5)
        save_image(edited, VAR_DIR / f"{name}_edited.jpg", quality=90)
        # ground‑truth box for edited version
        gt_rows.append([f"{name}_edited.jpg", x0, y0, rect_w, rect_h])
    # write ground truth csv
    with open(GT_PATH, "w", newline="", encoding="utf-8") as gt_file:
        writer = csv.writer(gt_file)
        writer.writerow(["filename", "x", "y", "w", "h"])
        writer.writerows(gt_rows)

if __name__ == "__main__":
    create_variants()
