"""
Phase 1 Diagnosis Script: Inspect misflagged camera photo (read only).
Runs full inspection and predict() on original image vs 384x384 resized image.
"""
import sys
import os
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "backend"))

import numpy as np
from PIL import Image, ExifTags
from ml.config import (
    MODEL_FILE,
    PROB_LOWER_REAL_BAND,
    PROB_UPPER_AI_BAND,
    MIN_IMAGE_DIM,
    HEAVY_COMPRESSION_JPEG_QUALITY,
)
from ml.gate import evaluate_gate, check_screenshot_border
from ml.features.clip_features import extract_clip_embedding
from ml.features.frequency import extract_frequency_features
from ml.features.noise import extract_noise_features
from ml.features.metadata import extract_metadata_features
from ml.predict import predict, get_model_bundle, extract_jpeg_quality

def get_exif_info(img: Image.Image):
    raw_exif = img.getexif()
    has_exif = bool(raw_exif and len(raw_exif) > 0)
    make = None
    model = None
    exposure_fields = {}
    if has_exif:
        make = raw_exif.get(271)  # Make
        model = raw_exif.get(272)  # Model
        try:
            ifd = raw_exif.get_ifd(ExifTags.IFD.Exif)
            for k, v in ifd.items():
                tag_name = ExifTags.TAGS.get(k, str(k))
                if any(x in tag_name.lower() for x in ["exposure", "iso", "fnumber", "shutter", "focal"]):
                    exposure_fields[tag_name] = str(v)
        except Exception:
            pass
    return has_exif, make, model, exposure_fields

def build_production_meta(image_path: Path, img: Image.Image):
    file_size = image_path.stat().st_size
    img_w, img_h = img.size
    has_exif, make, model, exposure = get_exif_info(img)

    computed_q = extract_jpeg_quality(img)
    jpeg_quality = computed_q

    meta = {
        "width": img_w,
        "height": img_h,
        "file_size": file_size,
        "jpeg_quality": jpeg_quality,
        "has_exif": has_exif,
        "generator_tag": None,
    }
    return meta, make, model, exposure

def diagnose_image(img: Image.Image, meta: dict, label: str):
    bundle = get_model_bundle()
    if bundle is None:
        raise RuntimeError("Model bundle not found!")

    t_lower = bundle.get("threshold_lower", PROB_LOWER_REAL_BAND)
    t_upper = bundle.get("threshold_upper", PROB_UPPER_AI_BAND)

    w = meta["width"]
    h = meta["height"]
    jq = meta["jpeg_quality"]

    # 1. Gate evaluation pre-model
    is_border = check_screenshot_border(img)
    gate1_trig, gate1_reasons = evaluate_gate(
        width=w, height=h, jpeg_quality=jq, image=img
    )

    # 2. Extract features
    img_rgb = img.convert("RGB")
    clip_emb = extract_clip_embedding(img_rgb)
    freq_feat = extract_frequency_features(img_rgb)
    noise_feat = extract_noise_features(img_rgb)
    meta_feat = extract_metadata_features(img_rgb, meta)

    # 3. CLIP Probe
    c_scaled = bundle["clip_scaler"].transform(clip_emb[None, :])
    clip_probe_score = float(bundle["clip_probe"].predict_proba(c_scaled)[0, 1])

    # 4. Forensic (Frequency + Noise) Classifier
    fn_feat = np.concatenate([freq_feat, noise_feat])[None, :]
    fn_scaled = bundle["forensic_scaler"].transform(fn_feat)
    forensic_score = float(bundle["forensic_clf"].predict_proba(fn_scaled)[0, 1])

    # 5. Disagreement Gate Check
    disagreement_threshold = 0.35
    gate_disagree, disagree_reasons = evaluate_gate(
        width=w,
        height=h,
        probe_score=clip_probe_score,
        forensic_score=forensic_score,
        disagreement_threshold=disagreement_threshold,
        noise_features=noise_feat,
        image=img,
    )

    # 6. Multimodal Fusion
    fus_in = np.concatenate([
        np.array([[clip_probe_score]]),
        np.array([[forensic_score]]),
        fn_scaled[:, :10],
        fn_scaled[:, 70:80],
        meta_feat[None, :]
    ], axis=1)
    fusion_score = float(bundle["fusion_model"].predict_proba(fus_in)[0, 1])
    t_lower = bundle["thresholds"]["lower_real"]
    t_upper = bundle["thresholds"]["upper_ai"]

    # 7. Actual predict() call
    full_predict_res = predict(img, meta)

    return {
        "label": label,
        "width": w,
        "height": h,
        "file_size": meta["file_size"],
        "jpeg_quality": jq,
        "has_exif": meta["has_exif"],
        "clip_probe_score": clip_probe_score,
        "forensic_score": forensic_score,
        "fusion_score": fusion_score,
        "threshold_lower": t_lower,
        "threshold_upper": t_upper,
        "gate_initial_triggered": gate1_trig,
        "gate_initial_reasons": gate1_reasons,
        "gate_disagree_triggered": gate_disagree,
        "gate_disagree_reasons": disagree_reasons,
        "final_band": full_predict_res["band"],
        "final_reasons": [r["key"] for r in full_predict_res["reasons"]],
        "final_gate_triggered": full_predict_res["gate_triggered"],
    }

