# Walt Mira SHORT — system specification (active)

Active strategy since 2026-11-09: **SHORT only**, based only on connected Walt Perps read-only data. See [rules/strategy.md](rules/strategy.md) for conditions and [PROMPT.md](PROMPT.md) for agent instructions.

## Topology
- ChatGPT scheduled monitor: every 4 hours, condition watch; read-only Walt queries for actual market eligibility, account balances, orders and positions. One proposal maximum; no message when none qualifies.
- GitHub: versioned strategy documents and offline risk tooling. Historical Hyperliquid LONG scan is disabled, and workflow has no scheduled market requests or order access.
- Interactive chat: only after user selects «ПРОВЕРИТЬ ID» may a fresh, bounded Walt preview be requested. «ИСПОЛНИТЬ ИМЕННО ЭТОТ ОРДЕР» is a separate explicit authorization, not implied by the first reply.

## Required signals
24h <= −5% and numerical 7d > 24h from Walt; high OI and 24h turnover, fresh spread/depth, confirmed lower move after rebound. 7d >24h by itself does not mean stabilization. Without a supported Walt history source: **NO SIGNAL**.

## Account/risk
Exactly one position wallet-wide, no conflicting pending orders; read-only balances and verified collateral currency. Max risk 10% of available applicable collateral (must allow >=$1), leverage <=5× and contract max, stop 2–2.5% above SHORT entry, net RR>=2 after stress fees, slippage, funding; minimum/step checked; account liquidation risk examined. Risk is an estimate not a guaranteed fill. No automatic leverage/capital increases.

## Retired implementation
Files `mira.py`, `walt_market_analysis.py`, `walt_status.py`, `walt_guard.py` and their legacy tests are **historical code only**, not active scanner code. Do not run these as a substitute for Walt sourcing or present their reports as current eligible signals.

System state: READ_ONLY_SHORT_SCOUT. Automatic execution: DISABLED.
