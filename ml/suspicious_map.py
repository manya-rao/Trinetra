"""
Suspicious Region Map Generator (Eye 3)
Generates a heatmap/overlay PNG highlighting high-frequency residual
and error-level inconsistencies across grid patches.
Always watermarked/labeled: 'suspicious regions, not proof'.
"""
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def generate_suspicious_map(image: Image.Image) -> bytes:
    """
    Computes a per-patch noise/ELA inconsistency map and renders an overlay PNG.
    Returns the PNG bytes.
    """
    # Work on RGB
    img_rgb = image.convert("RGB")
    w, h = img_rgb.size
    
    # 1. Compute high-pass noise residual via median filter subtraction
    blurred = img_rgb.filter(ImageFilter.MedianFilter(size=3))
    arr_orig = np.asarray(img_rgb, dtype=np.float32)
    arr_blur = np.asarray(blurred, dtype=np.float32)
    residual = np.abs(arr_orig - arr_blur).mean(axis=2) # 2D array (h, w)
    
    # 2. Grid patch analysis (e.g. 16x16 grid)
    grid_size = 16
    patch_w = max(4, w // grid_size)
    patch_h = max(4, h // grid_size)
    
    heatmap_grid = np.zeros((grid_size, grid_size), dtype=np.float32)
    for gy in range(grid_size):
        for gx in range(grid_size):
            y0, y1 = gy * patch_h, min(h, (gy + 1) * patch_h)
            x0, x1 = gx * patch_w, min(w, (gx + 1) * patch_w)
            if y1 > y0 and x1 > x0:
                patch = residual[y0:y1, x0:x1]
                # High standard deviation or localized spikes in noise residual indicate synthesis artifacts
                heatmap_grid[gy, gx] = np.std(patch)
                
    # Normalize heatmap grid
    min_val, max_val = heatmap_grid.min(), heatmap_grid.max()
    if max_val - min_val > 1e-5:
        norm_grid = (heatmap_grid - min_val) / (max_val - min_val)
    else:
        norm_grid = np.zeros_like(heatmap_grid)
        
    # Resize heatmap to original image size using bicubic interpolation
    heatmap_img = Image.fromarray((norm_grid * 255).astype(np.uint8), mode="L")
    heatmap_resized = heatmap_img.resize((w, h), resample=Image.BICUBIC)
    
    # Apply warm colormap overlay (RGBA): high values -> semi-transparent red/orange
    heat_arr = np.asarray(heatmap_resized, dtype=np.float32) / 255.0
    overlay = np.zeros((h, w, 4), dtype=np.uint8)
    
    # Red channel
    overlay[:, :, 0] = (np.clip(heat_arr * 2.0, 0, 1) * 230).astype(np.uint8)
    # Green channel (lower for red/orange)
    overlay[:, :, 1] = (np.clip(heat_arr * 0.8, 0, 1) * 120).astype(np.uint8)
    # Blue channel (minimal)
    overlay[:, :, 2] = (np.clip((1.0 - heat_arr) * 0.2, 0, 1) * 50).astype(np.uint8)
    # Alpha channel: higher warmth = higher opacity (max 140/255 for visibility)
    overlay[:, :, 3] = (np.clip(heat_arr, 0.15, 0.85) * 140).astype(np.uint8)
    
    overlay_img = Image.fromarray(overlay, mode="RGBA")
    
    # Draw label: "suspicious regions, not proof"
    draw = ImageDraw.Draw(overlay_img)
    label_text = "suspicious regions, not proof"
    
    # Draw a subtle background badge at bottom-right or bottom-left
    pad = 8
    badge_w = 210
    badge_h = 24
    bx0, by0 = pad, h - badge_h - pad
    bx1, by1 = bx0 + badge_w, by0 + badge_h
    
    draw.rectangle([bx0, by0, bx1, by1], fill=(0, 0, 0, 180))
    draw.text((bx0 + 6, by0 + 5), label_text, fill=(255, 235, 100, 240))
    
    # Export to PNG bytes
    buf = io.BytesIO()
    overlay_img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
