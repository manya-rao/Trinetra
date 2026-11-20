import cv2
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
try:
    from skimage.metrics import structural_similarity as ssim
    _skimage_available = True
except ImportError:
    _skimage_available = False

def _compute_ssim(img1_gray: np.ndarray, img2_gray: np.ndarray):
    """Compute SSIM score and difference map."""
    if _skimage_available:
        score, diff = ssim(img1_gray, img2_gray, full=True)
        return score, (diff * 255).astype(np.uint8)

    # Pure OpenCV / NumPy SSIM fallback (Wang et al.)
    I1 = img1_gray.astype(np.float64)
    I2 = img2_gray.astype(np.float64)
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    mu1 = cv2.GaussianBlur(I1, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(I2, (11, 11), 1.5)
    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.GaussianBlur(I1 * I1, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(I2 * I2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(I1 * I2, (11, 11), 1.5) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    score = float(ssim_map.mean())
    diff = np.clip(ssim_map * 255, 0, 255).astype(np.uint8)
    return score, diff

import logging

logger = logging.getLogger(__name__)

# Helper to load OpenCV image in RGB
def _load_image(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Image not found: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def _detect_keypoints(img: np.ndarray):
    """Return keypoints and descriptors using SIFT if available, else ORB."""
    try:
        sift = cv2.SIFT_create()
        kp, des = sift.detectAndCompute(img, None)
        method = "SIFT"
    except Exception:
        orb = cv2.ORB_create()
        kp, des = orb.detectAndCompute(img, None)
        method = "ORB"
    return kp, des, method

def _match_descriptors(des1, des2, method: str):
    if method == "SIFT":
        # FLANN based matcher for SIFT (float descriptors)
        index_params = dict(algorithm=1, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1, des2, k=2)
        # Lowe's ratio test
        good = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good.append(m)
        return good
    else:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)
        # Keep the top 30% as good matches
        good = matches[: int(0.3 * len(matches))]
        return good

def diff_images(
    original_path: Path,
    edited_path: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """Generate diff information between two images.

    Returns a dictionary with keys:
        - ``heatmap_path`` (str): path to a PNG visualising changed regions
        - ``aligned_path`` (str): the original image warped to the edited view
        - ``changed_regions`` (list of dicts with x, y, w, h)
    """
    img1 = _load_image(original_path)
    img2 = _load_image(edited_path)

    # Resize down for keypoint detection (respect MAX_IMAGE_LONG_SIDE)
    # Use config constant
    try:
        from app import config as cfg
    except ImportError:
        from backend.app import config as cfg
    max_side = cfg.MAX_IMAGE_LONG_SIDE
    def _resize_long_side(im):
        h, w = im.shape[:2]
        if max(h, w) > max_side:
            scale = max_side / max(h, w)
            new_sz = (int(w * scale), int(h * scale))
            return cv2.resize(im, new_sz, interpolation=cv2.INTER_AREA)
        return im
    img1_small = _resize_long_side(img1)
    img2_small = _resize_long_side(img2)

    kp1, des1, method = _detect_keypoints(img1_small)
    kp2, des2, _ = _detect_keypoints(img2_small)
    if des1 is None or des2 is None:
        logger.warning("No descriptors found – skipping diff, returning empty result")
        return {"heatmap_path": None, "aligned_path": None, "changed_regions": []}

    good_matches = _match_descriptors(des1, des2, method)
    if len(good_matches) < 4:
        logger.warning("Not enough matches for homography – returning empty diff")
        return {"heatmap_path": None, "aligned_path": None, "changed_regions": []}

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransacReprojThreshold=cfg.HOMOGRAPHY_RANSAC_REPROJ)
    if H is None:
        logger.warning("Homography estimation failed")
        return {"heatmap_path": None, "aligned_path": None, "changed_regions": []}

    # Warp original to edited view
    h2, w2 = img2.shape[:2]
    aligned = cv2.warpPerspective(img1, H, (w2, h2))

    # Compute SSIM on grayscale images
    gray_aligned = cv2.cvtColor(aligned, cv2.COLOR_RGB2GRAY)
    gray_edited = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
    ssim_score, diff = _compute_ssim(gray_aligned, gray_edited)

    # Threshold diff to get change mask
    _, mask_diff = cv2.threshold(diff, int(255 * (1 - cfg.SSIM_SCORE_THRESHOLD)), 255, cv2.THRESH_BINARY)
    # Remove small noise
    contours, _ = cv2.findContours(mask_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    changed_regions = []
    heatmap = np.zeros_like(img2)
    for cnt in contours:
        if cv2.contourArea(cnt) < cfg.MIN_CONTOUR_AREA_PX:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        changed_regions.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
        cv2.rectangle(heatmap, (x, y), (x + w, y + h), (255, 0, 0), 2)

    # Write outputs
    output_dir.mkdir(parents=True, exist_ok=True)
    heatmap_path = output_dir / f"{original_path.stem}_heatmap.png"
    aligned_path = output_dir / f"{original_path.stem}_aligned.png"
    cv2.imwrite(str(heatmap_path), cv2.cvtColor(heatmap, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(aligned_path), cv2.cvtColor(aligned, cv2.COLOR_RGB2BGR))

    return {
        "heatmap_path": str(heatmap_path),
        "aligned_path": str(aligned_path),
        "changed_regions": changed_regions,
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Diff two images and output heatmap/aligned files")
    parser.add_argument("orig", type=Path)
    parser.add_argument("edit", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    result = diff_images(args.orig, args.edit, args.out)
    print(json.dumps(result, indent=2))
