"""
Feature Extraction and Caching Pipeline (Eye 3: ai_lane)
Extracts:
1. OpenCLIP ViT-B-32 embeddings (512-dim, L2-normalized)
2. Azimuthal FFT frequency spectrum & peak statistics (70-dim)
3. Noise residual & ELA inconsistency statistics (15-dim)
4. Metadata flags (3-dim)

Saves all extracted matrices to ml/data/cache/ as .npy files for instantaneous retraining.
"""
import os
import sys
import logging
from pathlib import Path
import numpy as np
from PIL import Image
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("extract_cache")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
CACHE_DIR = BASE_DIR / "data" / "cache"

from ml.features.clip_features import extract_clip_embedding
from ml.features.frequency import extract_frequency_features
from ml.features.noise import extract_noise_features
from ml.features.metadata import extract_metadata_features

def run_extraction():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    classes = ["real", "stable_diffusion", "midjourney", "dalle", "flux"]
    
    all_clip = []
    all_freq = []
    all_noise = []
    all_meta = []
    all_labels = []      # 0 for real, 1 for AI
    all_generators = []  # str generator class
    all_paths = []
    
    logger.info("Scanning raw dataset directories...")
    image_files = []
    for c in classes:
        folder = RAW_DIR / c
        if not folder.exists():
            continue
        files = list(folder.glob("*.jpg"))
        logger.info(f"Class '{c}': found {len(files)} images.")
        for p in files:
            image_files.append((p, c))
            
    if not image_files:
        logger.error("No images found in raw directory! Run fetch_data.py first.")
        return
        
    logger.info(f"Extracting multimodal features for {len(image_files)} images...")
    
    for idx, (img_path, gen_name) in enumerate(tqdm(image_files, desc="Extracting")):
        try:
            with Image.open(img_path) as img:
                img_rgb = img.convert("RGB")
                
                # 1. OpenCLIP feature
                clip_emb = extract_clip_embedding(img_rgb)
                
                # 2. Frequency feature
                freq_feat = extract_frequency_features(img_rgb)
                
                # 3. Noise & ELA feature
                noise_feat = extract_noise_features(img_rgb)
                
                # 4. Metadata feature
                meta_feat = extract_metadata_features(img_rgb)
                
                label = 0 if gen_name == "real" else 1
                
                all_clip.append(clip_emb)
                all_freq.append(freq_feat)
                all_noise.append(noise_feat)
                all_meta.append(meta_feat)
                all_labels.append(label)
                all_generators.append(gen_name)
                all_paths.append(str(img_path))
                
        except Exception as e:
            logger.warning(f"Failed to process {img_path}: {e}")
            
    # Convert to numpy arrays
    clip_arr = np.array(all_clip, dtype=np.float32)
    freq_arr = np.array(all_freq, dtype=np.float32)
    noise_arr = np.array(all_noise, dtype=np.float32)
    meta_arr = np.array(all_meta, dtype=np.float32)
    labels_arr = np.array(all_labels, dtype=np.int32)
    generators_arr = np.array(all_generators, dtype=object)
    paths_arr = np.array(all_paths, dtype=object)
    
    logger.info(f"Extracted feature matrix shapes:")
    logger.info(f"  CLIP embeddings: {clip_arr.shape}")
    logger.info(f"  Frequency features: {freq_arr.shape}")
    logger.info(f"  Noise features: {noise_arr.shape}")
    logger.info(f"  Metadata features: {meta_arr.shape}")
    logger.info(f"  Labels: {labels_arr.shape} (Reals: {np.sum(labels_arr == 0)}, AI: {np.sum(labels_arr == 1)})")
    
    # Save cached .npy files
    np.save(CACHE_DIR / "clip_features.npy", clip_arr)
    np.save(CACHE_DIR / "frequency_features.npy", freq_arr)
    np.save(CACHE_DIR / "noise_features.npy", noise_arr)
    np.save(CACHE_DIR / "metadata_features.npy", meta_arr)
    np.save(CACHE_DIR / "labels.npy", labels_arr)
    np.save(CACHE_DIR / "generators.npy", generators_arr)
    np.save(CACHE_DIR / "paths.npy", paths_arr)
    
    logger.info(f"Successfully cached all extracted features to {CACHE_DIR}")

if __name__ == "__main__":
    run_extraction()
