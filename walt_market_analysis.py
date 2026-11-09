#!/usr/bin/env python3
"""Mira Recovery only: read-only Hyperliquid perpetual futures research for Walt.

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
BASE_URL = "https://api.hyperliquid.xyz/info"
MIRA_ASSETS = tuple(asset + "USDT" for asset in
                    ("BTC", "ETH", "SOL", "DOGE", "LINK", "AVAX", "ADA", "XRP"))
ASSETS = MIRA_ASSETS
INTERVALS = {"15m": 900}
COUNT = 800
ddef fetch_candles(symbol, interval, now_ms=None, count=COUNT):
    """Hyperliquid public perp candles; fail closed on missing/stale data."""
    if symbol not in MIRA_ASSETS or interval != "15m":
        raise ValueError("Unapproved perpetual symbol or timeframe")
    if not isinstance(count, int) or not (700 <= count <= 1000):
        raise ValueError("Insufficient requested history")
    now_ms = int(dt.datetime.now(dt.timezone.utc).timestamp()*1000) if now_ms is None else now_ms
    period = 900_000
    asset = symbol[:-4]  # approved symbols all have USDT suffix
    payload = json.dumps({"type":"candleSnapshot","req":{
        "coin":asset, "interval":"15m",
        "startTime":now_ms-(count+10)*period,
        "endTime":now_ms
    }}).encode("utf-8")
    req = urllib.request.Request(BASE_URL, data=payload,
          headers={"Content-Type":"application/json","User-Agent":"WaltMiraReadOnly/3.0"},
          method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw=json.load(resp)
    if not isinstance(raw,list):
        raise ValueError("Invalid Hyperliquid perpetual candles response")
    candles=[]
    for bar in raw:
        if not isinstance(bar,dict) or bar.get("s")!=asset or bar.get("i")!="15m":
            raise ValueError("Unexpected Hyperliquid market or interval")
        start,end=int(bar["t"]),int(bar["T"])
        if start % period or end!=start+period-1:
            raise ValueError("Misaligned perpetual candle")
        if end >= now_ms:
            continue
        o,h,l,c,v = map(float,(bar["o"],bar["h"],bar["l"],bar["c"],bar["v"]))
        if not all(math.isfinite(x) for x in (o,h,l,c,v)):
            raise ValueError("Nonfinite perpetual OHLCV")
        if l<=0 or l>min(o,c) or h<max(o,c) or v<0:
            raise ValueError("Invalid perpetual OHLCV")
        candles.append({"open_ms":start,"end_ms":end,"open":o,
                        "high":h,"low":l,"close":c,"volume":v})
    candles.sort(key=lambda b:b["open_ms"])
    if len(candles)<700:
        raise ValueError("Insufficient closed perpetual history")
    if any(b["open_ms"]-a["open_ms"]!=period for a,b in zip(candles,candles[1:])):
        raise ValueError("Missing/duplicate perpetual candles")
    if now_ms-(candles[-1]["end_ms"]+1)>period:
        raise ValueError("Stale perpetual candles")
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
        "source": "Hyperliquid public perpetual candleSnapshot",
        "generated_utc": now.isoformat(),
        "mira": monitor_recovery(MIRA_ASSETS, fetch_candles, now_ms),
        "limits": {"MIRA": {"budget_usdt": 9, "risk_usdt": 0.18,
                            "daily_proposals": 3, "leverage": 1,
                            "max_open_positions": 1}},
        "wallet_trading_enabled": False,
        "walt_price_verified": False,
        "note": "Research on Hyperliquid perpetuals, not validated Walt order prices. No orders."
    }
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args()
    result = scan()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["mira"]["ok"] else 2)
