# Trinetra: Digital Trust & Provenance

> **Share any suspicious image and get a Provenance Passport in seconds: where it came from, what was changed, and whether it is likely AI-made.**

* **Team:** Kinetix
* **Event:** Code for Innovex '26
* **Theme:** *Navyug - A New Era*
* **Track:** Misinformation & Provenance ("check where a claim or image came from and whether it was changed")

---

## 👁️ The Three Eyes Architecture

Most viral misinformation consists of authentic images taken out of context (recycled) or lightly edited real images—scenarios where pure AI classifiers fail. **Trinetra** answers origin, modification, and synthetic generation in a single unified pipeline:

1. **Eye 1: Origin** — Is the image known? What was its earliest indexed publication, verified source, and original context?
2. **Eye 2: Change** — Has the image been altered? Keypoint alignment (SIFT/ORB + RANSAC) to the source baseline with SSIM residual diff and localized heatmap bounding boxes.
3. **Eye 3: Synthesis** — Is there evidence of machine generation? Verifiable C2PA Content Credentials, frequency domain spectrum spikes, sensor noise consistency, and visual AI representations.

### The Confirmation Ladder (Strict Contract)
1. **Level 1 (C2PA / Signed Watermark):** `ai_confirmed` — The **only** place the word *"confirmed"* appears.
2. **Level 2 (Indexed Match + Structural Diff):** `modified` — Shows exact bounding boxes and diff heatmap.
3. **Level 3 (Model Signals Agree):** `likely_ai` — Banded confidence with explanatory reasons (never a raw percentage).
4. **Level 4 (Weak / Conflicting / Low-Res):** `inconclusive` — Prefer false negatives over false accusations, providing one-tap Google Lens and TinEye search links.
* **Authentic Unedited:** `original` — Clean provenance with verified source archive link.
* **Negative AI Detector Result:** `likely_real_looking` — Presented neutrally as *"No AI signs found, not proof"*.

---

## 📁 Monorepo Structure & Ownership

```
trinetra/
├── ml/                      # [Device 1] AI detector training & inference (ml.predict)
├── frontend/                # [Device 1] React PWA
├── shared/
│   ├── strings.json         # [Device 1] Multilingual strings (EN / HI)
│   └── fixtures/            # [Device 2] Frozen mock Passport JSON fixtures
│       ├── original.json
│       ├── modified.json
│       ├── ai_confirmed.json
│       ├── likely_ai.json
│       └── inconclusive.json
├── backend/                 # [Device 2] FastAPI service, Origin engine, Diff, C2PA, Aggregator
│   ├── app/
│   │   ├── main.py          # FastAPI application entrypoint & CORS
│   │   ├── config.py        # Config & CV thresholds
│   │   ├── schemas.py       # Pydantic v2 schemas for Passport JSON contract
│   │   ├── strings.py       # Dynamic strings loader with fallback
│   │   ├── storage.py       # Passport cache with TTL expiration
│   │   ├── resources/       # Fallback strings
│   │   └── routers/
│   │       ├── health.py    # GET /health
│   │       ├── analyze.py   # POST /analyze
│   │       ├── passport.py  # GET /passport/{id}, GET /p/{id}, GET /passport/{id}/card.png
│   │       └── match_hash.py# POST /match_hash
│   ├── static/files/        # Derived diff heatmaps, thumbnails, overlays
│   ├── tests/               # Pytest suite
│   ├── requirements.txt     # Python dependencies
│   └── run.py               # Local runner
├── bot/                     # [Device 2] Telegram verification bot
├── extension/               # [Device 2] WhatsApp Web browser extension (Manifest V3)
└── docs/                    # [Device 2] DEPLOY.md, IOS_SHORTCUT.md, RESULTS.md
```

---

## 🚀 Quickstart: Device 2 Backend (FastAPI)

### 1. Requirements
* Python 3.11+
* Windows, Linux, or macOS

### 2. Setup Virtual Environment
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Start Backend Server
```bash
# With MOCK=1 enabled (default for Device A frontend integration):
python run.py
```
The server starts at `http://localhost:8000`.
* API Documentation (Swagger UI): `http://localhost:8000/docs`
* Health Check: `http://localhost:8000/health`

### 4. Running the Tests
```bash
pytest tests/ -v
```

---

## 📡 Backend Endpoints (Device 2 API Contract)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check & mode (`{"status": "ok", "mock_mode": true}`) |
| `POST` | `/analyze` | Multipart image upload. Returns complete **Passport JSON**. In `MOCK=1`, filename keyword triggers the corresponding fixture. |
| `GET` | `/passport/{id}` | Fetches stored Passport JSON by ID. |
| `GET` | `/p/{id}` | Clean, responsive, human-readable HTML web page (EN / HI toggle). |
| `GET` | `/passport/{id}/card.png?lang=en\|hi` | 1080x1350 PNG Share Card generated on demand. |
| `POST` | `/match_hash` | JSON `{ "phash": str }` for privacy-preserving, opt-in hash lookups. |
| `GET` | `/files/{filename}` | Serves static overlays, heatmaps, and aligned images. |

---

## 🧪 Device A Integration: Mock Mode Guide

When `MOCK=1` (enabled by default in Phase 1):
Upload any image via `POST /analyze` with the target keyword in the file name to immediately receive the corresponding fixture:
* Filename contains `original` &rarr; returns `shared/fixtures/original.json`
* Filename contains `modified` or `edited` &rarr; returns `shared/fixtures/modified.json`
* Filename contains `ai_confirmed` or `confirmed` &rarr; returns `shared/fixtures/ai_confirmed.json`
* Filename contains `likely_ai` &rarr; returns `shared/fixtures/likely_ai.json`
* Any other filename &rarr; returns `shared/fixtures/inconclusive.json`

---

## 🚀 Live Demo & Empirical Evaluation

### 1. Run Live End-to-End Demo
```bash
python demo.py
```
Demonstrates all 3 confirmation lanes, privacy lookups, share card generation, and web passports.

### 2. Run Empirical Evaluation Benchmark
```bash
python backend/scripts/evaluate.py
```
Measures true empirical pHash recall across variant types, false positive rate on unseen random images, and p50/p95 retrieval latencies. Verified results documented in [`docs/RESULTS.md`](docs/RESULTS.md).

---

## 🤖 Clients & Integrations

- **Telegram Verification Bot:** [`bot/`](bot/) - Lightweight, async bot supporting forwarded photos and share card generation. See [`bot/README.md`](bot/README.md).
- **Browser Extension (Manifest V3):** [`extension/`](extension/) - One-click right-click image verification on any webpage or WhatsApp Web. See [`extension/README.md`](extension/README.md).
- **iOS Shortcut:** [`docs/IOS_SHORTCUT.md`](docs/IOS_SHORTCUT.md) - Share sheet integration recipe for iPhone and iPad.
- **Production Deployment Guide:** [`docs/DEPLOY.md`](docs/DEPLOY.md) - Docker containerization and cloud instructions.

* **Ephemeral Processing:** Uploaded source images are deleted after processing; only derived heatmaps and metadata needed for the passport are cached temporarily (1-hour TTL).
* **Search Scope Transparency:** Searches match against the local curated index. External third-party lookups (Lens / TinEye) require explicit user consent (`consent_external=true`).
* **Zero Chat Auto-Scanning:** No automated scraping or tracking of private communications. Opt-in hash lookup (`POST /match_hash`) transmits perceptual hashes only.
