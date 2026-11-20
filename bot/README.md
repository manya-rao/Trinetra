# Trinetra Telegram Verification Bot

This bot provides instant provenance checking directly inside Telegram for viral misinformation and forwarded images.

## Features
- **One-Tap Verification:** Forward any suspicious image or photo to the bot.
- **Three Eyes Breakdown:** Explains origin (Eye 1), modifications (Eye 2), and AI synthesis (Eye 3).
- **Share Card Delivery:** Sends back a 1080x1350 PNG Share Card ready to forward to groups.
- **Direct Web Link:** Link to `/p/{id}` for complete interactive inspection.

## Setup & Running

1. **Obtain Bot Token:**
   Create a new bot via [@BotFather](https://t.me/BotFather) and copy your bot token.

2. **Environment Variables:**
   ```bash
   export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
   export BACKEND_URL="http://127.0.0.1:8000"
   ```

3. **Run the Bot:**
   ```bash
   python bot/bot.py
   ```
