"""
Gate Module for Eye 3 (Synthesis Engine)
Enforces safety rules to prevent false accusations.
Forces band to 'inconclusive' when:
1. min(width, height) < 256
2. Very low JPEG quality or heavy recompression (quality <= 75)
3. Screenshot-style border padding or resampled letterbox
4. Artificial / synthetic uniform noise field (std > 2.0, kurtosis near 0, low spatial heterogeneity)
5. Strong disagreement between semantic CLIP probe and forensic frequency/noise signals
"""
from typing import Tuple, List, Optional
import numpy as np
from PIL import Image
from ml.config import MIN_IMAGE_DIM, HEAVY_COMPRESSION_JPEG_QUALITY

def check_screenshot_border(image: Image.Image) -> bool:
    """
    Detects solid letterbox padding or resampled borders typical of mobile screenshots.
    Returns True if at least 2 outer border bands have near-zero variance.
    """
    try:
        arr = np.asarray(image.convert("RGB"), dtype=np.float32)
        h, w, _ = arr.shape
        b_h = max(4, int(h * 0.03))
        b_w = max(4, int(w * 0.03))
        borders = [
            arr[:b_h, :, :],
            arr[-b_h:, :, :],
            arr[:, :b_w, :],
            arr[:, -b_w:, :]
        ]
        solid_count = sum(1 for b in borders if float(np.std(b)) < 4.0)
        return solid_count >= 2
    except Exception:
        return False

def check_camera_metadata(image: Image.Image) -> bool:
    """
    Checks if image carries genuine camera EXIF metadata:
    - Camera Make (tag 271) or Model (tag 272) is present and non-empty.
    - AND at least one physical exposure/camera setting field is present:
      ExposureTime (33434), FNumber (33437), ISOSpeedRatings (34855),
      ShutterSpeedValue (37377), ApertureValue (37378), FocalLength (37386).

    Documented Guardrail Guarantee:
    Camera EXIF can be stripped or forged, so metadata is NOT cryptographic proof of authenticity.
    However, when genuine capture metadata is present, pixels alone cannot substantiate an
    affirmative AI accusation, forcing an Inconclusive verdict with 'camera_metadata_present'.
    """
    try:
        exif = image.getexif()
        if not exif or len(exif) == 0:
            return False

        make = str(exif.get(271, "")).strip()
        model = str(exif.get(272, "")).strip()
        if not (make or model):
            return False

        exposure_tags = {33434, 33437, 34855, 37377, 37378, 37386}
        if any(tag in exif for tag in exposure_tags):
            return True

        from PIL import ExifTags
        ifd = exif.get_ifd(ExifTags.IFD.Exif)
        if ifd and any(tag in ifd for tag in exposure_tags):
            return True

        return False
    except Exception:
        return False

def evaluate_gate(
    width: int,
    height: int,
    jpeg_quality: Optional[float] = None,
    probe_score: Optional[float] = None,
    forensic_score: Optional[float] = None,
    disagreement_threshold: float = 0.35,
    noise_features: Optional[np.ndarray] = None,
    image: Optional[Image.Image] = None
) -> Tuple[bool, List[str]]:
    """
    Evaluates whether input image triggers gate rules requiring an Inconclusive verdict.

    Returns:
        (gate_triggered: bool, reason_keys: List[str])
    """
    reasons = []

    # Rule 1: Low resolution
    if width < MIN_IMAGE_DIM or height < MIN_IMAGE_DIM:
        reasons.append("low_resolution")

    # Rule 2: Heavy compression
    if jpeg_quality is not None and jpeg_quality > 0 and jpeg_quality <= HEAVY_COMPRESSION_JPEG_QUALITY:
        reasons.append("heavy_compression")

    # Rule 3: Screenshot border padding (letterboxing / device frame)
    if image is not None and check_screenshot_border(image):
        if "heavy_compression" not in reasons:
            reasons.append("heavy_compression")

    # Rule 4: Artificial / synthetic uniform noise field
    # (Unnatural Gaussian noise has kurtosis near 0, low spatial heterogeneity < 0.08, std > 2.0)
    if noise_features is not None:
        try:
            n_std = float(noise_features[1])
            n_kurt = float(noise_features[3])
            n_het = float(noise_features[5])
            if n_std > 2.0 and n_het < 0.08 and abs(n_kurt) < 2.0:
                if "noise_uniform" not in reasons:
                    reasons.append("noise_uniform")
        except Exception:
            pass

    # Rule 5: Significant signal disagreement
    # E.g. probe says 0.85 (AI) but frequency/noise says 0.2 (Real), or vice versa
    if probe_score is not None and forensic_score is not None:
        diff = abs(probe_score - forensic_score)
        if diff >= disagreement_threshold:
            reasons.append("signals_disagree")

    gate_triggered = len(reasons) > 0
    return gate_triggered, reasons
