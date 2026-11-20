"""
Trinetra Eye 3 (Synthesis Engine) Inference Interface.
Frozen Contract provided to Device B:

    from ml.predict import predict
    predict(image: PIL.Image, meta: dict) -> {
      "band": "likely_real_looking|inconclusive|likely_ai",
      "reasons": [{"key": str, "en": str, "hi": str}],
      "gate_triggered": bool,
      "suspicious_map_png": bytes | None
    }

meta keys: width, height, file_size, jpeg_quality (float|None), has_exif (bool), generator_tag (str|None).
Never returns a percentage. Loads the model once. Under ~3 s per image on CPU.
"""
import io
import time
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np
import joblib

from ml.config import MODEL_FILE, METADATA_FILE
from ml.gate import evaluate_gate
from ml.reasons import format_reasons
from ml.suspicious_map import generate_suspicious_map
from ml.features.clip_features import extract_clip_embedding
from ml.features.frequency import extract_frequency_features
from ml.features.noise import extract_noise_features
from ml.features.metadata import extract_metadata_features

# Global model cache (loaded once)
_MODEL_BUNDLE = None

def get_model_bundle():
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is None and MODEL_FILE.exists():
        try:
            _MODEL_BUNDLE = joblib.load(MODEL_FILE)
        except Exception as e:
            _MODEL_BUNDLE = None
    return _MODEL_BUNDLE

def predict(image: Image.Image, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Inference entrypoint for Eye 3 (Synthesis Detector).
    Matches frozen shared contract.
    """
    if meta is None:
        meta = {}

    w, h = image.size
    meta_width = meta.get("width", w)
    meta_height = meta.get("height", h)
    jpeg_quality = meta.get("jpeg_quality")
    has_exif = meta.get("has_exif", True)
    generator_tag = meta.get("generator_tag")

    # Initial Gate Evaluation (resolution, severe compression, screenshot borders)
    gate_triggered, gate_reasons = evaluate_gate(
        width=meta_width,
        height=meta_height,
        jpeg_quality=jpeg_quality,
        image=image
    )

    reasons_keys = list(gate_reasons)

    # Check unsigned metadata generator tags
    if generator_tag:
        reasons_keys.append("generator_tag_found")

    if not has_exif:
        reasons_keys.append("no_camera_metadata")

    bundle = get_model_bundle()

    if bundle is None or gate_triggered:
        # Fallback to safe inconclusive band
        band = "inconclusive"
        suspicious_map = None
        if not gate_triggered and min(w, h) >= 128:
            try:
                suspicious_map = generate_suspicious_map(image)
            except Exception:
                suspicious_map = None
    else:
        try:
            # 1. Feature extraction
            img_rgb = image.convert("RGB")
            clip_emb = extract_clip_embedding(img_rgb)
            freq_feat = extract_frequency_features(img_rgb)
            noise_feat = extract_noise_features(img_rgb)
            meta_feat = extract_metadata_features(img_rgb, meta)

            # 2. Individual sub-models
            c_scaled = bundle["clip_scaler"].transform(clip_emb[None, :])
            p_prob = float(bundle["clip_probe"].predict_proba(c_scaled)[0, 1])

            fn_feat = np.concatenate([freq_feat, noise_feat])[None, :]
            fn_scaled = bundle["forensic_scaler"].transform(fn_feat)
            fn_prob = float(bundle["forensic_clf"].predict_proba(fn_scaled)[0, 1])

            # 3. Disagreement and Synthetic Noise Check (Gate Rules 3, 4, 5)
            gate_disagree, disagree_reasons = evaluate_gate(
                width=meta_width,
                height=meta_height,
                probe_score=p_prob,
                forensic_score=fn_prob,
                disagreement_threshold=0.35,
                noise_features=noise_feat,
                image=image
            )

            if gate_disagree:
                gate_triggered = True
                reasons_keys.extend(disagree_reasons)
                band = "inconclusive"
            else:
                # 4. Multimodal Fusion Model
                fus_in = np.concatenate([
                    np.array([[p_prob]]),
                    np.array([[fn_prob]]),
                    fn_scaled[:, :10],
                    fn_scaled[:, 70:80],
                    meta_feat[None, :]
                ], axis=1)

                calibrated_score = float(bundle["fusion_model"].predict_proba(fus_in)[0, 1])

                lower_thresh = bundle["thresholds"]["lower_real"]
                upper_thresh = bundle["thresholds"]["upper_ai"]

                if calibrated_score < lower_thresh:
                    band = "likely_real_looking"
                elif calibrated_score > upper_thresh:
                    band = "likely_ai"
                else:
                    band = "inconclusive"

                # 5. Populate specific forensic reasons
                if p_prob > 0.60:
                    reasons_keys.append("clip_ai_signal")
                # High frequency peak prominence
                if freq_feat[67] > 0.35 or freq_feat[68] > 0.30:
                    reasons_keys.append("spectrum_peaks")
                # Noise pattern uniformity (low spatial heterogeneity)
                if noise_feat[5] < 0.25:
                    reasons_keys.append("noise_uniform")

            # 6. Generate suspicious map
            suspicious_map = generate_suspicious_map(image)

        except Exception as e:
            # Safe degradation fallback
            band = "inconclusive"
            suspicious_map = None

    return {
        "band": band,
        "reasons": format_reasons(reasons_keys),
        "gate_triggered": gate_triggered,
        "suspicious_map_png": suspicious_map
    }
