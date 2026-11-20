# Trinetra Eye 3 (Synthesis Engine & AI Image Detector)

**Team**: Kinetix | **Project**: Trinetra (Digital Trust & Provenance)
**Event**: Code for Innovex '26 | **Theme**: "Navyug - A New Era"
**Device**: Device A

---

## 1. Overview
The `ml/` subsystem houses the trained "heart" of **Eye 3 (Synthesis)** in the Trinetra Provenance Passport.
Unlike conventional binary AI detectors that produce brittle percentages, Eye 3 evaluates multimodal forensic signals:
1. **Semantic Embeddings**: Frozen OpenCLIP `ViT-B-32` backbone (512-dim, L2-normalized).
2. **Frequency-Domain Analysis**: 2D FFT, log-magnitude power spectrum, azimuthal (radial) average into 64 bins, and periodic peak prominence statistics.
3. **Spatial Noise & Inconsistency**: High-pass noise residual (median filter subtraction), 8x8 spatial grid kurtosis/std, global noise skew/kurtosis, and Error Level Analysis (ELA) variance.
4. **Metadata Forensics**: Camera EXIF presence, missing metadata heuristics, and unsigned AI generator tag detection.
5. **Multimodal Fusion & Probability Calibration**: Platt scaling / Sigmoid probability calibration with tuned decision thresholds.

---

## 2. Frozen Contract Interface (Used by Device B)

```python
from PIL import Image
from ml.predict import predict

# Example call
image = Image.open("suspicious.jpg")
meta = {
    "width": image.width,
    "height": image.height,
    "file_size": 150000,
    "jpeg_quality": 85.0,
    "has_exif": True,
    "generator_tag": None
}

result = predict(image, meta)
```

### Result Schema
```json
{
  "band": "likely_real_looking | inconclusive | likely_ai",
  "reasons": [
    {
      "key": "spectrum_peaks",
      "en": "Periodic frequency peaks characteristic of generative upsampling filters.",
      "hi": "आवृत्ति स्पेक्ट्रम में एआई अपसैंपलिंग से जुड़े आवधिक शिखर पाए गए।"
    }
  ],
  "gate_triggered": false,
  "suspicious_map_png": "<bytes | None>"
}
```

### Guaranteed Properties
- **Zero Percentages**: Never returns a raw probability percentage.
- **Inference Latency**: Under 3 seconds on standard CPU.
- **Safety Gate**: Triggers `inconclusive` when resolution < 256x256, severe recompression is detected, or semantic and forensic signals disagree strongly.
- **Confirmation Ladder**: Unsigned metadata tags can only contribute to `likely_ai`; "confirmed" is reserved strictly for Device B's cryptographic C2PA pipeline.

---

## 3. How to Retrain and Evaluate

### Activate Python Environment
```powershell
.\ml\.venv\Scripts\activate
```

### Run Full Test Suite
```powershell
$env:PYTHONPATH="."
pytest ml/tests/ -v
```

### Feature Extraction & Caching
```powershell
python ml/features/extract_cache.py
```

### Train Models & Calibrate Thresholds
```powershell
python ml/train.py
```

### Run Robustness & Latency Benchmarks
```powershell
python ml/evaluate.py
```
Outputs are written to `ml/RESULTS.md`, `ml/MODEL_CARD.md`, and `docs/MODEL_QA.md`.
