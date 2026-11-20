// Trinetra Manifest V3 Background Service Worker

const DEFAULT_BACKEND = "http://127.0.0.1:8000";

// Register right-click context menu on images
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "trinetra-verify-image",
    title: "👁️ Verify Image with Trinetra",
    contexts: ["image"]
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "trinetra-verify-image" && info.srcUrl) {
    const imageUrl = info.srcUrl;
    try {
      // 1. Fetch image bytes from page
      const resp = await fetch(imageUrl);
      const blob = await resp.blob();

      // 2. Upload to Trinetra /analyze
      const formData = new FormData();
      formData.append("image", blob, "web_inspect.jpg");
      formData.append("lang", "en");
      formData.append("consent_external", "true");

      const backendResp = await fetch(`${DEFAULT_BACKEND}/analyze`, {
        method: "POST",
        body: formData
      });

      if (!backendResp.ok) {
        throw new Error(`Server returned ${backendResp.status}`);
      }

      const passport = await backendResp.json();

      // 3. Open verified web passport in a new tab
      const passportUrl = `${DEFAULT_BACKEND}/p/${passport.id}?lang=en`;
      chrome.tabs.create({ url: passportUrl });

    } catch (err) {
      console.error("Trinetra verification failed:", err);
      // Fallback: open Trinetra web app with image URL param
      chrome.tabs.create({ url: `${DEFAULT_BACKEND}/health` });
    }
  }
});
