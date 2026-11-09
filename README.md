# Walt Mira SHORT — Walt-only futures scout

**Active from 9 November 2026:** SHORT after a sharp 24-hour fall and a confirmed failed rebound. This supersedes Mira Recovery LONG. Trading signals are sourced only from the connected Walt read-only tools, never Github or Hyperliquid.

The ChatGPT condition-watch automation checks **every four hours** and can recommend at most one deal. It never prepares, places or changes orders. Any trade needs a separate live preview and an explicit second execution confirmation.

Risk: maximum **10% of usable available collateral**, minimum eligible loss budget **$1**, leverage **≤5×**, SHORT stop **2–2.5% above entry**, net R:R **≥2** after expenses, no more than one position across Walt. If any required market/account data is unavailable or stale, **no signal**. Stop orders do not guarantee a fill price.

- [Strategy](rules/strategy.md)
- [Agent/system prompt](PROMPT.md)
- [System topology](SYSTEM.md)
- [Maintenance agent instructions](AGENTS.md)
- [Trade journal template](journal/last_trades.csv)

GitHub Actions runs a **configuration audit only on changes/manual dispatch**; it no longer scans Hyperliquid every 15 minutes. The old scripts `mira.py`, `walt_market_analysis.py`, `walt_status.py`, `walt_guard.py` and `tests/` are kept as historical source code, **not active**. Do not use their old LONG report `walt-report.json` to select trades.

Walt read-only MCP may not expose 24h/7d price history or live book depth. Until those data points can be verified through an authorized Walt source, the scout correctly refuses to issue a trade. Never commit keys, account tokens or actual trading history to this public repository.
