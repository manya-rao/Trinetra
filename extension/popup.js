// Trinetra Popup UI Handler

const fileInput = document.getElementById("fileUpload");
const analyzeBtn = document.getElementById("analyzeBtn");
const resultArea = document.getElementById("resultArea");
const BACKEND_URL = "http://127.0.0.1:8000";

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    analyzeBtn.style.display = "block";
  }
});

analyzeBtn.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  resultArea.innerHTML = "<span style='color: #38bdf8;'>⏳ Analyzing image with Three Eyes...</span>";

  try {
    const formData = new FormData();
    formData.append("image", file);
    formData.append("lang", "en");
    formData.append("consent_external", "true");

    const resp = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      body: formData
    });

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const passport = await resp.json();

    resultArea.innerHTML = `
      <div style="padding: 8px; background: #1e293b; border-radius: 6px; margin-top: 8px;">
        <strong>Verdict:</strong> ${passport.verdict.toUpperCase()}<br/>
        <strong>Confidence:</strong> ${passport.confidence_band.toUpperCase()}<br/>
        <a href="${BACKEND_URL}/p/${passport.id}?lang=en" target="_blank" style="color: #38bdf8; text-decoration: underline; display: inline-block; margin-top: 6px;">View Full Passport &rarr;</a>
      </div>
    `;
  } catch (err) {
    resultArea.innerHTML = `<span style="color: #ef4444;">Error: ${err.message}</span>`;
  }
});
