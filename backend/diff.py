import cv2
import numpy as np
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from skimage.metrics import structural_similarity as ssim
    _skimage_available = True
except ImportError:
    _skimage_available = False

try:
    from app import config as cfg
except ImportError:
    from backend.app import config as cfg

logger = logging.getLogger(__name__)


def _compute_ssim(img1_gray: np.ndarray, img2_gray: np.ndarray):
    """Compute SSIM score and normalized uint8 difference (similarity) map [0, 255].
    255 means identical (similarity 1.0), 0 means completely different.
    """
    if _skimage_available:
        score, diff = ssim(img1_gray, img2_gray, full=True)
        # skimage full=True can produce negative floats in [-1, 1]
        diff_clipped = np.clip(diff, 0.0, 1.0)
        return float(score), (diff_clipped * 255).astype(np.uint8)

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
    diff = np.clip(ssim_map, 0.0, 1.0)
    return score, (diff * 255).astype(np.uint8)


def _load_image(path: Path) -> np.ndarray:
    """Helper to load OpenCV image in RGB."""
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Image not found: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _resize_to_working_size(img: np.ndarray, max_side: int):
    """Downscale image so its maximum dimension is at most max_side using INTER_AREA."""
    h, w = img.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / float(max(h, w))
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA), scale
    return img.copy(), 1.0


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
    """Match keypoint descriptors using Lowe's ratio test."""
    if method == "SIFT":
        index_params = dict(algorithm=1, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1, des2, k=2)
        good = []
        for m_n in matches:
            if len(m_n) == 2:
                m, n = m_n
                if m.distance < 0.75 * n.distance:
                    good.append(m)
        return good
    else:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)
        good = matches[: int(0.3 * len(matches))]
        return good


