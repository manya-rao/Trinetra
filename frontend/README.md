# Trinetra React PWA Frontend

**Team**: Kinetix | **Project**: Trinetra (Digital Trust & Provenance)
**Event**: Code for Innovex '26 | **Theme**: "Navyug - A New Era"
**Device**: Device A

---

## 1. Overview
The `frontend/` subsystem is a mobile-first, high-performance Progressive Web Application (PWA) built with **React 19**, **Vite**, and **Tailwind CSS**.
It delivers the **Provenance Passport** across the Three Eyes:
- **Eye 1: Origin** (Archive source, date, claim, fact-check report)
- **Eye 2: Change** (Interactive pixel before/after comparison slider + edit heatmap overlay)
- **Eye 3: Synthesis** (Multimodal forensic signals + suspicious region artifact map)

---

## 2. PWA Features & Mobile Considerations
- **Web App Manifest (`/manifest.json`)**: Configured with `standalone` display, dark theme `#0c1017`, and standard PWA icons (192px and 512px).
- **Web Share Target API**: Allows users to share an image directly into Trinetra from WhatsApp, Telegram, or any camera roll app (`POST /share-target` intercepted by Service Worker `/sw.js`).
- **iOS & Desktop Fallbacks**:
  - iOS WebKit does not currently support the Web Share Target specification; on iOS, users utilize the file picker, camera roll trigger, or drag-and-drop.
  - Native clipboard paste (`Ctrl+V`) is supported globally across the interface.
- **HTTPS & Tunnels**: Mobile browsers mandate HTTPS for Service Worker registration and Web Share Target. For testing on physical phones during local development, use an HTTPS tunnel (e.g., Cloudflare Tunnel, ngrok, or Tailscale Funnel).

---

## 3. UI/UX & Confirmation Ladder Architecture
1. **Never Colour Alone**: Every status and verdict badge combines an accessible Lucide icon, semantic text headline, and color-coded border:
   - `original`: Green + Shield Check
   - `modified`: Amber + Scissors
   - `out_of_context`: Amber + Clock Rewind
   - `ai_confirmed`: Red + CPU Alert (**The ONLY place the word "confirmed" appears**)
   - `likely_ai`: Orange + Sparkles
   - `likely_real_looking`: Teal + Camera ("No AI signs found, not proof")
   - `inconclusive`: Grey-Blue + Help Circle
2. **Zero Percentages**: No raw probability percentage is ever displayed to the user.
3. **Dual Language (EN / HI)**: One-tap toggle between English and Hindi, rendered with bundled `Noto Sans Devanagari` and system font fallbacks. *(Note: Hindi strings need native-speaker review).*
4. **Client Privacy Guarantee**: Uploaded image buffers are held in ephemeral memory object URLs (`URL.createObjectURL`) and explicitly revoked upon completion or reset (`URL.revokeObjectURL`). No images are persisted to `localStorage` or `IndexedDB`.
5. **Wider Web Search**: Google Lens and TinEye search buttons are gated behind an explicit third-party consent modal.

---

## 4. How to Run

### Development Mode
```powershell
cd frontend
npm install
npm run dev
```
Available at `http://localhost:3000`.

### Production Build & Preview
```powershell
npm run build
npm run preview
```

### Mock Mode vs. Real API Integration
- The API client defaults to Mock Mode (`USE_MOCK = true`) using the 7 contract-compliant JSON fixtures in `frontend/src/mocks/`.
- During evaluation or judging, use the fixture dropdown in the header to preview any verdict instantly.
- To connect to Device B's FastAPI backend:
  Set environment variable `VITE_API_URL=http://localhost:8000` or append `?mock=0` to the URL.
