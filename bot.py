#!/usr/bin/env python3
"""
Funding Rate Signal Bot
Monitors Hyperliquid funding rates and sends AI-analyzed alerts to Discord.
Supports ANY LLM provider (Kimi, OpenAI, Anthropic, Groq, local, etc.)
"""

import os
import json
import time
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── Configuration ───────────────────────────────────────────────────────────

HYPERLIQUID_API = "https://api.hyperliquid.xyz/info"

# LLM Provider config — pick your provider via .env
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "kimi").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "kimi-k2.6")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.kimi.com/coding/v1/messages")

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

THRESHOLD = float(os.getenv("THRESHOLD", "0.001"))  # 0.1% default
ASSETS = os.getenv("ASSETS", "BTC,ETH,SOL,AVAX,ARB,OP,LINK,UNI").split(",")
SIGNALS_FILE = "signals.json"
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))  # 5 min default

# Provider presets — add yours here
PROVIDER_PRESETS = {
    "kimi": {
        "url": "https://api.kimi.com/coding/v1/messages",
        "model": "kimi-k2.6",
        "headers": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        "format_payload": lambda model, sys_msg, user_msg: {
            "model": model,
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg}
            ],
            "max_tokens": 200
        },
        "extract_response": lambda r: r.json()["content"][0]["text"]
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
        "headers": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        "format_payload": lambda model, sys_msg, user_msg: {
            "model": model,
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg}
            ],
            "max_tokens": 200
        },
        "extract_response": lambda r: r.json()["choices"][0]["message"]["content"]
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "model": "claude-3-haiku-20240307",
        "headers": lambda key: {"x-api-key": key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
        "format_payload": lambda model, sys_msg, user_msg: {
            "model": model,
            "max_tokens": 200,
            "system": sys_msg,
            "messages": [{"role": "user", "content": user_msg}]
        },
        "extract_response": lambda r: r.json()["content"][0]["text"]
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama3-8b-8192",
        "headers": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        "format_payload": lambda model, sys_msg, user_msg: {
            "model": model,
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg}
            ],
            "max_tokens": 200
        },
        "extract_response": lambda r: r.json()["choices"][0]["message"]["content"]
    }
}

# ─── Fetch Funding Rates ─────────────────────────────────────────────────────

