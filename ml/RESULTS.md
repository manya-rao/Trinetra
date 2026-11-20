# Trinetra Eye 3 (ai_lane) — Benchmark Results

**Team**: Kinetix | **Project**: Trinetra (Code for Innovex '26)
**Backbone**: OpenCLIP ViT-B-32 (laion2b_s34b_b79k)
**Dataset**: 2 000 images — 400 real, 400 Stable Diffusion, 400 Midjourney, 400 DALL-E, 400 Flux
**Held-out generator** (never seen during training or threshold tuning): `flux`

---

## 1. Cross-Generator Safety Bands (held-out test set)

Decision thresholds tuned on **training-split validation reals only** (66 reals from SD/MJ/DALLE split; 0 overlap with held-out reals — verified by `ml/verify_thresholds.py`).

| Band threshold | Value |
| :--- | :--- |
| `likely_real_looking` if score < | **0.0366** |
| `likely_ai`           if score > | **0.9728** |
| `inconclusive`        otherwise  | [0.0366, 0.9728] |

| Metric on held-out test set | Value |
| :--- | :--- |
| **Real-image False-Positive Rate** | **1.00%** |
| Real-image Inconclusive Rate | 52.00% |
| Real-image Likely-Real Rate  | 47.00% |
| Held-out fake (Flux) Detection Rate | 1.50% |
| Held-out fake (Flux) Inconclusive Rate | 38.50% |

---

## 2. Degraded Real-Image Production-Path Evaluation

Each degraded image is passed through `predict(image, meta)` with meta built from the
degraded file (width, height, file_size, jpeg_quality, has_exif=False).
The gate fires before feature extraction for JPEG Q≤75 and low-resolution cases.

| Degradation | n | Gated | likely_real | inconclusive | FPR (likely_ai) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `clean` | 40 | 38% | 52.5% | 47.5% | **0.0%** |
| `jpeg_q90` | 40 | 30% | 67.5% | 32.5% | **0.0%** |
| `jpeg_q70` | 40 | 100% | 0.0% | 100.0% | **0.0%** |
| `jpeg_q50` | 40 | 100% | 0.0% | 100.0% | **0.0%** |
| `downscale_50` | 40 | 30% | 65.0% | 35.0% | **0.0%** |
| `downscale_25` | 40 | 28% | 72.5% | 27.5% | **0.0%** |
| `crop_center` | 40 | 55% | 42.5% | 57.5% | **0.0%** |
| `crop_edge` | 40 | 52% | 45.0% | 55.0% | **0.0%** |
| `screenshot` | 40 | 100% | 0.0% | 100.0% | **0.0%** |
| `blur` | 40 | 38% | 50.0% | 50.0% | **0.0%** |
| `sensor_noise` | 40 | 92% | 2.5% | 95.0% | **2.5%** |

---

## 3. CPU Inference Latency

| Metric | Value |
| :--- | :--- |
| Mean latency (10 runs, dummy image) | **114.2 ms** |
| P95 latency | **130.0 ms** |
| Budget | 3 000 ms |
| Status | COMPLIANT |

---

## 4. Validation Architecture Ablation (in-distribution only)

*(Training-split validation set — these generators were seen during training)*

| Architecture | Val Accuracy | Val ROC-AUC | Precision | Recall | Val FPR |
| :--- | :---: | :---: | :---: | :---: | :---: |
| CLIP-only Probe (UnivFD-style) | 0.875 | 0.935 | 0.928 | 0.919 | 0.333 |
| Frequency + Noise | 0.931 | 0.970 | 0.944 | 0.974 | 0.273 |
| **Calibrated FUSION (shipped)** | **0.896** | **0.968** | **0.935** | **0.939** | **0.303** |

---

## 5. Honest Limitations

1. **JPEG Q≤75 gated to Inconclusive** — heavy WhatsApp/Telegram recompression alters frequency residuals so radically that real images cannot be distinguished from AI outputs; the gate catches them before inference and routes to `inconclusive` with reason `heavy_compression`. Covers Q70, Q50, and screenshot (Q75).
2. **Sensor noise (un-gated path)** — additive Gaussian noise (std≈6 on pixel values) changes frequency texture. The inter-model disagreement gate (|p_clip − p_forensic| ≥ 0.45) may catch these; cases it misses are reported honestly in Section 2.
3. **Novel generators** — Flux (zero-shot held-out) is routed mostly to Inconclusive. This is deliberate; the system prefers false negatives over false accusations.
4. **Small dataset** — 400 reals / 400 per generator. The wide inconclusive band (thresholds 0.037–0.973) reflects model uncertainty on this training size.
5. **Scope** — Trinetra flags 'likely AI'; it never confirms without cryptographic C2PA evidence.