Team Cool as Code — STRATEGY DOCUMENTATION
==================================

PATTERN DISCOVERED
------------------
Through exhaustive statistical analysis of 116,346 one-minute OHLCV bars,
we identified the hidden mathematical pattern embedded in Asset Alpha:

  >>> VOLATILITY SQUEEZE → VOLUME BREAKOUT → Z-SCORE MEAN REVERSION <<<

The three features computed in the starter notebook (Section 3) are
deliberate breadcrumbs pointing to this pattern:

  1. ROLLING 5-PERIOD VOLATILITY: Detects "squeeze" phases when price
     compresses into a narrow range (below the 15th percentile of
     historical volatility).

  2. VOLUME RATIO (vs 10-period average): Detects breakout events when
     trading volume spikes above 1.8-2.5x the recent average,
     signaling institutional activity or regime change.

  3. 30-PERIOD Z-SCORE: Determines breakout DIRECTION via mean
     reversion. When price is below its 30-period mean (Z < 0), the
     post-breakout drift is positive. When above (Z > 0), the drift
     is negative.

STATISTICAL EVIDENCE:
  - Squeeze (vol < 15pct) + Volume spike (> 2.5x) with Z < 0:
    Forward 10-bar return = +0.076% (n=322 events)
  - Same condition with Z > 0:
    Forward 10-bar return = -0.059% (n=464 events)
  - Spread = 0.135% — the strongest signal in the dataset

ADDITIONAL FINDINGS:
  - Hurst exponent: 0.557 (near random walk)
  - Return autocorrelation lag-1: +0.017 (weak positive momentum)
  - Runs test Z-score: -30.3 (returns cluster in direction)
  - Volatility clustering: |return| autocorrelation +0.21 at lag-1
  - 780-bar (2-day) cycle detected via F-ratio analysis (F=5.09)

WHY WE CHOSE NOT TO ACTIVELY TRADE THE PATTERN
-----------------------------------------------
Despite confirming the pattern's statistical significance, our backtest
across 296 rolling 1080-bar windows proved that ACTIVE TRADING DESTROYS
VALUE in this market:

  Strategy              Mean P&L    Beats Hold
  ─────────────────────────────────────────────
  Pure Hold 58%          -1.33%      baseline
  Breadcrumb strategy    -2.21%      15.9%
  SMA Crossover          -3.82%       4.1%
  Momentum trading       -6.12%       0.0%
  Adaptive multi-signal  -3.29%       2.4%

The root cause: the 0.1% transaction fee (0.2% round-trip) exceeds
the per-trade edge of every signal we identified. The squeeze-breakout
signal has a 0.135% theoretical spread, but after entry + exit fees of
0.2%, the net expected value per trade is NEGATIVE.

Furthermore, uninvested cash decays at 0.02%/minute (~3.5% over 3 hours),
creating strong pressure to deploy capital rather than time the market.

STRATEGY IMPLEMENTED
--------------------
Based on these findings, our strategy optimizes for the two factors that
actually determine competition outcome:

  1. MINIMIZE CASH DECAY by maintaining maximum practical allocation
  2. PROTECT AGAINST CATASTROPHIC LOSS via regime-aware drawdown stops

Implementation:
  - BUY to 59% allocation on tick 0 (just below 60% server cap)
  - HOLD through normal market fluctuations
  - BEARISH BREAKOUT STOP: If a confirmed squeeze-breakout occurs with
    bearish z-score (Z > 1.0) and negative momentum, reduce to 35%
  - CRASH STOP: If session drawdown exceeds 8%, reduce to 20%
  - RECOVERY: Restore 59% when drawdown recovers below 3% with
    positive momentum

POSITION SIZING
---------------
  - Target: 59% of net worth in shares
  - Rationale: Maximizes market exposure while staying safely below the
    60% server-enforced cap. If we targeted exactly 60%, a small price
    uptick could trigger server-side forced liquidation (incurring fees).
  - The remaining 41% cash absorbs ~1.5% decay over 3 hours — an
    acceptable cost for maintaining rebalancing capacity.
  - Trade threshold: 8% position drift required before rebalancing,
    preventing fee-generating noise trades.

RISK MANAGEMENT
---------------
  - Maximum 5 trades over the entire competition (hard cap)
  - 8% drawdown stop: reduces to 20% allocation during severe crashes
  - Bearish breakout detector: uses the discovered pattern defensively
    (not to generate alpha, but to avoid loss during confirmed regime
    changes)
  - Recovery requires both reduced drawdown (< 3%) AND positive momentum
    confirmation to avoid premature re-entry during ongoing crashes
  - Rebalance band of 8%: suppresses whipsaw from normal price drift

EXPECTED PERFORMANCE
--------------------
  - Mean P&L: -1.3% (driven by unavoidable cash decay on 41% cash)
  - Win rate: ~25% of scenarios (requires asset appreciation > 2.5%)
  - Worst case: -13% (extreme crash without recovery)
  - Best case: +8.4% (strong uptrend)
  - Expected trades: 1 (initial buy only) in normal conditions
  - Sharpe ratio: highest among all strategies tested

TECHNICAL REQUIREMENTS
----------------------
  - Reads API_URL and TEAM_API_KEY from environment variables or .env
  - Runs via: python agent.py
  - Handles both HTTP and HTTPS endpoints
  - Retry logic: 3 attempts per API call with backoff
  - Single failed request does NOT crash the agent
  - Terminates cleanly on Ctrl+C (KeyboardInterrupt handled)
  - Rate-limit aware: handles HTTP 429 with 2-second backoff