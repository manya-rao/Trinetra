# Trinetra Browser Extension (Manifest V3)

A Chrome / Edge / Brave extension that integrates provenance verification into everyday web browsing and WhatsApp Web.

## Features
- **Context Menu Inspection:** Right-click on any image on any website or chat and select **"Verify Image with Trinetra"**.
- **Three Eyes Verification:** Queries the backend `/analyze` pipeline and opens the verified Provenance Passport in a dedicated tab.
- **Popup Upload:** Directly drop or select an image file from the browser toolbar.

## Installation Instructions

1. Open Chrome/Edge and navigate to `chrome://extensions/` or `edge://extensions/`.
2. Enable **Developer mode** (toggle in upper right).
3. Click **Load unpacked**.
4. Select the `extension/` directory in this repository.
5. The Trinetra icon will appear in your extensions toolbar.
