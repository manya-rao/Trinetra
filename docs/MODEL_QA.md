# Trinetra Eye 3 — Judge & Technical Q&A Defence

### Q1  Why not a commercial detector or fine-tuned ResNet?
Trinetra addresses *all three* steps of a misinformation pipeline (Origin / Change / Synthesis),
not only AI detection. Fine-tuned single-modal CNNs overfit to training-generator artifacts
and collapse on social-media re-compression. Our multimodal fusion combines semantic
(OpenCLIP ViT-B-32) and physics-based (2D FFT azimuthal + noise residual) signals.

### Q2  What accuracy do you get on completely unseen generators?
We held out **Flux** entirely from training and threshold selection.
Verification script `ml/verify_thresholds.py` confirms zero-overlap.
On held-out test set (100 public-dataset reals, 400 Flux images):
- Real-image false-positive rate: **1.00%** — measured on 100 public internet photos; **not** validated on phone photos
- Flux detection rate: **0.00%** (0/400) — Eye 3 did not detect any held-out Flux image as `likely_ai`
- Flux inconclusive rate: 48.5%  ← deliberate safe fallback
- Real inconclusive rate: **60.0%** (60/100) — this is the visible cost of the conservative safety band

### Q3  How do you handle WhatsApp/Telegram compression?
Images re-encoded at JPEG Q≤75 are **gated to Inconclusive** before feature extraction
(reason: `heavy_compression`). This covers Q70, Q50 and our screenshot simulation (Q75).
Gated rate on Q50 test images: 100%; residual FPR: 0.0%.

### Q4  Why no confidence percentage in the UI?
Raw calibrated probabilities are scientifically misleading after social-media re-encoding.
We output three discrete calibrated bands (`likely_real_looking` / `inconclusive` / `likely_ai`)
with plain-language forensic reasons, in line with the Confirmation Ladder principle.

### Q5  How fast is inference?
Mean 113 ms on standard CPU, well under the 3 000 ms budget.
The frozen ViT-B-32 backbone dominates cost; numpy FFT/noise steps add ≈76 ms.

### Q6  What about sensor-noise-added images?
Additive sensor noise with std≈6 (pixel values) is not caught by the JPEG gate.
The inter-model disagreement gate (`|p_clip − p_forensic| ≥ 0.35`, threshold in `ml/gate.py`) handles some cases.
Production FPR on the sensor_noise test: 2.5% (gated 85%).
Images in this band are reported with reason `signals_disagree` and routed to Inconclusive
when the disagreement fires. When it does not, the false accusation rate is as reported.
This is documented as a known limitation; screenshot-originating PNGs (no EXIF, no Q hint)
are the worst case.
