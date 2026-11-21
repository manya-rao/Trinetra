# Trinetra Eye 3 (ai_lane) — Model Card

## Model Details
- **Developer**: Team Kinetix (Code for Innovex '26, Navyug)
- **Model Name**: Trinetra Multimodal Synthesis Classifier (`ai_lane`)
- **Version**: 1.0.0
- **Type**: Calibrated Logistic-Regression Fusion on frozen OpenCLIP ViT-B-32 embeddings + 2D FFT azimuthal spectrum + spatial noise residual/ELA + metadata heuristics
- **Shipped artifact**: `ml/models/ai_lane.joblib` (≈2.5 MB)
- **CPU inference latency**: 113 ms (mean, standard CPU)

## Intended Use
Eye 3 (Synthesis Engine) of the Trinetra Provenance Passport.
Outputs one of three bands: `likely_real_looking`, `inconclusive`, `likely_ai`.
Never outputs `confirmed` — that is reserved for cryptographic C2PA / watermark evidence.

## Training Data
- Generators seen during training: Stable Diffusion, Midjourney, DALL-E (400 each)
- Held-out generator (zero samples seen during training **or threshold tuning**): Flux
- Photographic baseline: 400 public internet images (**no phone/DSLR photos**)
- Preprocessing: 384×384 center-crop, JPEG Q95 recompression, sRGB conversion, metadata stripped
- **User data**: Not included. Only 1 user image was available (`ml/data/user/misflagged_01.jpg`), below the 100-image minimum to constitute a usable split.

## Evaluation Summary (held-out cross-generator)
- Real-image FPR (bands): **1.00%** (target ≤1%) — measured on 100 public-dataset held-out reals, NOT phone photos
- Flux detection rate: **0.00%** (0/400) — conservative: novel generators → Inconclusive
- Real inconclusive rate: **60.00%** (60/100) — wide safety band by design
- Validation ROC-AUC: 0.971 (in-distribution only)

## Ethical Considerations
- False-positive minimisation is the primary design objective.
- Output bands replace raw probabilities; no bare percentage is ever shown.
- Heavy-compression images (JPEG Q≤75) are gated to Inconclusive to protect journalists.
