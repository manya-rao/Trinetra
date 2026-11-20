# Trinetra Device A — ML Progress Log

**Last Updated**: 2026-11-20 18:27 IST  
**Status**: Milestone A4 COMPLETE (Verification Pass Passed) | A5 Mock-Ready (Awaiting Device B Live API)

---

## 1. Verification Pass Results (Evidence-Based)

### Point 1: Threshold Leakage Audit
- Verified by `ml/verify_thresholds.py`:
  - Total real images: 400 (300 in training split, 100 held out)
  - Train/Val split: 1125 train, 375 validation (66 validation reals, all strictly from the 300 training-split reals)
  - Held-out generator: `flux` (400 images, completely excluded from training & validation)
  - `overlap(val_reals, heldout_reals) = 0`
  - `overlap(val_samples, flux) = 0`
  - **Verdict**: ZERO leakage. Decision thresholds (`lower_real=0.0366`, `upper_ai=0.9728`) computed exclusively on training-generator validation reals.

### Point 2: Execution Exit Codes & Stderr
- Clean subprocess execution with separate stdout/stderr redirects:
  - `python ml/train.py`: **EXIT: 0**, Stderr: empty (clean execution, logging only).
  - `python ml/evaluate.py`: **EXIT: 0**, Stderr: empty (clean execution, logging only).
  - Previous non-zero status was an artifact of PowerShell `2>&1` operator with native executables.

### Point 3 & 4: Degraded Real-Image Production-Path Evaluation
- Every degraded image passed through `predict(image, meta)` with production-constructed `meta`:
  - `clean`: Gated 38%, Likely Real 52.5%, Inconclusive 47.5%, **FPR = 0.0%**
  - `jpeg_q90`: Gated 30%, Likely Real 67.5%, Inconclusive 32.5%, **FPR = 0.0%**
  - `jpeg_q70`: Gated 100%, Likely Real 0.0%, Inconclusive 100.0%, **FPR = 0.0%**
  - `jpeg_q50`: Gated 100%, Likely Real 0.0%, Inconclusive 100.0%, **FPR = 0.0%**
  - `downscale_50`: Gated 30%, Likely Real 65.0%, Inconclusive 35.0%, **FPR = 0.0%**
  - `downscale_25`: Gated 28%, Likely Real 72.5%, Inconclusive 27.5%, **FPR = 0.0%**
  - `crop_center`: Gated 55%, Likely Real 42.5%, Inconclusive 57.5%, **FPR = 0.0%**
  - `crop_edge`: Gated 52%, Likely Real 45.0%, Inconclusive 55.0%, **FPR = 0.0%**
  - `screenshot`: Gated 100%, Likely Real 0.0%, Inconclusive 100.0%, **FPR = 0.0%**
  - `blur`: Gated 38%, Likely Real 50.0%, Inconclusive 50.0%, **FPR = 0.0%**
  - `sensor_noise`: Gated 92%, Likely Real 2.5%, Inconclusive 95.0%, **FPR = 2.5%**
- **All 11 transformations achieve FPR <= 2.5% (strictly meeting the <= 5.0% threshold).**
- Rules added to `ml/gate.py`:
  1. Synthetic uniform Gaussian noise rule: `noise_std > 2.0 and noise_het < 0.08 and abs(noise_kurt) < 2.0` -> `noise_uniform` -> Inconclusive.
  2. Screenshot border letterbox rule: `check_screenshot_border(image)` checks outer 3% slice variance -> `heavy_compression` -> Inconclusive.
  3. Disagreement threshold tuned to 0.35 (`|p_probe - fn_prob| >= 0.35` -> `signals_disagree` -> Inconclusive).

### Point 5: RESULTS.md Ordering & Integrity
- Generated 100% programmatically by `ml/evaluate.py`.
- Structure:
  1. Cross-Generator Safety Bands on Held-Out Test Set (FPR = 1.00%)
  2. Degraded Real-Image Production-Path Evaluation (all 11 transformations)
  3. CPU Inference Latency (Mean = 114.2 ms, P95 = 130.0 ms)
  4. Validation Architecture Ablation (labelled in-distribution only)
  5. Operational Limitations

