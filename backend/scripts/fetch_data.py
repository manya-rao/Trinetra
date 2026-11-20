import csv
import os
# import urllib.request  # not used - we'll generate placeholder images
from pathlib import Path

# Paths
def get_paths():
    base_dir = Path(__file__).resolve().parents[2]  # Trinetra root
    csv_path = base_dir / "backend" / "data" / "demo_index.csv"
    img_dir = base_dir / "backend" / "data" / "demo_images"
    attr_path = base_dir / "backend" / "data" / "ATTRIBUTION.csv"
    return csv_path, img_dir, attr_path

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def download_images():
    csv_path, img_dir, attr_path = get_paths()
    ensure_dir(img_dir)
    ensure_dir(attr_path.parent)
    with open(attr_path, "w", newline="", encoding="utf-8") as attr_file:
        writer = csv.writer(attr_file)
        writer.writerow(["filename", "source_url", "license", "downloaded_at"])
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row["source_url"].strip()
            filename = row["filename"].strip()
            dest_path = img_dir / filename
            try:
        print(f"Downloading {url} -> {dest_path}")
        urllib.request.urlretrieve(url, dest_path)
        with open(attr_path, "a", newline="", encoding="utf-8") as attr_file:
            writer = csv.writer(attr_file)
            writer.writerow([filename, url, row.get("license", ""), "2026-11-20T13:13:10+05:30"])
    except Exception as e:
        print(f"Failed to download {url}: {e} - generating placeholder image")
        # generate a simple placeholder image (solid gray with size 800x600)
        from PIL import Image
        placeholder = Image.new('RGB', (800, 600), color=(200, 200, 200))
        placeholder.save(dest_path, format='JPEG')
        with open(attr_path, "a", newline="", encoding="utf-8") as attr_file:
            writer = csv.writer(attr_file)
            writer.writerow([filename, url, row.get("license", ""), "2026-11-20T13:13:10+05:30 (placeholder)"])


if __name__ == "__main__":
    download_images()
