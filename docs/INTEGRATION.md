# Trinetra Integration & Deployment Guide

**Team**: Kinetix  
**Project**: Trinetra — Digital Trust & Cybersecurity  
**Event**: Code for Innovex '26 (Theme: *Navyug - A New Era*)  
**Track**: Misinformation & Provenance

---

## 1. Quickstart (One-Command Run)

### Backend Service (FastAPI + ML Pipeline)
From the repository root:
```bash
# 1. Activate Python virtual environment
.\.venv\Scripts\activate   # Windows
# or: source .venv/bin/activate # Linux/macOS

# 2. Run backend via Uvicorn (default: port 8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Health probe*: `GET http://localhost:8000/health`  
Returns `{"status": "ok", "service": "trinetra-backend", "version": "0.1.0", "mock_mode": false, "ml_available": true, "c2pa_available": true}`.
*(Note: If port 8000 is occupied by another local host service, set `PORT=8001` and `BACKEND_PORT=8001`)*.

### Frontend Client (Vite 6 + React 19 + Tailwind v4 + Lenis)
From the repository root:
```bash
cd frontend
npm install
npm run dev
```
Local development server will run at `http://localhost:5173`.  
Vite dev server proxies all `/analyze`, `/passport`, `/p`, `/match_hash`, `/health`, and `/files` requests directly to `http://localhost:8000` (or `BACKEND_PORT`).

---

## 2. Environment Variables

| Variable | Scope | Default | Description |
| :--- | :--- | :--- | :--- |
| `BACKEND_PORT` | Backend / Vite Proxy | `8000` | Local port for FastAPI Uvicorn server |
| `VITE_API_URL` | Frontend build | `""` (proxied in dev) | Production backend origin URL (e.g., `https://api.trinetra.kinetix.internal`) |
| `CORS_ORIGINS` | Backend | `*` | Comma-delimited list of allowed CORS origins for production |
| `CLIP_OFFLINE` | Backend / ML | `1` | Forces OpenCLIP to use local cached weights, preventing runtime downloads |
| `TELEGRAM_BOT_TOKEN` | Distribution POC | `""` | Optional token for running the Telegram distribution proof-of-concept bot |

---

## 3. Resource Requirements & Memory Footprint

- **CPU Latency**: Mean inference latency is **114.2 ms** (P95: 130.0 ms) on standard CPU architecture (under the 3,000 ms real-time interactive budget).
- **RAM / VRAM**:
  - OpenCLIP ViT-B-32 (`laion2b_s34b_b79k`) weights: ~605 MB
  - Scikit-learn fusion calibrator + joblib artifacts: ~12 MB
  - Torch CPU runtime overhead: ~500 MB
  - Total operational working set: **~1.2 GB RAM** (no GPU required for CPU inference).
- **Disk Footprint**:
  - Pre-computed reference index (64 DEMO DATA images): ~35 MB
  - Model weights directory (`ml/models/`): ~620 MB

---

## 4. HTTPS Checklist for PWA Share Target

The Trinetra Progressive Web App includes a W3C Web Share Target API configuration in `frontend/public/manifest.json`:
```json
"share_target": {
  "action": "/#verify",
  "method": "POST",
  "enctype": "multipart/form-data",
  "params": {
    "files": [
      {
        "name": "image",
        "accept": ["image/*"]
      }
    ]
  }
}
```

### Production Deployment Requirements:
1. **Valid TLS/SSL (HTTPS)**: The Web Share Target API requires a secure context (`https://`). Service workers will not register over plain `http://` except on `localhost`.
2. **Service Worker Registration**: `frontend/public/sw.js` intercepts `fetch` events with method `POST` directed at `/#verify`, stores the incoming file in a temporary Cache API slot, and posts a message to client windows.
3. **MIME Types**: Ensure reverse proxy (e.g., Nginx, Caddy, Cloudflare) sends `application/manifest+json` for `manifest.json`.
4. **iOS Fallback**: iOS Safari does not support receiving files via Web Share Target. Trinetra gracefully falls back to direct photo upload or clipboard paste.

---

## 5. Hosting Recommendations

- **Backend**:
  - **Hugging Face Docker Space** or **AWS App Runner / Google Cloud Run**:
    - Container with Python 3.11+, PyTorch (CPU-only build), OpenCV headless, and Uvicorn.
    - Set memory limit to at least 2.0 GiB (nominal usage: ~1.2 GiB).
    - Expose port 8001 or 8080.
- **Frontend**:
  - **Vercel** / **Cloudflare Pages** / **Netlify**:
    - Run `npm run build` inside `frontend/`.
    - Deploy output directory `frontend/dist/`.
    - Configure rewrite rule: `/files/* -> <BACKEND_ORIGIN>/files/*` and `/analyze -> <BACKEND_ORIGIN>/analyze`.

---

## 6. Verification Status & Test Evidence

| System Layer | Status | Test / Proof Command | Notes |
| :--- | :---: | :--- | :--- |
| **Backend Unit & Integration** | **WORKS** | `pytest backend ml/tests` | All 52/52 tests pass |
| **Frontend Static & Type Check** | **WORKS** | `cd frontend && npx tsc --noEmit` | Clean type-checking, 0 errors |
| **Frontend Production Build** | **WORKS** | `cd frontend && npm run build` | Vite 6 builds clean `dist/` |
| **Frontend Responsive & Overflow** | **WORKS** | `scripts/verify_hero_layout.mjs`, `scripts/verify_phase3.mjs` | 0px overflow across 390, 768, 1280, 1920 |
| **E2E Demo Scenarios** | **WORKS** | `python scripts/run_phase6_scenarios.py` | Scenarios A, B, C1, C2, D verified on live server |
| **Native WhatsApp API Hook** | **UNTESTED** | Marked in UI as concept / manual forward | Trinetra does not spy on encrypted chats; users share suspicious images manually via system share or Web app |
| **External Live Search APIs** | **UNTESTED / INTENTIONAL** | Consent Modal | Google Lens & TinEye queries require explicit user consent and open in browser |
