# Walt read-only market monitor

Public-market research scanner for BTCUSDT / ETHUSDT spot OHLCV at 5m, 15m, 1h.

- Uses only public Binance klines. No keys, wallet connection or trading methods.
- Evaluates preliminary technical setups for A (Trend Following) and B (Momentum Breakout).
- **Never creates executable orders**; all reports set trade_ready=false.
- Scheduled every 15 minutes via GitHub Actions (best effort).
- Run Actions > Walt read-only BTC ETH monitor > Run workflow.
- Inspect run Summary and walt-report JSON artifact. Network failure means NO SIGNAL, never a fallback guess.
- Binance spot market prices and volume are not Walt USDC perpetual prices. Final trade approval additionally requires Walt price, contract, margin, liquidity, fee, slippage, stop, TP and net risk checks.
- Never store Walt trading credentials here.
