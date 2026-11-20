"""
Trinetra Telegram Verification Bot
Allows users to forward or send images to get an instant Provenance Passport.
Uses the Telegram Bot HTTP API via httpx (no external bot library dependency required).
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("trinetra-bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
POLL_TIMEOUT = int(os.getenv("POLL_TIMEOUT", "30"))

VERDICT_EMOJIS = {
    "original": "🟢 VERIFIED ORIGINAL",
    "modified": "🟡 MODIFIED / ALTERED",
    "out_of_context": "🟡 RECYCLED / OUT OF CONTEXT",
    "ai_confirmed": "🔴 AI-GENERATED (CONFIRMED)",
    "likely_ai": "🟠 LIKELY AI-GENERATED",
    "likely_real_looking": "🔵 NO AI SIGNS FOUND (NOT PROOF)",
    "inconclusive": "⚪ INCONCLUSIVE ANALYSIS"
}

async def send_message(client: httpx.AsyncClient, chat_id: int, text: str, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        await client.post(url, json=payload, timeout=15)
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")

async def send_photo(client: httpx.AsyncClient, chat_id: int, photo_url_or_bytes: str, caption: str = ""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": photo_url_or_bytes, "caption": caption, "parse_mode": "HTML"}
    try:
        await client.post(url, json=payload, timeout=25)
    except Exception as e:
        logger.error(f"Error sending photo to {chat_id}: {e}")

async def analyze_telegram_image(client: httpx.AsyncClient, file_url: str, caption: str = None) -> dict:
    """Download image from Telegram and submit to Trinetra /analyze endpoint."""
    img_resp = await client.get(file_url, timeout=30)
    if img_resp.status_code != 200:
        raise RuntimeError("Failed to download image from Telegram servers")

    files = {"image": ("telegram_upload.jpg", img_resp.content, "image/jpeg")}
    data = {
        "lang": "en",
        "consent_external": "true",
        "claim_text": caption or ""
    }
    
    resp = await client.post(f"{BACKEND_URL}/analyze", files=files, data=data, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Backend returned status {resp.status_code}: {resp.text}")
    return resp.json()

def format_passport_reply(passport: dict) -> str:
    verdict = passport.get("verdict", "inconclusive")
    verdict_label = VERDICT_EMOJIS.get(verdict, verdict.upper())
    pid = passport.get("id", "")
    eyes = passport.get("eyes", {})
    reasons = passport.get("reasons", [])
    web_url = f"{BACKEND_URL}/p/{pid}?lang=en"

    reasons_text = "\n".join([f"• {r.get('en', '')}" for r in reasons[:3]]) or "• No specific risk flags"

    msg = (
        f"<b>👁️ TRINETRA PROVENANCE PASSPORT</b>\n"
        f"<code>ID: {pid}</code>\n\n"
        f"<b>Verdict:</b> {verdict_label}\n"
        f"<b>Confidence:</b> {passport.get('confidence_band', 'n/a').upper()}\n\n"
        f"<b>The Three Eyes:</b>\n"
        f"  1️⃣ <b>Origin:</b> {eyes.get('origin', 'none').upper()}\n"
        f"  2️⃣ <b>Change:</b> {eyes.get('change', 'n/a').upper()}\n"
        f"  3️⃣ <b>Synthesis:</b> {eyes.get('synthesis', 'none').upper()}\n\n"
        f"<b>Verified Evidence:</b>\n{reasons_text}\n\n"
        f"🌐 <b>Interactive Web Passport:</b> <a href=\"{web_url}\">View Full Analysis</a>\n"
        f"<i>Scope: Matched against Trinetra Fact-Check Repository.</i>"
    )
    return msg

async def process_update(client: httpx.AsyncClient, update: dict):
    message = update.get("message")
    if not message:
        return
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    caption = message.get("caption", "")

    if text.startswith("/start") or text.startswith("/help"):
        welcome = (
            "<b>👋 Welcome to Trinetra Provenance Bot!</b>\n\n"
            "Forward or send any suspicious image to get an instant <b>Provenance Passport</b>:\n"
            "• <b>Eye 1 (Origin):</b> Has this image appeared in fact-check archives?\n"
            "• <b>Eye 2 (Change):</b> Has it been cropped, altered, or photoshopped?\n"
            "• <b>Eye 3 (Synthesis):</b> Is it AI-generated (C2PA or visual model signatures)?\n\n"
            "<i>Code for Innovex '26 • Team Kinetix • Theme: Navyug</i>"
        )
        await send_message(client, chat_id, welcome)
        return

    # Check for photo
    photos = message.get("photo")
    if photos:
        # Choose highest resolution photo
        highest_photo = photos[-1]
        file_id = highest_photo["file_id"]

        await send_message(client, chat_id, "⏳ <i>Analyzing image with Three Eyes pipeline...</i>")

        try:
            # 1. Get file path
            file_info_resp = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}")
            file_info = file_info_resp.json()
            if not file_info.get("ok"):
                await send_message(client, chat_id, "❌ Could not retrieve image from Telegram.")
                return

            file_path = file_info["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

            # 2. Analyze
            passport = await analyze_telegram_image(client, download_url, caption=caption)
            reply = format_passport_reply(passport)
            
            # 3. Send reply
            await send_message(client, chat_id, reply)

            # 4. Also send share card image
            card_url = f"{BACKEND_URL}/passport/{passport['id']}/card.png?lang=en"
            await send_photo(client, chat_id, card_url, caption="📸 <b>Trinetra Provenance Share Card</b>")

        except Exception as e:
            logger.error(f"Analysis error: {e}")
            await send_message(client, chat_id, f"⚠️ Analysis failed: {e}")

async def run_bot():
    if not BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured. Bot daemon will exit (configure env var to activate).")
        return

    logger.info("Starting Trinetra Telegram verification bot...")
    offset = 0
    async with httpx.AsyncClient() as client:
        while True:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout={POLL_TIMEOUT}"
                resp = await client.get(url, timeout=POLL_TIMEOUT + 5)
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        asyncio.create_task(process_update(client, update))
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_bot())
