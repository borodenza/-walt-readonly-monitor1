# Mira SHORT: BTC external context (research only)

Run: `python3 mira_short_context.py --json` (Python 3 standard library; no API key).

The module downloads **closed** BTCUSDT spot 15-minute candles from the Binance public market-data endpoint. It validates OHLCV, timestamp continuity and freshness; computes EMA20/50/200, RSI14, rolling 24h and 7d returns, geometric daily 7d return, volume confirmation and an elementary failed-rebound proxy. It fails closed on stale/missing data.

**This is NOT a Walt trade signal.** Binance spot BTCUSDT is not Walt BTC-USDC perpetual. No Binance quote, candle, bid/ask or depth may be presented as verified Walt market data. The script does not connect to Walt, GitHub secrets, Telegram, or any wallet, and contains no trading or order methods. Its output always sets `walt_signal_verified=false` and `trade_ready=false`, even when `research_short_context=true`.

Before proposing a Walt SHORT, separately verify using Walt read-only tools: all-wallet positions, contract id and current rate, Walt 24h/7d returns, actual Walt bid/ask and depth, fresh failed rebound, OI/volume, usable USDC collateral and conversion from USDT if applicable, funding, fees, contract minimum/step, structural SL, TP and complete stressed net R:R >= 2 with risk <= 10% of usable collateral and >= $1. If Walt does not expose the required information, report **NOT READY**, not a confirmed signal.

This module is a manually run research helper, not integrated with the scheduled ChatGPT automation. Existing strategy rules and manual two-stage order confirmation are unchanged.