def fetch_funding_rates():
    """Fetch current funding rates from Hyperliquid."""
    payload = {"type": "fundingRates"}
    try:
        r = requests.post(HYPERLIQUID_API, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        # Parse funding rates from response
        rates = {}
        for item in data:
            coin = item.get("coin", "")
            if coin in ASSETS:
                rates[coin] = float(item.get("fundingRate", 0))
        return rates
    except Exception as e:
        print(f"❌ Error fetching funding rates: {e}")
        return {}

def fetch_asset_prices():
    """Fetch current prices for context."""
    payload = {"type": "allMids"}
    try:
        r = requests.post(HYPERLIQUID_API, json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ Error fetching prices: {e}")
        return {}

# ─── AI Analysis ─────────────────────────────────────────────────────────────

def analyze_with_llm(asset, funding_rate, price=None):
    """Send funding rate data to configured LLM for analysis."""
    
    preset = PROVIDER_PRESETS.get(LLM_PROVIDER)
    if not preset:
        print(f"❌ Unknown provider: {LLM_PROVIDER}. Available: {', '.join(PROVIDER_PRESETS.keys())}")
        return "AI analysis unavailable — unknown provider."
    
    price_str = f" | Price: ${price:.2f}" if price else ""
    
    prompt = f"""Analyze this funding rate signal for {asset}:

Current Funding Rate: {funding_rate:.6f} ({funding_rate*100:.4f}%){price_str}

Provide a brief trading insight (2-3 sentences):
1. What does this funding rate suggest about market sentiment?
2. Is this a potential long or short opportunity?
3. Any risk warning?

Keep it concise and actionable."""

    sys_msg = "You are a crypto trading analyst specializing in funding rate strategies."
    
    headers = preset["headers"](LLM_API_KEY)
    payload = preset["format_payload"](LLM_MODEL, sys_msg, prompt)
    
    try:
        r = requests.post(
            LLM_API_URL or preset["url"],
            headers=headers,
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        return preset["extract_response"](r)
    except Exception as e:
        print(f"❌ LLM API error ({LLM_PROVIDER}): {e}")
        return "AI analysis unavailable."

# ─── Discord Notification ────────────────────────────────────────────────────

def send_discord_alert(asset, funding_rate, analysis, direction, price=None):
    """Send alert to Discord webhook."""
    emoji = "🟢" if direction == "positive" else "🔴"
    color = 0x00ff00 if direction == "positive" else 0xff0000
    
    price_str = f" | Price: `${price:.2f}`" if price else ""
    
    payload = {
        "username": "Funding Rate Bot",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/6134/6134346.png",
        "embeds": [{
            "title": f"{emoji} {asset} Funding Rate Alert",
            "description": (
                f"**Rate:** `{funding_rate:.6f}` ({funding_rate*100:.4f}%){price_str}\n\n"
                f"**AI Analysis:**\n{analysis}"
            ),
            "color": color,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "footer": {"text": f"Hyperliquid • {LLM_PROVIDER.upper()} AI Analysis"}
        }]
    }
    
    try:
        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Discord alert sent for {asset}")
        return True
    except Exception as e:
        print(f"❌ Discord error: {e}")
        return False

def send_discord_summary(rates, prices=None):
    """Send a summary of all funding rates to Discord."""
    lines = []
    for asset in ASSETS:
        if asset in rates:
            rate = rates[asset]
            emoji = "🟢" if rate > 0 else "🔴"
            price_str = f" @ ${prices.get(asset, 0):.2f}" if prices and asset in prices else ""
            lines.append(f"{emoji} **{asset}**: `{rate:.6f}` ({rate*100:.4f}%){price_str}")
    
    if not lines:
        lines.append("No funding rate data available.")
    
    payload = {
        "username": "Funding Rate Bot",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/6134/6134346.png",
        "embeds": [{
            "title": "📊 Funding Rate Summary",
            "description": "\n".join(lines),
            "color": 0x3498db,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "footer": {"text": "Hyperliquid • All Assets"}
        }]
    }
    
    try:
        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        r.raise_for_status()
        print("✅ Summary sent to Discord")
        return True
    except Exception as e:
        print(f"❌ Discord error: {e}")
        return False

# ─── Signal Logging ──────────────────────────────────────────────────────────

def log_signal(asset, funding_rate, analysis, alerted, price=None):
    """Save signal to local JSON log."""
    signal = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "asset": asset,
        "funding_rate": funding_rate,
        "price": price,
        "analysis": analysis,
        "alert_sent": alerted,
        "llm_provider": LLM_PROVIDER
    }
    
    signals = []
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE, "r") as f:
            signals = json.load(f)
    
    signals.append(signal)
    
    with open(SIGNALS_FILE, "w") as f:
        json.dump(signals, f, indent=2)

# ─── Core Logic ──────────────────────────────────────────────────────────────

def check_and_alert(asset=None, force=False):
    """Check funding rates and send alerts for threshold breaches."""
    print(f"\n🔍 Checking funding rates... ({datetime.utcnow().isoformat()}Z)")
    
    rates = fetch_funding_rates()
    prices = fetch_asset_prices()
    
    if not rates:
        print("❌ No funding rate data received")
        return
    
    assets_to_check = [asset] if asset else ASSETS
    
    for a in assets_to_check:
        if a not in rates:
            continue
            
        rate = rates[a]
        price = prices.get(a) if prices else None
        
        print(f"📈 {a}: {rate:.6f} ({rate*100:.4f}%)")
        
        if force or abs(rate) > THRESHOLD:
            if force:
                print(f"🚨 Manual check triggered for {a}")
            else:
                print(f"⚠️  Threshold exceeded! Analyzing with {LLM_PROVIDER}...")
            
            analysis = analyze_with_llm(a, rate, price)
            direction = "positive" if rate > 0 else "negative"
            alerted = send_discord_alert(a, rate, analysis, direction, price)
            log_signal(a, rate, analysis, alerted, price)
            print(f"📝 Analysis: {analysis[:100]}...")
        else:
            print(f"✅ Within threshold, no alert.")
    
    print("-" * 50)

def run_monitoring_loop():
    """Run continuous monitoring loop."""
    print(f"🚀 Funding Rate Signal Bot starting...")
    print(f"📊 Monitoring: {', '.join(ASSETS)}")
    print(f"🎯 Threshold: ±{THRESHOLD*100:.2f}%")
    print(f"🤖 LLM Provider: {LLM_PROVIDER}")
    print(f"⏱️  Check interval: {CHECK_INTERVAL}s ({CHECK_INTERVAL//60}min)")
    print("-" * 50)
    
    while True:
        try:
            check_and_alert()
            print(f"😴 Sleeping {CHECK_INTERVAL}s...\n")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user.")
            break
        except Exception as e:
            print(f"❌ Error in monitoring loop: {e}")
            time.sleep(60)  # Wait 1 min on error

def send_manual_summary():
    """Send a manual summary of all funding rates."""
    print("📊 Fetching funding rate summary...")
    rates = fetch_funding_rates()
    prices = fetch_asset_prices()
    
    if rates:
        send_discord_summary(rates, prices)
    else:
        print("❌ No data available")

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Funding Rate Signal Bot — AI-powered Hyperliquid monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bot.py --monitor              # Start continuous monitoring (default)
  python bot.py --check                # Single check, alert if threshold exceeded
  python bot.py --check --asset SOL    # Check specific asset only
  python bot.py --force --asset BTC    # Force alert for BTC regardless of threshold
  python bot.py --summary              # Send summary of all rates to Discord
  python bot.py --check --force        # Force alert for all assets
        """
    )
    
    parser.add_argument("--monitor", action="store_true", help="Run continuous monitoring loop")
    parser.add_argument("--check", action="store_true", help="Single check run")
    parser.add_argument("--summary", action="store_true", help="Send funding rate summary to Discord")
    parser.add_argument("--asset", type=str, help="Specific asset to check (e.g., BTC, ETH, SOL)")
    parser.add_argument("--force", action="store_true", help="Force alert regardless of threshold")
    parser.add_argument("--provider", type=str, help="Override LLM provider (kimi, openai, anthropic, groq)")
    
    args = parser.parse_args()
    
    # Override provider if specified
    global LLM_PROVIDER, LLM_API_URL, LLM_MODEL
    if args.provider:
        LLM_PROVIDER = args.provider.lower()
        preset = PROVIDER_PRESETS.get(LLM_PROVIDER)
        if preset:
            LLM_API_URL = preset["url"]
            LLM_MODEL = preset["model"]
            print(f"🔧 Using provider: {LLM_PROVIDER}")
    
    # Validate config
    if not DISCORD_WEBHOOK:
        print("❌ DISCORD_WEBHOOK_URL not set in .env")
        return
    if not LLM_API_KEY:
        print(f"❌ LLM_API_KEY not set in .env")
        return
    
    # Route to appropriate mode
    if args.summary:
        send_manual_summary()
    elif args.check or args.force:
        check_and_alert(asset=args.asset, force=args.force)
    else:
        # Default: monitoring loop
        run_monitoring_loop()

if __name__ == "__main__":
    main()
