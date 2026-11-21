"""
Noise Residual and Error Level Analysis (ELA) Feature Extractor (Eye 3)
Extracts:
1. High-pass noise residual (image minus 3x3 median filter)
2. Per-patch standard deviation and kurtosis on an 8x8 spatial grid
3. Global noise residual statistics (mean, std, skew, kurtosis)
4. ELA (Error Level Analysis) variance across compression levels
"""
import io
import numpy as np
from PIL import Image, ImageFilter
from scipy.stats import kurtosis, skew
from ml.config import NOISE_GRID_PATCHES
from ml.features.crop_util import get_fixed_crops

def compute_ela_residual(image: Image.Image, quality: int = 90) -> np.ndarray:
    """Computes Error Level Analysis residual array."""
    rgb = image.convert("RGB")
    buf = io.BytesIO()
    rgb.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")
    
    arr_orig = np.asarray(rgb, dtype=np.float32)
    arr_recomp = np.asarray(recompressed, dtype=np.float32)
    ela = np.abs(arr_orig - arr_recomp).mean(axis=2) # 2D array
    return ela

def _extract_single_crop_noise(rgb: Image.Image, grid_size: int = NOISE_GRID_PATCHES) -> np.ndarray:
    w, h = rgb.size
    
    # 1. High-pass residual via median filter subtraction
    blurred = rgb.filter(ImageFilter.MedianFilter(size=3))
    arr_orig = np.asarray(rgb, dtype=np.float32)
    arr_blur = np.asarray(blurred, dtype=np.float32)
    residual = (arr_orig - arr_blur).mean(axis=2) # 2D float array
    
    # 2. Per-patch grid statistics (grid_size x grid_size)
    patch_w = max(4, w // grid_size)
    patch_h = max(4, h // grid_size)
    
    patch_stds = []
    patch_kurtoses = []
    
    for gy in range(grid_size):
        for gx in range(grid_size):
            y0, y1 = gy * patch_h, min(h, (gy + 1) * patch_h)
            x0, x1 = gx * patch_w, min(w, (gx + 1) * patch_w)
            if y1 > y0 and x1 > x0:
                patch = residual[y0:y1, x0:x1].flatten()
                p_std = float(np.std(patch))
                p_kurt = float(kurtosis(patch, fisher=True)) if len(patch) > 4 else 0.0
                patch_stds.append(p_std)
                patch_kurtoses.append(p_kurt)
            else:
                patch_stds.append(0.0)
                patch_kurtoses.append(0.0)
                
    patch_stds_arr = np.array(patch_stds, dtype=np.float32)
    patch_kurt_arr = np.array(patch_kurtoses, dtype=np.float32)
    # Clamp extreme kurtosis outliers
    patch_kurt_arr = np.clip(patch_kurt_arr, -3.0, 30.0)
    
    # 3. Global noise statistics
    flat_res = residual.flatten()
    glob_mean = float(np.mean(flat_res))
    glob_std = float(np.std(flat_res))
    if glob_std < 1e-9 or len(flat_res) <= 3:
        glob_skew = 0.0
    else:
        _gs = skew(flat_res)
        glob_skew = 0.0 if np.isnan(_gs) else float(_gs)
    if glob_std < 1e-9 or len(flat_res) <= 4:
        glob_kurt = 0.0
    else:
        _gk = kurtosis(flat_res, fisher=True)
        glob_kurt = 0.0 if np.isnan(_gk) else float(_gk)
    
    # Grid spatial variance (how non-uniform the noise field is)
    grid_std_of_stds = float(np.std(patch_stds_arr))
    grid_mean_of_stds = float(np.mean(patch_stds_arr))
    grid_heterogeneity = grid_std_of_stds / (grid_mean_of_stds + 1e-6)
    
    # 4. ELA variance
    ela = compute_ela_residual(rgb, quality=90)
    ela_mean = float(np.mean(ela))
    ela_std = float(np.std(ela))
    ela_variance = float(np.var(ela))
    
    # Summary patch features: mean, std, max, min of grid
    summary_features = np.array([
        glob_mean,
        glob_std,
        glob_skew,
        np.clip(glob_kurt, -3.0, 30.0),
        grid_std_of_stds,
        grid_heterogeneity,
        ela_mean,
        ela_std,
        ela_variance,
        float(np.percentile(patch_stds_arr, 10)),
        float(np.percentile(patch_stds_arr, 50)),
        float(np.percentile(patch_stds_arr, 90)),
        float(np.percentile(patch_kurt_arr, 10)),
        float(np.percentile(patch_kurt_arr, 50)),
        float(np.percentile(patch_kurt_arr, 90))
    ], dtype=np.float32)
    
    summary_features = np.nan_to_num(summary_features, nan=0.0, posinf=0.0, neginf=0.0)
    return summary_features

def extract_noise_features(image: Image.Image, grid_size: int = NOISE_GRID_PATCHES) -> np.ndarray:
    """
    Extracts spatial noise and compression inconsistency features normalized across fixed-size 384x384 crops.
    Ensures full-resolution camera photos and 384px training images produce comparable feature statistics.
    """
    crops = get_fixed_crops(image, crop_size=384, max_crops=5)
    crop_feats = [_extract_single_crop_noise(c.convert("RGB"), grid_size) for c in crops]
    return np.mean(crop_feats, axis=0).astype(np.float32)