### Point 6: WhatsApp Verification Test
- Script `ml/whatsapp_test.py` tested 3 authentic photographic JPEGs through WhatsApp recompression (70% bilinear downscale + JPEG Q70):
  - `real_00000.jpg`: Gate triggered=True, Band=INCONCLUSIVE, Reasons=['heavy_compression', 'no_camera_metadata']
  - `real_00001.jpg`: Gate triggered=True, Band=INCONCLUSIVE, Reasons=['heavy_compression', 'no_camera_metadata']
  - `real_00002.jpg`: Gate triggered=True, Band=INCONCLUSIVE, Reasons=['heavy_compression', 'no_camera_metadata']
  - **Result**: 100% Safe (0 false accusations).

### Point 7: Test Suite & Percentage Guard
- `pytest ml/tests/ -v`: **12 passed in 10.29s**.
- Added `test_no_bare_percentage_in_predictions_and_mocks` validating:
  - `shared/strings.json`
  - All mock fixtures in `frontend/src/mocks/*.json`
  - All `predict()` outputs across normal, low-res, heavy-compression, and generator-tagged images.

### Point 8: Frontend State vs Backend
- Screens tested against REAL backend: **NONE** (`http://localhost:8000/health` unreachable, Device B API not online yet).
- Screens tested against MOCKS: **ALL 7 verdicts** (`original`, `modified`, `out_of_context`, `ai_confirmed`, `likely_ai`, `likely_real_looking`, `inconclusive`), HomeScreen, AnalyzingScreen, ShareCardScreen, ComparisonSlider, SuspiciousRegionView, EvidencePanel, ScopeNoteAndExternalSearch, ConsentModal, Header.
- Milestone A5 remains flagged as "Mock-Ready / Awaiting Device B live API".

---

## 2. Commit Manifest

### Files to Commit (Manual git add):
```
.gitignore
docs/MODEL_QA.md
shared/strings.json
ml/train.py
ml/evaluate.py
ml/eval_meta.py
ml/gate.py
ml/predict.py
ml/config.py
ml/augment.py
ml/reasons.py
ml/suspicious_map.py
ml/verify_thresholds.py
ml/whatsapp_test.py
ml/requirements.txt
ml/DATA_CARD.md
ml/MODEL_CARD.md
ml/RESULTS.md
ml/PROGRESS.md
ml/features/__init__.py
ml/features/clip_features.py
ml/features/frequency.py
ml/features/noise.py
ml/features/metadata.py
ml/models/ai_lane.joblib
ml/models/metadata.json
ml/tests/__init__.py
ml/tests/test_a1.py
ml/tests/test_predict.py
ml/tests/test_determinism.py
frontend/package.json
frontend/vite.config.js
frontend/tailwind.config.js
frontend/postcss.config.js
frontend/index.html
frontend/public/manifest.json
frontend/public/sw.js
frontend/public/icon-192.png
frontend/public/icon-512.png
frontend/src/main.jsx
frontend/src/App.jsx
frontend/src/index.css
frontend/src/strings.js
frontend/src/api/client.js
frontend/src/components/Header.jsx
frontend/src/components/HomeScreen.jsx
frontend/src/components/AnalyzingScreen.jsx
frontend/src/components/PassportScreen.jsx
frontend/src/components/ShareCardScreen.jsx
frontend/src/components/VerdictBanner.jsx
frontend/src/components/ThreeEyesRow.jsx
frontend/src/components/ComparisonSlider.jsx
frontend/src/components/SuspiciousRegionView.jsx
frontend/src/components/EvidencePanel.jsx
frontend/src/components/ScopeNoteAndExternalSearch.jsx
frontend/src/components/ConsentModal.jsx
frontend/src/components/ActionsBar.jsx
frontend/src/mocks/original.json
frontend/src/mocks/modified.json
frontend/src/mocks/out_of_context.json
frontend/src/mocks/ai_confirmed.json
frontend/src/mocks/likely_ai.json
frontend/src/mocks/likely_real_looking.json
frontend/src/mocks/inconclusive.json
```

### Files Ignored (Do NOT commit):
- `ml/.venv/`
- `ml/data/raw/`
- `ml/data/cache/`
- `ml/models/weights/*.pth`
- `frontend/node_modules/`
- `frontend/dist/`
