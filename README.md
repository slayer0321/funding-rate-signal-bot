# Funding Rate Signal Bot 🤖

AI-powered funding rate monitor for Hyperliquid perpetuals.

## What it does

- 📊 Fetches real-time funding rates from Hyperliquid
- 🤖 Analyzes signals with Kimi AI (LLM)
- 🚨 Sends alerts to Discord when thresholds are exceeded
- 📝 Logs all signals to local JSON

## Architecture

```
Hyperliquid API → Python Bot → Kimi AI Analysis → Discord Webhook
                     ↓
                signals.json (local log)
```

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/slayer0321/funding-rate-signal-bot.git
   cd funding-rate-signal-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `KIMI_API_KEY` | Your Kimi API key |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for alerts |

## Tech Stack

- **Python 3.11+**
- **Hyperliquid API** — funding rate data
- **Kimi AI** — LLM analysis
- **Discord Webhooks** — notifications

## Author

Built by [Jonathan Behem](https://github.com/slayer0321) for Foresight Ventures application.
