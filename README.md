# Funding Rate Signal Bot 🤖

AI-powered funding rate monitor for Hyperliquid perpetuals.
**Works with ANY LLM provider** — Kimi, OpenAI, Anthropic, Groq, or bring your own.

## What it does

- 📊 Fetches real-time funding rates from Hyperliquid
- 🤖 Analyzes signals with your choice of AI (Kimi, OpenAI, Claude, Llama, etc.)
- 🚨 Sends alerts to Discord when thresholds are exceeded
- 📝 Logs all signals to local JSON
- ⏱️  **Auto-monitoring mode** — runs continuously, checking every N minutes
- 🎮 **Manual mode** — trigger checks on demand via command line

## Architecture

```
Hyperliquid API → Python Bot → Your Choice of LLM → Discord Webhook
                     ↓
                signals.json (local log)
```

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/slayer0321/funding-rate-signal-bot.git
cd funding-rate-signal-bot
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Minimum required in `.env`:**
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
LLM_PROVIDER=kimi              # or openai, anthropic, groq
LLM_API_KEY=your_api_key_here
```

### 3. Run

#### 🔄 Continuous Monitoring (default)
Checks funding rates every 5 minutes, alerts when threshold exceeded:
```bash
python bot.py
# or explicitly:
python bot.py --monitor
```

#### 🔍 Single Check
Run once, alert only if threshold exceeded:
```bash
python bot.py --check
```

#### 🎯 Check Specific Asset
```bash
python bot.py --check --asset SOL
```

#### 🚨 Force Alert
Ignore threshold, force an alert for an asset:
```bash
python bot.py --force --asset BTC
```

#### 📊 Send Summary
Get a snapshot of ALL funding rates (no AI analysis, just data):
```bash
python bot.py --summary
```

#### 🔧 Use Different LLM (one-time override)
```bash
python bot.py --check --provider openai
python bot.py --check --provider anthropic --asset ETH
```

## Supported LLM Providers

| Provider | Default Model | Needs API Key |
|----------|--------------|---------------|
| **Kimi** | `kimi-k2.6` | `LLM_API_KEY` |
| **OpenAI** | `gpt-4o-mini` | `LLM_API_KEY` |
| **Anthropic** | `claude-3-haiku` | `LLM_API_KEY` |
| **Groq** | `llama3-8b-8192` | `LLM_API_KEY` |

**Want to add another provider?** Just add a preset in `bot.py` — 10 lines of code.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_WEBHOOK_URL` | ✅ | — | Discord webhook for alerts |
| `LLM_PROVIDER` | ❌ | `kimi` | LLM provider to use |
| `LLM_API_KEY` | ✅ | — | API key for chosen provider |
| `LLM_MODEL` | ❌ | *(provider default)* | Override model |
| `LLM_API_URL` | ❌ | *(provider default)* | Override API endpoint |
| `THRESHOLD` | ❌ | `0.001` | Alert threshold (0.1%) |
| `ASSETS` | ❌ | `BTC,ETH,SOL,...` | Comma-separated list |
| `CHECK_INTERVAL` | ❌ | `300` | Seconds between checks |

## Example Discord Output

### Alert (threshold exceeded)
```
🟢 BTC Funding Rate Alert
Rate: 0.0013 (0.1300%)

AI Analysis:
Positive funding suggests long-heavy positioning. 
Potential short opportunity if price rejects resistance. 
Risk: Funding can flip quickly in volatile markets.
```

### Summary (manual request)
```
📊 Funding Rate Summary
🟢 BTC: 0.0012 (0.1200%) @ $67,420.50
🔴 ETH: -0.0008 (-0.0800%) @ $3,520.10
🟢 SOL: 0.0021 (0.2100%) @ $145.30
...
```

## Tech Stack

- **Python 3.11+**
- **Hyperliquid API** — funding rate data
- **Any LLM** — your choice of AI provider
- **Discord Webhooks** — notifications

## Project Structure

```
funding-rate-signal-bot/
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── .env.example        # Configuration template
├── .gitignore          # Secrets & data excluded
├── signals.json        # Local signal log (created on first run)
└── README.md           # This file
```

## Security

- ✅ `.env` is gitignored — secrets never committed
- ✅ `.env.example` provided as template
- ✅ No hardcoded credentials
- ✅ `signals.json` (personal data) is gitignored

## Author

Built by [Jonathan Behem](https://github.com/slayer0321)

- GitHub: https://github.com/slayer0321
- X/Twitter: @JoCryptoTech
- Location: Shenzhen, China (Remote)
