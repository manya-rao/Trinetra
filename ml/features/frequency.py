"""
Frequency-domain Feature Extractor (Eye 3)
Computes:
1. Grayscale 2D FFT with DC shift to center
2. Log-magnitude power spectrum: log(1 + |FFT|)
3. Azimuthal (radial) average into fixed bins
4. Peak statistics (high-frequency periodic peak prominence typical of generative upsamplers)
"""
import numpy as np
from PIL import Image
from typing import Tuple
from ml.config import FFT_AZIMUTHAL_BINS

def extract_frequency_features(image: Image.Image, num_bins: int = FFT_AZIMUTHAL_BINS) -> np.ndarray:
    """
    Extracts frequency features from PIL image.
    Returns 1D numpy array of shape (num_bins + 6,):
    - Azimuthal average bins (num_bins,)
    - Log-magnitude mean, std, max, median, skewness proxy, high-freq energy ratio (6,)
    """
    # 1. Convert to grayscale and float32 normalized [0, 1]
    gray = image.convert("L")
    arr = np.asarray(gray, dtype=np.float32) / 255.0
    h, w = arr.shape
    
    # 2. 2D FFT and center DC component
    fft2 = np.fft.fft2(arr)
    fft2_shifted = np.fft.fftshift(fft2)
    magnitude = np.abs(fft2_shifted)
    log_mag = np.log1p(magnitude) # log(1 + |FFT|)
    
    # 3. Azimuthal (radial) average
    cy, cx = h // 2, w // 2
    y, x = np.ogrid[:h, :w]
    r = np.hypot(x - cx, y - cy)
    max_r = np.hypot(cx, cy)
    
    # Bin indices
    r_bins = np.linspace(0, max_r, num_bins + 1)
    azimuthal_profile = np.zeros(num_bins, dtype=np.float32)
    
    for i in range(num_bins):
        mask = (r >= r_bins[i]) & (r < r_bins[i + 1])
        if np.any(mask):
            azimuthal_profile[i] = log_mag[mask].mean()
        else:
            azimuthal_profile[i] = 0.0
            
    # Normalize azimuthal profile to unit scale
    profile_mean = azimuthal_profile.mean()
    profile_std = azimuthal_profile.std() + 1e-6
    azimuthal_norm = (azimuthal_profile - profile_mean) / profile_std
    
    # 4. Peak statistics (periodic upsampling artifacts create isolated frequency spikes)
    # Differences from smooth radial decay
    diffs = np.abs(np.diff(azimuthal_profile, 2)) if num_bins >= 3 else np.array([0.0])
    peak_prominence_max = float(np.max(diffs)) if len(diffs) > 0 else 0.0
    peak_prominence_mean = float(np.mean(diffs)) if len(diffs) > 0 else 0.0
    
    # High-frequency vs low-frequency energy ratio
    mid_bin = num_bins // 2
    low_freq_energy = float(np.sum(azimuthal_profile[:mid_bin])) + 1e-6
    high_freq_energy = float(np.sum(azimuthal_profile[mid_bin:]))
    hf_ratio = high_freq_energy / low_freq_energy
    
    global_mean = float(log_mag.mean())
    global_std = float(log_mag.std())
    global_max = float(log_mag.max())
    
    stats = np.array([
        global_mean,
        global_std,
        global_max,
        peak_prominence_max,
        peak_prominence_mean,
        hf_ratio
    ], dtype=np.float32)
    
    return np.concatenate([azimuthal_norm, stats])
