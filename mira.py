"""Replay today's closed bars so retries cannot reset the daily proposal budget."""
from walt_market_analysis import ema, rsi

PERIOD = 900_000
DAY = 96 * PERIOD


def candidate(symbol, bars, i):
    bar = bars[i]
    price = bar["close"]
    day_change = price / bars[i - 96]["close"] - 1
    week_change = price / bars[i - 672]["close"] - 1
    if day_change > -0.05 or week_change <= day_change:
        return None
    window = bars[i - 64:i + 1]
    closes = [b["close"] for b in window]
    prev = bars[i - 1]
    prior_volume = sum(b["volume"] for b in window[-21:-1]) / 20
    current_rsi = rsi(closes)
    if not (price > ema(closes, 20)[-1] and current_rsi > rsi(closes[:-1])
            and price > prev["high"] and bar["low"] > prev["low"]
            and prior_volume > 0 and bar["volume"] > prior_volume):
        return None
    closed = bar["end_ms"] + 1
    return {"id": f"{symbol}-{closed}", "symbol": symbol, "closed_ms": closed,
            "expires_ms": closed + PERIOD, "futures_close": price, "rsi": current_rsi,
            "change24_pct": 100 * day_change, "change7d_pct": 100 * week_change}


def daily_queue(events):
    selected = []
    seen = set()
    for event in sorted(events, key=lambda e: (e["closed_ms"], e["symbol"])):
        if event["symbol"] not in seen:
            selected.append(event)
            seen.add(event["symbol"])
        if len(selected) == 3:
            break
    return selected


def monitor_recovery(symbols, fetch, now_ms):
    result = {"ok": False, "symbols": list(symbols), "source": "Binance USDⓈ-M Futures · 15m",
              "proposals": [], "observations": {}, "errors": {}}
    events = []
    latest = now_ms // PERIOD * PERIOD
    midnight = now_ms // DAY * DAY
    for symbol in symbols:
        try:
            bars = fetch(symbol, "15m", now_ms, count=800)
            if bars[-1]["end_ms"] + 1 != latest or bars[672]["end_ms"] + 1 > midnight:
                raise ValueError("Incomplete daily replay")
            for i in range(672, len(bars)):
                if bars[i]["end_ms"] + 1 >= midnight:
                    event = candidate(symbol, bars, i)
                    if event:
                        events.append(event)
            result["observations"][symbol] = {
                "change24_pct": 100 * (bars[-1]["close"] / bars[-97]["close"] - 1),
                "futures_close": bars[-1]["close"]}
        except Exception as exc:
            result["errors"][symbol] = str(exc)
    if not result["errors"]:
        result.update(ok=True, proposals=daily_queue(events))
    return result
