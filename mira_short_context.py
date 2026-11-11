#!/usr/bin/env python3
"""Mira SHORT external-context research. NEVER a Walt trading signal or order."""
import argparse
import datetime as dt
import json
import math
import urllib.parse
import urllib.request

API = "https://data-api.binance.vision/api/v3/klines"
INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000, "4h": 14_400_000}

def fetch_bars(symbol="BTCUSDT", interval="15m", limit=800, now_ms=None):
    if symbol != "BTCUSDT" or interval not in INTERVAL_MS or not 200 <= limit <= 1000:
        raise ValueError("Unsupported market/interval/history")
    now_ms = now_ms or int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
    query = urllib.parse.urlencode({"symbol": symbol, "interval": interval, "limit": limit})
    req = urllib.request.Request(API + "?" + query, headers={"User-Agent": "MiraResearch/1.0"})
    with urllib.request.urlopen(req, timeout=12) as response:
        raw = json.load(response)
    if not isinstance(raw, list):
        raise ValueError("Invalid API response")
    step = INTERVAL_MS[interval]
    bars = []
    for item in raw:
        start, end = int(item[0]), int(item[6])
        if end >= now_ms:
            continue  # unfinished candle is never a signal
        o, h, l, c, v = map(float, (item[1], item[2], item[3], item[4], item[5]))
        if (start % step or end != start + step - 1 or
            not all(math.isfinite(x) for x in (o,h,l,c,v)) or
            l <= 0 or l > min(o,c) or h < max(o,c) or v < 0):
            raise ValueError("Invalid OHLCV candle")
        bars.append({"t":start,"open":o,"high":h,"low":l,"close":c,"volume":v})
    if len(bars) < 700 and interval == "15m":
        raise ValueError("Insufficient 7d 15m history")
    if len(bars) < 200:
        raise ValueError("Insufficient indicator history")
    if any(b["t"] - a["t"] != step for a,b in zip(bars,bars[1:])):
        raise ValueError("Missing or duplicate candles")
    if now_ms - (bars[-1]["t"] + step) > step * 2:
        raise ValueError("Stale candles")
    return bars

def ema(values, n):
    if len(values) < n: raise ValueError("Insufficient EMA data")
    result = sum(values[:n]) / n
    alpha = 2 / (n + 1)
    for v in values[n:]:
        result = alpha * v + (1-alpha) * result
    return result

def rsi(values, n=14):
    if len(values) < n+1: raise ValueError("Insufficient RSI data")
    changes = [values[i]-values[i-1] for i in range(1,len(values))]
    gain = sum(max(x,0) for x in changes[:n])/n
    loss = sum(max(-x,0) for x in changes[:n])/n
    for x in changes[n:]:
        gain = (gain*(n-1)+max(x,0))/n
        loss = (loss*(n-1)+max(-x,0))/n
    return 100 if loss == 0 and gain else 50 if loss == 0 else 100-100/(1+gain/loss)

def analyze(bars):
    if len(bars) < 673: raise ValueError("Need at least 673 closed 15m candles")
    closes = [b["close"] for b in bars]
    last = closes[-1]
    r24 = 100*(last/closes[-97]-1)
    r7 = 100*(last/closes[-673]-1)
    geometric_daily = (1+r7/100)**(1/7)-1
    e20, e50, e200 = (ema(closes,n) for n in (20,50,200))
    vol20 = sum(b["volume"] for b in bars[-21:-1])/20
    downtrend = last < e20 < e50 < e200
    # Context only: a rebound to EMA20 followed by a bearish close below prior low.
    rebound_seen = any(b["high"] >= e20 for b in bars[-8:-1])
    bearish_rejection = bars[-1]["close"] < bars[-2]["low"] and bars[-1]["close"] < bars[-1]["open"]
    volume_confirmed = vol20 > 0 and bars[-1]["volume"] > 1.2*vol20
    return {
        "r24_pct":round(r24,3), "r7_pct":round(r7,3),
        "r7_geometric_daily_pct":round(100*geometric_daily,4),
        "r24_vs_r7day_pass":r24/100 > geometric_daily,
        "r24_drop_pass":r24 <= -5,
        "ema20":round(e20,2),"ema50":round(e50,2),"ema200":round(e200,2),
        "rsi14":round(rsi(closes),2),
        "downtrend":downtrend, "recent_rebound_proxy":rebound_seen,
        "bearish_rejection_proxy":bearish_rejection,
        "volume_confirmation":volume_confirmed,
        "research_short_context":all((r24<=-5,r24/100>geometric_daily,downtrend,rebound_seen,bearish_rejection,volume_confirmed))
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--json",action="store_true")
    args=p.parse_args()
    result={"mode":"EXTERNAL_RESEARCH_ONLY","execution":"DISABLED",
            "source":"Binance BTCUSDT spot 15m closed candles",
            "walt_signal_verified":False,
            "trade_ready":False,
            "blockers":["Walt 24h/7d history not verified","Walt spread/depth not verified",
                        "USDT to USDC collateral not verified","Walt execution and stress-risk not verified"]}
    try:
        bars=fetch_bars()
        result.update({"candle_end_utc":dt.datetime.fromtimestamp((bars[-1]["t"]+900_000)/1000,dt.timezone.utc).isoformat(),
                       "analysis":analyze(bars)})
    except Exception as exc:
        result["error"]=str(exc)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if "analysis" in result else 2

if __name__=="__main__":
    raise SystemExit(main())
