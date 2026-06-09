#!/usr/bin/env python3
"""
Funding Rate Signal Bot
Monitors Hyperliquid funding rates and sends AI-analyzed alerts to Discord.
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── Configuration ───────────────────────────────────────────────────────────

HYPERLIQUID_API = "https://api.hyperliquid.xyz/info"
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_API_URL = "https://api.kimi.com/coding/v1/messages"
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

THRESHOLD = 0.001  # 0.1% — alert if |funding rate| > threshold
ASSETS = ["BTC", "ETH", "SOL", "AVAX", "ARB", "OP", "LINK", "UNI"]
SIGNALS_FILE = "signals.json"

# ─── Fetch Funding Rates ─────────────────────────────────────────────────────

def fetch_funding_rates():
    """Fetch current funding rates from Hyperliquid."""
    payload = {"type": "allMids"}
    try:
        r = requests.post(HYPERLIQUID_API, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        # Extract funding rates (simplified — actual Hyperliquid funding endpoint)
        return data
    except Exception as e:
        print(f"❌ Error fetching funding rates: {e}")
        return None

def fetch_meta():
    """Fetch asset metadata from Hyperliquid."""
    payload = {"type": "meta"}
    try:
        r = requests.post(HYPERLIQUID_API, json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ Error fetching meta: {e}")
        return None

# ─── AI Analysis via Kimi ────────────────────────────────────────────────────

def analyze_with_kimi(asset, funding_rate, context):
    """Send funding rate data to Kimi for AI analysis."""
    prompt = f"""Analyze this funding rate signal for {asset}:

Current Funding Rate: {funding_rate:.4f}%
Context: {context}

Provide a brief trading insight (2-3 sentences):
1. What does this funding rate suggest about market sentiment?
2. Is this a potential long or short opportunity?
3. Any risk warning?

Keep it concise and actionable."""

    headers = {
        "Authorization": f"Bearer {KIMI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "kimi-k2.6",
        "messages": [
            {"role": "system", "content": "You are a crypto trading analyst specializing in funding rate strategies."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200
    }

    try:
        r = requests.post(KIMI_API_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        response = r.json()
        return response["content"][0]["text"]
    except Exception as e:
        print(f"❌ Kimi API error: {e}")
        return "AI analysis unavailable."

# ─── Discord Notification ────────────────────────────────────────────────────

def send_discord_alert(asset, funding_rate, analysis, direction):
    """Send alert to Discord webhook."""
    emoji = "🟢" if direction == "positive" else "🔴"
    color = 0x00ff00 if direction == "positive" else 0xff0000

    payload = {
        "username": "Funding Rate Bot",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/6134/6134346.png",
        "embeds": [{
            "title": f"{emoji} {asset} Funding Rate Alert",
            "description": f"**Rate:** `{funding_rate:.4f}%`\n\n**AI Analysis:**\n{analysis}",
            "color": color,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "footer": {"text": "Hyperliquid • Kimi AI Analysis"}
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

# ─── Signal Logging ──────────────────────────────────────────────────────────

def log_signal(asset, funding_rate, analysis, alerted):
    """Save signal to local JSON log."""
    signal = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "asset": asset,
        "funding_rate": funding_rate,
        "analysis": analysis,
        "alert_sent": alerted
    }

    signals = []
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE, "r") as f:
            signals = json.load(f)

    signals.append(signal)

    with open(SIGNALS_FILE, "w") as f:
        json.dump(signals, f, indent=2)

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("🚀 Funding Rate Signal Bot starting...")
    print(f"📊 Monitoring: {', '.join(ASSETS)}")
    print(f"🎯 Threshold: ±{THRESHOLD*100:.2f}%")
    print("-" * 50)

    # Note: This is a simplified version. Full implementation would use
    # Hyperliquid's funding rate endpoint and proper error handling.

    # Example signal (for demo purposes)
    demo_signals = [
        {"asset": "SOL", "rate": -0.0023, "context": "High negative funding — potential short squeeze"},
        {"asset": "BTC", "rate": 0.0013, "context": "Moderate positive funding — neutral sentiment"},
    ]

    for signal in demo_signals:
        asset = signal["asset"]
        rate = signal["rate"]
        context = signal["context"]

        print(f"\n📈 {asset}: {rate:.4f}%")

        if abs(rate) > THRESHOLD:
            print(f"⚠️  Threshold exceeded! Analyzing with Kimi...")
            analysis = analyze_with_kimi(asset, rate, context)
            direction = "positive" if rate > 0 else "negative"
            alerted = send_discord_alert(asset, rate, analysis, direction)
            log_signal(asset, rate, analysis, alerted)
            print(f"📝 Analysis: {analysis[:100]}...")
        else:
            print(f"✅ Within threshold, no alert.")

    print("\n✅ Bot run complete.")

if __name__ == "__main__":
    main()
