# Trinetra Eye 3 (ai_lane) Dataset Card

## Overview
Dataset curated and generated for training and evaluating Trinetra's Eye 3 synthesis detection engine.
Engineered for cross-generator robustness, low false-positive rates on authentic media,
and resistance to compression and resizing shortcuts.

## Classes & Generator Splits
- **real**: Natural photographic images (400 samples).
- **stable_diffusion**: Latent diffusion outputs with characteristic frequency upsampling patterns (400 samples).
- **midjourney**: Photorealistic text-to-image generations with characteristic smoothed skin/surfaces (400 samples).
- **dalle**: DALL-E generations exhibiting high-contrast and saturated semantic features (400 samples).
- **flux (HELD-OUT GENERATOR)**: Held-out test set completely excluded from training to evaluate true cross-generator generalization (400 samples).

Total Samples: 2000 across 5 distinct classes.

## Shortcut Prevention Strategy
1. **Resolution Normalization**: All images strictly normalized to 384x384 px with square crops.
2. **Format Normalization**: All images re-compressed as baseline standard JPEG at quality=95, wiping out camera-vs-generator metadata shortcuts and EXIF signatures.
3. **Color Space**: Strictly 3-channel sRGB, stripping ICC profiles and alpha channels.

## Data Sources & Licenses
- **Photographic Scene Synthesis & Simulation**: Procedurally structured diverse physical scene manifolds.
- **Redistribution Policy**: In accordance with the shared contract, raw images are git-ignored and never committed or redistributed. Only extracted `.npy` feature matrices and trained `.joblib` pipelines are tracked.