def diff_images(
    original_path: Path,
    edited_path: Path,
    output_dir: Path,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate reliable diff information and SSIM colour heatmap between two images.

    Returns a dictionary with keys:
        - reliable (bool): whether alignment and diff pass sanity checks
        - reliability_reason (str): diagnostic text explaining reliability
        - inlier_count (int): number of homography inliers
        - inlier_ratio (float): inlier ratio of matched keypoints
        - changed_area_fraction (float): fraction of frame detected as changed
        - heatmap_path (str | None): path to PNG visualising SSIM colour heatmap
        - aligned_path (str | None): warped original image aligned to edited image
        - changed_regions (list of dicts with x, y, w, h in edited image coordinates)
    """
    img1 = _load_image(original_path)
    img2 = _load_image(edited_path)
    h2, w2 = img2.shape[:2]

    # Compare at common working size (downscale with INTER_AREA)
    max_side = cfg.DIFF_WORKING_LONG_SIDE
    img1_work, scale1 = _resize_to_working_size(img1, max_side)
    img2_work, scale2 = _resize_to_working_size(img2, max_side)
    h2_work, w2_work = img2_work.shape[:2]

    # Detect keypoints on working size images
    kp1, des1, method = _detect_keypoints(img1_work)
    kp2, des2, _ = _detect_keypoints(img2_work)
    if des1 is None or des2 is None:
        logger.warning("No descriptors found - returning unreliable diff")
        return {
            "reliable": False,
            "reliability_reason": "No keypoint descriptors found in one or both images",
            "inlier_count": 0,
            "inlier_ratio": 0.0,
            "changed_area_fraction": 0.0,
            "heatmap_path": None,
            "aligned_path": None,
            "changed_regions": []
        }

    good_matches = _match_descriptors(des1, des2, method)
    if len(good_matches) < 4:
        logger.warning(f"Not enough matches for homography: {len(good_matches)}")
        return {
            "reliable": False,
            "reliability_reason": f"Insufficient matching keypoints ({len(good_matches)} < 4)",
            "inlier_count": 0,
            "inlier_ratio": 0.0,
            "changed_area_fraction": 0.0,
            "heatmap_path": None,
            "aligned_path": None,
            "changed_regions": []
        }

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransacReprojThreshold=cfg.HOMOGRAPHY_RANSAC_REPROJ)
    if H is None or mask is None:
        logger.warning("Homography estimation failed")
        return {
            "reliable": False,
            "reliability_reason": "Homography estimation failed",
            "inlier_count": 0,
            "inlier_ratio": 0.0,
            "changed_area_fraction": 0.0,
            "heatmap_path": None,
            "aligned_path": None,
            "changed_regions": []
        }

    inlier_count = int(np.sum(mask))
    inlier_ratio = float(inlier_count / len(good_matches)) if good_matches else 0.0

    if inlier_count < cfg.HOMOGRAPHY_MIN_INLIERS or inlier_ratio < cfg.HOMOGRAPHY_MIN_INLIER_RATIO:
        logger.warning(f"Weak homography alignment: inliers={inlier_count}, ratio={inlier_ratio:.2f}")
        return {
            "reliable": False,
            "reliability_reason": f"Weak alignment (inliers={inlier_count} < {cfg.HOMOGRAPHY_MIN_INLIERS} or ratio={inlier_ratio:.2f} < {cfg.HOMOGRAPHY_MIN_INLIER_RATIO})",
            "inlier_count": inlier_count,
            "inlier_ratio": inlier_ratio,
            "changed_area_fraction": 0.0,
            "heatmap_path": None,
            "aligned_path": None,
            "changed_regions": []
        }

    # Warp original working image to edited working view
    aligned_work = cv2.warpPerspective(img1_work, H, (w2_work, h2_work))

    # Pre-SSIM light Gaussian blur to suppress compression / resampling artifacts
    k = cfg.DIFF_BLUR_KERNEL_SIZE
    if k % 2 == 0:
        k += 1
    sigma = cfg.DIFF_BLUR_SIGMA
    gray_aligned = cv2.GaussianBlur(cv2.cvtColor(aligned_work, cv2.COLOR_RGB2GRAY), (k, k), sigma)
    gray_edited = cv2.GaussianBlur(cv2.cvtColor(img2_work, cv2.COLOR_RGB2GRAY), (k, k), sigma)

    ssim_score, diff_map = _compute_ssim(gray_aligned, gray_edited)

    # Invert threshold: diff_map is similarity (255 = identical, 0 = changed).
    # Mark pixels where similarity is LOW with THRESH_BINARY_INV.
    thresh_val = int(255 * cfg.SSIM_DIFF_THRESHOLD)
    _, mask_diff = cv2.threshold(diff_map, thresh_val, 255, cv2.THRESH_BINARY_INV)

    total_work_pixels = w2_work * h2_work
    changed_pixels = int(np.count_nonzero(mask_diff))
    changed_area_fraction = float(changed_pixels / total_work_pixels) if total_work_pixels > 0 else 0.0

    # If changed area is almost the whole image, diff is unreliable
    if changed_area_fraction > cfg.DIFF_MAX_CHANGED_FRACTION:
        logger.warning(f"Changed area fraction too large: {changed_area_fraction:.2f} > {cfg.DIFF_MAX_CHANGED_FRACTION}")
        return {
            "reliable": False,
            "reliability_reason": f"Changed area fraction too large ({changed_area_fraction:.2f} > {cfg.DIFF_MAX_CHANGED_FRACTION})",
            "inlier_count": inlier_count,
            "inlier_ratio": inlier_ratio,
            "changed_area_fraction": changed_area_fraction,
            "heatmap_path": None,
            "aligned_path": None,
            "changed_regions": []
        }

    # Find contours and filter small isolated noise
    contours, _ = cv2.findContours(mask_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    changed_regions = []
    work_boxes = []

    scale_to_orig_x = w2 / float(w2_work)
    scale_to_orig_y = h2 / float(h2_work)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < cfg.MIN_CONTOUR_AREA_PX:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if w < cfg.DIFF_MIN_REGION_BOUNDS or h < cfg.DIFF_MIN_REGION_BOUNDS:
            continue
        work_boxes.append((x, y, w, h))

        orig_x = int(round(x * scale_to_orig_x))
        orig_y = int(round(y * scale_to_orig_y))
        orig_w = int(round(w * scale_to_orig_x))
        orig_h = int(round(h * scale_to_orig_y))
        changed_regions.append({"x": orig_x, "y": orig_y, "w": orig_w, "h": orig_h})

    # SSIM colour heatmap overlay (dissimilarity = 255 - similarity)
    dissimilarity = 255 - diff_map
    heatmap_jet = cv2.applyColorMap(dissimilarity, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(img2_work, 0.65, heatmap_jet, 0.35, 0)

    # Draw rectangles on overlay
    for (x, y, w, h) in work_boxes:
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (255, 0, 0), 2)

    # Scale outputs to match original edited image dimensions if working image was downscaled
    if scale2 < 1.0:
        final_heatmap = cv2.resize(overlay, (w2, h2), interpolation=cv2.INTER_LINEAR)
        final_aligned = cv2.resize(aligned_work, (w2, h2), interpolation=cv2.INTER_LINEAR)
    else:
        final_heatmap = overlay
        final_aligned = aligned_work

    # Unique filenames per request
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = request_id if request_id else original_path.stem
    heatmap_path = output_dir / f"{stem}_heatmap.png"
    aligned_path = output_dir / f"{stem}_aligned.png"
    cv2.imwrite(str(heatmap_path), cv2.cvtColor(final_heatmap, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(aligned_path), cv2.cvtColor(final_aligned, cv2.COLOR_RGB2BGR))

    return {
        "reliable": True,
        "reliability_reason": "Reliable alignment and diff",
        "inlier_count": inlier_count,
        "inlier_ratio": inlier_ratio,
        "changed_area_fraction": changed_area_fraction,
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
    parser.add_argument("--request-id", type=str, default=None)
    args = parser.parse_args()
    result = diff_images(args.orig, args.edit, args.out, request_id=args.request_id)
    print(json.dumps(result, indent=2))
