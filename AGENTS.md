# Walt Mira SHORT — instructions for code and monitoring agents

Single active strategy: read-only **SHORT after a sharp fall and failed rebound**. Consult `rules/strategy.md` and `PROMPT.md` first. Previous Mira Recovery LONG / Trend Following / Momentum Breakout are retired and MUST NOT be used for proposals.

The ChatGPT automation is the ONLY scheduled trading-signal scout. It checks every 4 hours, consumes **Walt read-only** market/account data, and fails closed. Historical 24h/7d changes, bid/ask/depth, liquidity, margin conversions and positions must actually be available; a current rate alone is insufficient. NEVER infer price history or use legacy `walt-report.json`, Hyperliquid, Binance or other venue as signal inputs.

GitHub is documentation and optional offline risk calculations, not a live price feed. `.github/workflows/walt-readonly-monitor.yml` validates configuration on changes and is intentionally NOT a market scanner. The old `mira.py`, `walt_market_analysis.py`, `walt_status.py`, `walt_guard.py` and `tests/` are historical sources only, not operational rules or live-signal validation.

Risk: up to 10% of usable free collateral, minimum allowed stress loss of $1 for consideration; leverage <= 5x and <= contract max; SHORT SL 2–2.5% above Walt entry, net RR>=2, conservative fees, funding, slippage, min contract size and available margin verified. Never assume USDT and USDC balances are interchangeable. Up to one position wallet-wide and one candidate per scan.

The scheduled agent MUST NEVER invoke `perps_prepare_*` or `perps_execute_operation`. Any fully verified proposal gets a unique short-lived ID and “ПРОВЕРИТЬ ID” / “ОТКЛОНИТЬ ID”. Those are not execution. A separate live interactive revalidation+Walt preview and a second precise consent “ИСПОЛНИТЬ ИМЕННО ЭТОТ ОРДЕР” are required before execution.

No keys or tokens in this public repository; no trade history with personal financial details. Missing or stale data => **no notifications and no trades**.
