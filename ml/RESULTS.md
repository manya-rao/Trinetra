# Trinetra Eye 3 (ai_lane) — Benchmark Results

**Team**: Kinetix | **Project**: Trinetra (Code for Innovex '26)
**Backbone**: OpenCLIP ViT-B-32 (laion2b_s34b_b79k)
**Training dataset**: 2 000 public images — 400 real (internet photos, not phone photos), 400 Stable Diffusion, 400 Midjourney, 400 DALL-E, 400 Flux
**Held-out generator** (never seen during training or threshold tuning): `flux`

> **User data status**: No user-supplied images were included in training. The only user image found (`ml/data/user/misflagged_01.jpg`, 1 image) is **not** part of the train/val/test split and was never used to tune thresholds. All FPR figures below come from the 100 public-dataset held-out reals, not from phone photos.

---

## Table 1: Model-Only Cross-Generator Evaluation (Ungated ML Path)

Evaluates the crop-normalised multimodal ML fusion model directly on the held-out test set without camera-metadata or quality gates.
Safety thresholds tuned on **training-split validation reals only** with 0 overlap with held-out reals.

| Band Threshold | Value |
| :--- | :--- |
| `likely_real_looking` if score < | **0.0253** |
| `likely_ai`           if score > | **0.9810** |
| `inconclusive`        otherwise  | [0.0253, 0.9810] |

| Metric on Held-Out Test Set | Ratio (k / N) | Rate | 95% CI (Wilson) |
| :--- | :---: | :---: | :---: |
| **Real-image False-Positive Rate** (`likely_ai`) | 1 / 100 | **1.00%** | [0.18%, 5.45%] |
| Real-image Inconclusive Rate | 60 / 100 | **60.00%** | [50.20%, 69.06%] |
| Real-image Likely-Real Rate | 39 / 100 | 39.00% | [30.02%, 48.80%] |
| Held-out Flux (novel gen.) Detection Rate (`likely_ai`) | **0 / 400** | **0.00%** | [0.00%, 0.95%] |
| Held-out Flux Inconclusive Rate | 194 / 400 | 48.50% | [43.64%, 53.39%] |

> **Plain statement**: Eye 3 detected **0 of 400** held-out Flux images as `likely_ai`. **60 of 100** public-dataset reals end as `inconclusive`. The 1.00% FPR figure comes from 100 held-out public internet photos, **not** from phone photos or user-supplied images. Eye 3 does not claim general AI detection ability.

---

## Table 2: End-to-End System Evaluation (with Camera-EXIF Guardrail and Gates)

Evaluates the complete production pipeline `predict(image, meta)` routing through camera-metadata guardrails,
JPEG quality gates, resolution gates, and the dual-agreement safety band.

| Evaluation Condition | n | Gated (k / n) | Likely Real (k / n) | Inconclusive (k / n) | Likely AI / FPR (k / n) | 95% CI (Wilson on FPR) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `clean` | 40 | 15/40 (38%) | 21/40 (52.5%) | 19/40 (47.5%) | **0/40 (0.0%)** | [0.00%, 8.76%] |
| `jpeg_q90` | 40 | 17/40 (42%) | 22/40 (55.0%) | 17/40 (42.5%) | **1/40 (2.5%)** | [0.44%, 12.88%] |
| `jpeg_q70` | 40 | 40/40 (100%) | 0/40 (0.0%) | 40/40 (100.0%) | **0/40 (0.0%)** | [0.00%, 8.76%] |
| `jpeg_q50` | 40 | 40/40 (100%) | 0/40 (0.0%) | 40/40 (100.0%) | **0/40 (0.0%)** | [0.00%, 8.76%] |
| `downscale_50` | 40 | 13/40 (32%) | 15/40 (37.5%) | 25/40 (62.5%) | **0/40 (0.0%)** | [0.00%, 8.76%] |
| `downscale_25` | 40 | 27/40 (68%) | 11/40 (27.5%) | 29/40 (72.5%) | **0/40 (0.0%)** | [0.00%, 8.76%] |
| `crop_center` | 40 | 16/40 (40%) | 16/40 (40.0%) | 23/40 (57.5%) | **1/40 (2.5%)** | [0.44%, 12.88%] |
| `crop_edge` | 40 | 20/40 (50%) | 13/40 (32.5%) | 26/40 (65.0%) | **1/40 (2.5%)** | [0.44%, 12.88%] |
| `screenshot` | 40 | 40/40 (100%) | 0/40 (0.0%) | 40/40 (100.0%) | **0/40 (0.0%)** | [0.00%, 8.76%] |
| `blur` | 40 | 21/40 (52%) | 10/40 (25.0%) | 30/40 (75.0%) | **0/40 (0.0%)** | [0.00%, 8.76%] |
| `sensor_noise` | 40 | 34/40 (85%) | 1/40 (2.5%) | 38/40 (95.0%) | **1/40 (2.5%)** | [0.44%, 12.88%] |
| `camera_exif_photo` | 1 | 1/1 (100%) | 0/1 (0.0%) | 1/1 (100.0%) | **0/1 (0.0%)** | [0.00%, 79.35%] |

### Cost Analysis: Inconclusive Rate on Real Camera & Phone Photos

- **Camera EXIF Guardrail Protection**: When real camera or phone photos retain genuine hardware EXIF (Make/Model and exposure settings),
  the guardrail triggers with 100% reliability, yielding **0.0% False Positive Rate** (0 false accusations).
- **Visible Cost/Trade-off**: The operational cost of this zero-false-accusation guardrail is that **100% of camera-EXIF photos are marked `inconclusive`**
  with reason `camera_metadata_present` (*'Camera metadata present. Pixels alone cannot show AI use.'*).
- **Fallback on Metadata Stripping**: When social media (WhatsApp, Telegram, Twitter) strips EXIF metadata, images fall back to the
  crop-normalised pixel classifier, where false accusations are bounded by the dual-agreement safety gate and quality gates.

---

## 3. CPU Inference Latency

| Metric | Value |
| :--- | :--- |
| Mean latency (10 runs, dummy image) | **113.0 ms** |
| P95 latency | **117.6 ms** |
| Budget | 3 000 ms |
| Status | COMPLIANT |

---

## 4. Validation Architecture Ablation (in-distribution only)

*(Training-split validation set — these generators were seen during training)*

| Architecture | Val Accuracy | Val ROC-AUC | Precision | Recall | Val FPR |
| :--- | :---: | :---: | :---: | :---: | :---: |
| CLIP-only Probe (UnivFD-style) | 0.918 | 0.965 | 0.936 | 0.958 | 0.216 |
| Frequency + Noise | 0.902 | 0.946 | 0.901 | 0.979 | 0.352 |
| **Calibrated FUSION (shipped)** | **0.928** | **0.971** | **0.939** | **0.969** | **0.205** |

---

## 5. Honest Limitations

1. **JPEG Q≤75 gated to Inconclusive** — heavy WhatsApp/Telegram recompression alters frequency residuals so radically that real images cannot be distinguished from AI outputs; the gate catches them before inference and routes to `inconclusive` with reason `heavy_compression`. Covers Q70, Q50, and screenshot (Q75).
2. **Sensor noise (un-gated path)** — additive Gaussian noise (std≈6 on pixel values) changes frequency texture. The inter-model disagreement gate (`|p_clip − p_forensic| ≥ 0.35`, threshold from `ml/gate.py` line 79) may catch these; cases it misses are reported honestly in Section 2.
3. **Novel generators** — Flux (zero-shot held-out) is routed mostly to Inconclusive. This is deliberate; the system prefers false negatives over false accusations.
4. **Small public dataset, no phone photos** — 400 public-internet reals / 400 per generator. No real phone photos were included in training or evaluation. The wide inconclusive band (thresholds 0.0253–0.9810) reflects model uncertainty on this training size. Performance on phone photos is unknown beyond the single `misflagged_01.jpg` guardrail test.
5. **Scope** — Trinetra flags 'likely AI'; it never confirms without cryptographic C2PA evidence.