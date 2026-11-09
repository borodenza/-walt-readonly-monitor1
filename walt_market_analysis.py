#!/usr/bin/env python3
"""Read-only BTC/ETH intraday signal scanner using public Binance spot OHLCV.

Never connects to trading/order APIs. Output is research, NOT an executable order.
Run: python3 walt_market_analysis.py --json
"""

import argparse
import datetime as dt
import json
import math
import sys
import urllib.parse
import urllib.request

BASE_URL = "https://data-api.binance.vision/api/v3/klines"
ASSETS = ("BTCUSDT", "ETHUSDT")
INTERVALS = {"5m": 300, "15m": 900, "1h": 3600}
COUNT = 250


def fetch_candles(symbol, interval, now_ms=None):
    if symbol not in ASSETS or interval not in INTERVALS:
        raise ValueError("Unapproved symbol or interval")
    url = BASE_URL + "?" + urllib.parse.urlencode({
        "symbol": symbol, "interval": interval, "limit": COUNT
    })
    req = urllib.request.Request(url, headers={"User-Agent": "WaltResearchReadOnly/1.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        raw = json.load(response)
    if not isinstance(raw, list):
        raise ValueError("Invalid API response")
    now_ms = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000) if now_ms is None else now_ms
    candles = []
    for bar in raw:
        if not isinstance(bar, list) or len(bar) < 7:
            raise ValueError("Invalid candle shape")
        start, end = int(bar[0]), int(bar[6])
        if end >= now_ms:  # Discard current, incomplete candle.
            continue
        open_, high, low, close, volume = map(float, (bar[1], bar[2], bar[3], bar[4], bar[5]))
        if not all(math.isfinite(x) for x in (open_, high, low, close, volume)):
            raise ValueError("Nonfinite OHLCV")
        if low <= 0 or low > min(open_, close) or high < max(open_, close) or volume < 0:
            raise ValueError("Invalid OHLCV values")
        candles.append({"open_ms": start, "end_ms": end, "open": open_,
                        "high": high, "low": low, "close": close, "volume": volume})
    if len(candles) < 100:
        raise ValueError("Insufficient closed candle history")
    period = INTERVALS[interval] * 1000
    if any(b["open_ms"] - a["open_ms"] != period for a, b in zip(candles, candles[1:])):
        raise ValueError("Missing or duplicate candles")
    # A signal based on stale data is prohibited; tolerance is one entire interval.
    if now_ms - (candles[-1]["end_ms"] + 1) > period:
        raise ValueError("Stale candles")
    return candles


def ema(values, length):
    if len(values) < length:
        raise ValueError("Insufficient EMA history")
    output = [None] * (length - 1) + [sum(values[:length]) / length]
    alpha = 2 / (length + 1)
    for value in values[length:]:
        output.append(alpha * value + (1 - alpha) * output[-1])
    return output


def rsi(values, length=14):
    if len(values) < length + 1:
        raise ValueError("Insufficient RSI history")
    changes = [b - a for a, b in zip(values, values[1:])]
    gains = [max(v, 0.0) for v in changes]
    losses = [max(-v, 0.0) for v in changes]
    avg_gain = sum(gains[:length]) / length
    avg_loss = sum(losses[:length]) / length
    for g, l in zip(gains[length:], losses[length:]):
        avg_gain = (avg_gain * (length - 1) + g) / length
        avg_loss = (avg_loss * (length - 1) + l) / length
    if avg_loss == 0:
        return 100.0 if avg_gain else 50.0
    return 100 - 100 / (1 + avg_gain / avg_loss)


def atr(bars, length=14):
    ranges = [max(b["high"] - b["low"], abs(b["high"] - a["close"]),
                  abs(b["low"] - a["close"])) for a, b in zip(bars, bars[1:])]
    value = sum(ranges[:length]) / length
    for tr in ranges[length:]:
        value = (value * (length - 1) + tr) / length
    return value


def calculate(bars):
    close = [b["close"] for b in bars]
    vol = [b["volume"] for b in bars]
    return {
        "close": close[-1], "ema20": ema(close, 20)[-1],
        "ema50": ema(close, 50)[-1], "rsi14": rsi(close),
        "atr14": atr(bars), "volume_last": vol[-1],
        "volume_mean_prev20": sum(vol[-21:-1]) / 20,
        "support_prev20": min(b["low"] for b in bars[-21:-1]),
        "resistance_prev20": max(b["high"] for b in bars[-21:-1]),
        "last_closed_utc": dt.datetime.fromtimestamp(
            (bars[-1]["end_ms"] + 1) / 1000, dt.timezone.utc).isoformat(),
    }


def evaluate_a(data, bars):
    hourly, mid, fast = data["1h"], data["15m"], data["5m"]
    direction = ("LONG" if hourly["ema20"] > hourly["ema50"] and hourly["close"] > hourly["ema50"]
                 else "SHORT" if hourly["ema20"] < hourly["ema50"] and hourly["close"] < hourly["ema50"]
                 else None)
    if not direction:
        return "Нет согласованного часового тренда"
    past = bars["15m"][-7:-1]
    touched = any(abs(b["low" if direction == "LONG" else "high"] - mid["ema20"]) <= mid["atr14"] * .5
                  for b in past)
    candle = bars["15m"][-1]
    resumed = candle["close"] > candle["open"] and candle["close"] > bars["15m"][-2]["high"] if direction == "LONG" else candle["close"] < candle["open"] and candle["close"] < bars["15m"][-2]["low"]
    if not touched or not resumed:
        return "Не подтверждён откат к EMA20 и возобновление тренда на закрытой 15m свече"
    if direction == "LONG" and not (50 <= mid["rsi14"] <= 70):
        return "RSI15m не соответствует фильтру Long"
    if direction == "SHORT" and not (30 <= mid["rsi14"] <= 50):
        return "RSI15m не соответствует фильтру Short"
    if not (fast["volume_last"] > fast["volume_mean_prev20"]):
        return "Нет подтверждения объёмом на 5m"
    return f"Условный технический кандидат {direction}; без расчёта исполнения Walt сигнал запрещён"


def evaluate_b(data, bars):
    fast, mid, hourly = data["5m"], data["15m"], data["1h"]
    long_break = fast["close"] > fast["resistance_prev20"] and mid["close"] > mid["ema20"]
    short_break = fast["close"] < fast["support_prev20"] and mid["close"] < mid["ema20"]
    if not (long_break or short_break):
        return "Нет подтверждённого пробоя локального уровня"
    direction = "LONG" if long_break else "SHORT"
    if fast["volume_mean_prev20"] <= 0 or fast["volume_last"] < 1.5 * fast["volume_mean_prev20"]:
        return "Недостаточное подтверждение пробоя объёмом"
    if abs(fast["close"] - fast["ema20"]) > 2 * fast["atr14"]:
        return "Цена слишком далеко от EMA20: запрет догонять импульс"
    if direction == "LONG" and (fast["rsi14"] > 75 or hourly["close"] < hourly["ema50"]):
        return "Перекупленность или конфликт с часовым трендом"
    if direction == "SHORT" and (fast["rsi14"] < 25 or hourly["close"] > hourly["ema50"]):
        return "Перепроданность или конфликт с часовым трендом"
    return f"Условный технический кандидат {direction}; без расчёта исполнения Walt сигнал запрещён"


def scan():
    out = {"mode": "READ_ONLY_RESEARCH", "source": "Binance spot public klines",
           "execution": "DISABLED", "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "assets": {}}
    for symbol in ASSETS:
        try:
            bars = {tf: fetch_candles(symbol, tf) for tf in INTERVALS}
            data = {tf: calculate(v) for tf, v in bars.items()}
            out["assets"][symbol] = {"timeframes": data, "strategy_a": evaluate_a(data, bars),
                                      "strategy_b": evaluate_b(data, bars), "trade_ready": False,
                                      "blocker": "External spot candles differ from Walt perpetuals; verify Walt price, market liquidity, USDC collateral, min size, stop, TP and net RR before trading"}
        except Exception as exc:
            out["assets"][symbol] = {"error": str(exc), "strategy_a": "NO_SIGNAL",
                                      "strategy_b": "NO_SIGNAL", "trade_ready": False}
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()
    result = scan()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if all("timeframes" in x for x in result["assets"].values()) else 2)