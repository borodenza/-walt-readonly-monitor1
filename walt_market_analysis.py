#!/usr/bin/env python3
"""Mira Recovery only: read-only Bybit USDT linear futures research for Walt.

NEVER accesses a Walt wallet, API keys or order methods. Does not place trades.
Run: python3 walt_market_analysis.py --json
"""
import argparse
import datetime as dt
import json
import math
import sys
import urllib.parse
import urllib.request

# Public Binance futures candlesticks. Prices are research references, NOT Walt quotes.
BASE_URL = "https://api.bybit.com/v5/market/kline"
MIRA_ASSETS = tuple(asset + "USDT" for asset in
                    ("BTC", "ETH", "SOL", "DOGE", "LINK", "AVAX", "ADA", "XRP"))
ASSETS = MIRA_ASSETS
INTERVALS = {"15m": 900}
COUNT = 800
def fetch_candles(symbol, interval, now_ms=None, count=COUNT):
    """Bybit V5 public linear USDT perps: rows newest first, current bar excluded.

    If API or data quality fails, error out (no signal). Never fall back to spot.
    """
    if symbol not in MIRA_ASSETS or interval != "15m":
        raise ValueError("Unapproved linear futures symbol or timeframe")
    if not isinstance(count, int) or not (700 <= count <= 1000):
        raise ValueError("Futures scan requires enough closed history")
    url = BASE_URL + "?" + urllib.parse.urlencode({
        "category": "linear", "symbol": symbol,
        "interval": "15", "limit": count
    })
    request = urllib.request.Request(url, headers={"User-Agent": "WaltMiraResearch/2.1"})
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = json.load(response)
    if not isinstance(raw, dict) or raw.get("retCode") != 0:
        raise ValueError("Bybit V5 futures market API returned error")
    data = raw.get("result", {})
    if not isinstance(data, dict) or data.get("category") != "linear" or data.get("symbol") != symbol:
        raise ValueError("Bybit futures market mismatch")
    rows = data.get("list")
    if not isinstance(rows, list):
        raise ValueError("Malformed Bybit futures candles")
    now_ms = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000) if now_ms is None else now_ms
    period = 900_000
    candles = []
    for bar in rows:
        if not isinstance(bar, list) or len(bar) < 7:
            raise ValueError("Malformed futures candle")
        start = int(bar[0])
        end = start + period - 1
        if start % period:
            raise ValueError("Misaligned futures candle")
        if end >= now_ms:
            continue  # Last-traded-price field is not a finished candle
        o, h, l, c, v = map(float, (bar[1], bar[2], bar[3], bar[4], bar[5]))
        if not all(math.isfinite(x) for x in (o,h,l,c,v)):
            raise ValueError("Nonfinite futures candle")
        if l <= 0 or l > min(o,c) or h < max(o,c) or v < 0:
            raise ValueError("Malformed futures OHLCV")
        candles.append({"open_ms":start, "end_ms":end,
                        "open":o, "high":h, "low":l, "close":c, "volume":v})
    candles.sort(key=lambda b: b["open_ms"])
    if len(candles) < 700:
        raise ValueError("Insufficient closed futures candle history")
    if any(b["open_ms"]-a["open_ms"] != period for a,b in zip(candles,candles[1:])):
        raise ValueError("Missing or duplicate futures candles")
    if now_ms-(candles[-1]["end_ms"]+1) > period:
        raise ValueError("Stale futures candles")
    return candles


def ema(values, length):
    if len(values) < length:
        raise ValueError("Insufficient EMA history")
    result = [None] * (length - 1) + [sum(values[:length]) / length]
    a = 2 / (length + 1)
    for value in values[length:]:
        result.append(a * value + (1 - a) * result[-1])
    return result

def rsi(values, length=14):
    if len(values) < length + 1:
        raise ValueError("Insufficient RSI history")
    changes = [b - a for a, b in zip(values, values[1:])]
    gains = [max(d, 0.0) for d in changes]
    losses = [max(-d, 0.0) for d in changes]
    avg_gain = sum(gains[:length]) / length
    avg_loss = sum(losses[:length]) / length
    for gain, loss in zip(gains[length:], losses[length:]):
        avg_gain = (avg_gain * (length - 1) + gain) / length
        avg_loss = (avg_loss * (length - 1) + loss) / length
    if avg_loss == 0:
        return 100.0 if avg_gain else 50.0
    return 100 - 100 / (1 + avg_gain / avg_loss)

def scan():
    from mira import monitor_recovery
    now = dt.datetime.now(dt.timezone.utc)
    now_ms = int(now.timestamp() * 1000)
    out = {
        "mode": "READ_ONLY_RESEARCH", "execution": "DISABLED",
        "strategy": "MIRA_RECOVERY_ONLY",
        "source": "Bybit V5 linear futures public klines",
        "generated_utc": now.isoformat(),
        "mira": monitor_recovery(MIRA_ASSETS, fetch_candles, now_ms),
        "limits": {"MIRA": {"budget_usdt": 9, "risk_usdt": 0.18,
                            "daily_proposals": 3, "leverage": 1,
                            "max_open_positions": 1}},
        "wallet_trading_enabled": False,
        "walt_price_verified": False,
        "note": "Research on Binance futures, not validated Walt order prices. No orders."
    }
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args()
    result = scan()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["mira"]["ok"] else 2)