def main():
    target_path = root_dir / "ml" / "data" / "user" / "misflagged_01.jpg"
    if not target_path.exists():
        print(f"Error: {target_path} does not exist.")
        sys.exit(1)

    orig_img = Image.open(target_path)
    orig_meta, make, model, exposure = build_production_meta(target_path, orig_img)

    print("==================================================================")
    print("PHASE 1: DIAGNOSE (READ-ONLY) - REAL CAMERA PHOTO INVESTIGATION")
    print("Target Image:", target_path)
    print(f"Camera EXIF: Make='{make}', Model='{model}'")
    print("Sample Exposure Fields:", list(exposure.items())[:4])
    print("==================================================================\n")

    # Diagnose Original
    print("Running diagnostic on ORIGINAL image...")
    diag_orig = diagnose_image(orig_img, orig_meta, "Original (Full Resolution)")

    # Diagnose Resized (384x384)
    print("Running diagnostic on RESIZED (384x384) image...")
    resized_img = orig_img.resize((384, 384), Image.Resampling.BICUBIC)
    resized_meta = {
        "width": 384,
        "height": 384,
        "file_size": orig_meta["file_size"],
        "jpeg_quality": orig_meta["jpeg_quality"],
        "has_exif": orig_meta["has_exif"],
        "generator_tag": None,
    }
    diag_resized = diagnose_image(resized_img, resized_meta, "Resized (384x384)")

    # Side-by-side Table
    print("\n" + "="*80)
    print(f"{'METRIC / PARAMETER':<35} | {'ORIGINAL (FULL RES)':<20} | {'RESIZED (384x384)':<20}")
    print("="*80)
    dim_orig_str = f"{diag_orig['width']}x{diag_orig['height']}"
    dim_res_str = f"{diag_resized['width']}x{diag_resized['height']}"
    print(f"{'Dimensions':<35} | {dim_orig_str:<20} | {dim_res_str:<20}")
    print(f"{'File Size (bytes)':<35} | {diag_orig['file_size']:<20} | {diag_resized['file_size']:<20}")
    print(f"{'Estimated JPEG Quality':<35} | {str(diag_orig['jpeg_quality']):<20} | {str(diag_resized['jpeg_quality']):<20}")
    print(f"{'Has EXIF':<35} | {str(diag_orig['has_exif']):<20} | {str(diag_resized['has_exif']):<20}")
    print(f"{'Camera Make':<35} | {str(make):<20} | {str(make):<20}")
    print(f"{'Camera Model':<35} | {str(model):<20} | {str(model):<20}")
    print("-"*80)
    print(f"{'CLIP Probe Score (p_ai)':<35} | {diag_orig['clip_probe_score']:<20.4f} | {diag_resized['clip_probe_score']:<20.4f}")
    print(f"{'Forensic Score (Freq+Noise)':<35} | {diag_orig['forensic_score']:<20.4f} | {diag_resized['forensic_score']:<20.4f}")
    print(f"{'Fusion Score':<35} | {diag_orig['fusion_score']:<20.4f} | {diag_resized['fusion_score']:<20.4f}")
    print(f"{'Threshold Lower (Real band)':<35} | {diag_orig['threshold_lower']:<20.4f} | {diag_resized['threshold_lower']:<20.4f}")
    print(f"{'Threshold Upper (AI band)':<35} | {diag_orig['threshold_upper']:<20.4f} | {diag_resized['threshold_upper']:<20.4f}")
    print("-"*80)
    print(f"{'Gate Initial Triggered':<35} | {str(diag_orig['gate_initial_triggered']):<20} | {str(diag_resized['gate_initial_triggered']):<20}")
    print(f"{'Gate Disagree Triggered':<35} | {str(diag_orig['gate_disagree_triggered']):<20} | {str(diag_resized['gate_disagree_triggered']):<20}")
    print(f"{'Gate Disagree Reasons':<35} | {str(diag_orig['gate_disagree_reasons']):<20} | {str(diag_resized['gate_disagree_reasons']):<20}")
    print(f"{'Final Output Band':<35} | {diag_orig['final_band']:<20} | {diag_resized['final_band']:<20}")
    print(f"{'Final Output Reasons':<35} | {str(diag_orig['final_reasons']):<20} | {str(diag_resized['final_reasons']):<20}")
    print("="*80)

if __name__ == "__main__":
    main()
