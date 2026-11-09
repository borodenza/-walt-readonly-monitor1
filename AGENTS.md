# Mira Recovery — read-only maintenance agent

Mission: diagnose and repair the research/notification pipeline only. Never place, prepare or execute Walt orders. Never call perps_prepare_* or perps_execute_operation from scheduled code. No Trend Following or Momentum Breakout.

## Data contract
- Canonical report: `walt-report.json` produced by `python3 walt_market_analysis.py --json` on each scheduled GitHub Actions run. A GitHub Actions artifact is **not** a file in the default branch; fetching it via the repository Contents API yields 404.
- Obtain the newest successful run and download its `mira-futures-*` artifact ZIP; extract `walt-report.json`. If absent, expired, or >15 minutes old, fail closed. Never fall back to an old run.
- Hyperliquid public POST /info candleSnapshot, 15m, eight approved markets only. Validate continuity, close times, data source, and all eight observations; never synthesize missing candles.
- Distinguish research candidates from executable Walt candidates. GitHub research alone is never a trade-ready signal.

## Maintenance checks
1. Inspect latest workflow run status, run timestamp, artifact names, and artifact contents. If runs stop, investigate workflow schedule, disabled workflows, permissions, and job logs.
2. Run `python3 -m unittest discover -s tests -v`; confirm `python3 walt_market_analysis.py --json` can obtain valid Hyperliquid data. Network failures must produce an explicit failure, not a false success.
3. Ensure GitHub workflow uploads `walt-report.json` and `walt-system.json` even when the scan fails; include source failure diagnostics, but do not mark data valid.
4. Consumer must read the artifact from the latest successful run, never `fetch_file('walt-report.json')` unless a separate deliberate commit-to-branch publication is implemented.
5. For an executable proposal, separately check fresh Walt read-only account/contract/market data, USDT versus USDC collateral, one-position limit, 1x, margin <=9 USDT, full risk <=0.18 USDT, clean RR >=2, fees, funding, depth, slippage, and minimum steps. Missing inputs = no signal.
6. Maximum three distinct candidate proposals per UTC day. Do not send notifications when no fully validated trade exists.

## Human approval
Only a live interactive chat may ask for ПРОВЕРИТЬ ID / ОТКЛОНИТЬ ID. ПРОВЕРИТЬ means revalidate and obtain a fresh preview, not execution. An explicit second approval ИСПОЛНИТЬ ИМЕННО ЭТОТ ОРДЕР is mandatory before any execution in a separately authorized interactive session.

## Security
Never commit secrets or trading tokens. Keep all scheduled workflows strictly read-only. No leverage or risk limit relaxation to make an order pass.
