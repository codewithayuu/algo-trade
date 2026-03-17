"""
==========================================================================
Team Cool as Code — Algorithmic Trading Agent
Strategy: Disciplined Capital Deployment with Regime Awareness
==========================================================================
Core thesis: The asset exhibits a volatility-squeeze → volume-breakout
pattern with z-score-based mean reversion. However, the 0.1% transaction
fee exceeds the per-trade edge, making active exploitation unprofitable.
The optimal strategy is to deploy capital at maximum allocation, minimize
trades, and protect against catastrophic drawdowns only.
==========================================================================
"""

import os
import sys
import time
import requests
import numpy as np
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

def load_env(path=".env"):
    """Load environment variables from .env file if present."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()

API_URL = os.getenv("API_URL", "https://algotrading.sanyamchhabra.in/api")
API_KEY = os.getenv("TEAM_API_KEY", "")
HEADERS = {"X-API-Key": API_KEY}

# Strategy parameters (backed by 296-window backtest)
TARGET_ALLOC    = 0.59   # Changed from 0.58 → 0.59 (data shows higher = better)
CRASH_ALLOC     = 0.20   # Reduced allocation during crash
CAUTIOUS_ALLOC  = 0.35   # Reduced allocation on bearish breakout
REBAL_BAND      = 0.08   # Only trade if position drifts > 8%
CRASH_DD        = 0.08   # Session drawdown threshold for crash stop
RECOVERY_DD     = 0.03   # Drawdown recovery to restore allocation
MAX_TRADES      = 5      # Hard cap on total trades
TICK_INTERVAL   = 10     # Seconds between ticks


# ═══════════════════════════════════════════════════════════════════════
# API HELPERS (robust, retry-enabled, crash-proof)
# ═══════════════════════════════════════════════════════════════════════

def api_call(method, endpoint, data=None):
    """
    Make an API call with retry logic.
    A single failed request will NOT crash the agent.
    Returns None on failure after retries.
    """
    # Remove /api prefix if it exists in endpoint since API_URL already includes it
    if endpoint.startswith('/api'):
        endpoint = endpoint[4:]  # Remove '/api' from beginning
    url = f"{API_URL}{endpoint}"
    for attempt in range(3):
        try:
            if method == "GET":
                r = requests.get(url, headers=HEADERS, timeout=8)
            else:
                r = requests.post(url, json=data, headers=HEADERS, timeout=8)
            if r.status_code == 429:
                time.sleep(2)
                continue
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            if attempt == 2:
                print(f"  [WARN] API {endpoint} failed: {e}")
                return None
            time.sleep(1.5)
    return None


def get_price():
    return api_call("GET", "/api/price")


def get_portfolio():
    return api_call("GET", "/api/portfolio")


def buy(qty):
    if qty <= 0:
        return None
    return api_call("POST", "/api/buy", {"quantity": int(qty)})


def sell(qty):
    if qty <= 0:
        return None
    return api_call("POST", "/api/sell", {"quantity": int(qty)})


# ═══════════════════════════════════════════════════════════════════════
# FEATURE ENGINE (implements the 3 breadcrumb features)
# ═══════════════════════════════════════════════════════════════════════

class FeatureEngine:
    """
    Computes the three features from the starter notebook:
    1. Rolling 5-period volatility (squeeze detection)
    2. Volume ratio vs 10-period average (breakout detection)
    3. 30-period Z-score (mean reversion direction)
    """

    def __init__(self):
        self.prices = []
        self.volumes = []
        self.vol_history = []  # rolling vol values for percentile calc

    def update(self, price, volume):
        self.prices.append(price)
        self.volumes.append(volume)

    def ready(self):
        return len(self.prices) >= 35

    def compute(self):
        if not self.ready():
            return None

        p = np.array(self.prices)
        v = np.array(self.volumes)

        # Feature 1: Rolling 5-bar volatility
        rets = np.diff(p[-6:]) / p[-6:-1]
        roll_vol = np.std(rets)
        self.vol_history.append(roll_vol)

        # Feature 2: Volume ratio
        vol_ratio = v[-1] / (np.mean(v[-10:]) + 1e-10)

        # Feature 3: 30-bar Z-score
        mean30 = np.mean(p[-30:])
        std30 = np.std(p[-30:])
        zscore = (p[-1] - mean30) / (std30 + 1e-10)

        # Squeeze detection: is current vol in bottom 15th percentile?
        if len(self.vol_history) > 30:
            vol_15pct = np.percentile(self.vol_history, 15)
            in_squeeze = roll_vol < vol_15pct
        else:
            in_squeeze = False

        # 30-bar momentum
        mom30 = (p[-1] - p[-30]) / p[-30]

        return {
            'roll_vol': roll_vol,
            'vol_ratio': vol_ratio,
            'zscore': zscore,
            'in_squeeze': in_squeeze,
            'mom30': mom30,
            'price': p[-1],
        }


# ═══════════════════════════════════════════════════════════════════════
# STRATEGY STATE MACHINE
# ═══════════════════════════════════════════════════════════════════════

class Strategy:
    """
    States:
      NORMAL   → Hold at TARGET_ALLOC (59%)
      CAUTIOUS → Reduced to CAUTIOUS_ALLOC (35%) on bearish breakout
      CRASHED  → Emergency CRASH_ALLOC (20%) on severe drawdown
    """

    def __init__(self):
        self.state = "NORMAL"
        self.peak_nw = 0.0
        self.trade_count = 0
        self.bought_initial = False
        self.recent_squeeze = False
        self.squeeze_countdown = 0

    def decide(self, features, session_dd, pos_pct):
        """Returns (target_alloc, reason) tuple."""
        reason = ""

        # === CRASH PROTECTION (highest priority) ===
        if session_dd >= CRASH_DD and self.state != "CRASHED":
            self.state = "CRASHED"
            reason = "CRASH STOP"
            return CRASH_ALLOC, reason

        if self.state == "CRASHED":
            if session_dd <= RECOVERY_DD:
                self.state = "NORMAL"
                reason = "RECOVERED"
                return TARGET_ALLOC, reason
            return CRASH_ALLOC, reason

        # === BREADCRUMB PATTERN DETECTION ===
        if features is not None:
            # Track squeeze state
            if features['in_squeeze']:
                self.squeeze_countdown = 15  # remember squeeze for 15 ticks
                self.recent_squeeze = True
            elif self.squeeze_countdown > 0:
                self.squeeze_countdown -= 1
            else:
                self.recent_squeeze = False

            # SQUEEZE + VOLUME BREAKOUT detected
            if self.recent_squeeze and features['vol_ratio'] > 2.5:
                if features['zscore'] > 1.0 and features['mom30'] < -0.003:
                    # Bearish breakout after squeeze
                    if self.state != "CAUTIOUS":
                        self.state = "CAUTIOUS"
                        reason = "BEARISH BREAKOUT"
                        return CAUTIOUS_ALLOC, reason

            # Recovery from cautious
            if self.state == "CAUTIOUS":
                if features['mom30'] > 0.002 and features['zscore'] > -0.5:
                    self.state = "NORMAL"
                    reason = "TREND RESTORED"
                    return TARGET_ALLOC, reason
                return CAUTIOUS_ALLOC, reason

        # === DEFAULT: HOLD AT TARGET ===
        return TARGET_ALLOC, reason


# ═══════════════════════════════════════════════════════════════════════
# MAIN TRADING LOOP
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 62)
    print("  TEAM :- Cool as Code 🦇🦇 | Disciplined Capital Deployment")
    print("  Strategy: Hold 59% + Regime Awareness + Crash Protection")
    print("=" * 62)
    print(f"  API: {API_URL}")
    print(f"  Key: {'configured' if API_KEY else 'MISSING!'}")
    print()

    if not API_KEY:
        print("ERROR: TEAM_API_KEY not set. Add to .env or environment.")
        sys.exit(1)

    engine = FeatureEngine()
    strategy = Strategy()
    tick = 0

    while True:
        try:
            # ── Fetch market data ──
            td = get_price()
            port = get_portfolio()

            if td is None or port is None:
                print(f"T{tick:>4d} | API error, skipping tick")
                tick += 1
                time.sleep(TICK_INTERVAL)
                continue

            price   = td["close"]
            phase   = td.get("phase", "unknown")
            cash    = port["cash"]
            shares  = port["shares"]
            nw      = port["net_worth"]
            pnl     = port.get("pnl_pct", 0.0)
            volume  = td.get("volume", 0)

            # ── Market closed? ──
            if phase == "closed":
                print(f"\n{'='*62}")
                print(f"  MARKET CLOSED")
                print(f"  Final NW: ${nw:,.2f} | PnL: {pnl:+.2f}%")
                print(f"  Trades: {strategy.trade_count}")
                print(f"{'='*62}")
                break

            # ── Update features ──
            engine.update(price, volume)
            features = engine.compute() if engine.ready() else None

            # ── Portfolio metrics ──
            strategy.peak_nw = max(strategy.peak_nw, nw)
            session_dd = (strategy.peak_nw - nw) / strategy.peak_nw \
                if strategy.peak_nw > 0 else 0.0
            pos_pct = (shares * price) / nw if nw > 0 else 0.0

            # ── Strategy decision ──
            target, reason = strategy.decide(features, session_dd, pos_pct)
            target = min(target, 0.59)

            # ── Execute trade if needed ──
            action = "HOLD"
            need_trade = (not strategy.bought_initial) or \
                         (reason != "") or \
                         (abs(pos_pct - target) > REBAL_BAND)

            if need_trade and strategy.trade_count < MAX_TRADES:
                tgt_shares = int(target * nw / price)
                diff = tgt_shares - shares

                if diff > 0:
                    max_buy = int(cash * 0.99 / (price * 1.001))
                    qty = max(0, min(diff, max_buy))
                    if qty > 0:
                        result = buy(qty)
                        if result is not None:
                            action = f"BUY {qty}"
                            strategy.trade_count += 1
                            strategy.bought_initial = True

                elif diff < 0:
                    qty = min(-diff, shares)
                    if qty > 0:
                        result = sell(qty)
                        if result is not None:
                            action = f"SELL {qty}"
                            strategy.trade_count += 1

                # Refresh portfolio after trade
                if action != "HOLD":
                    port = get_portfolio()
                    if port:
                        nw = port["net_worth"]
                        pnl = port.get("pnl_pct", 0.0)
                        shares = port["shares"]
                        pos_pct = (shares * price) / nw if nw > 0 else 0

            # ── Log ──
            tag = f" [{reason}]" if reason else ""
            flag = "*" if action != "HOLD" else " "
            st = strategy.state[0]
            mom_str = f"{features['mom30']:+.4f}" if features else "  wait"
            print(f"{flag}T{tick:>4d} [{st}] {action+tag:<30s} | "
                  f"p={price:>8.2f} | pos={pos_pct:.0%} | "
                  f"nw=${nw:>10,.0f} | dd={session_dd:.1%} | "
                  f"pnl={pnl:+.2f}% | m={mom_str}")

            tick += 1

        except KeyboardInterrupt:
            print("\n  Agent stopped by user. Exiting.........")
            print("\n  Happyy tradinggg :).........")
            break
        except Exception as e:
            print(f"T{tick:>4d} | ERROR: {type(e).__name__}: {e}")
            tick += 1

        try:
            time.sleep(TICK_INTERVAL)
        except KeyboardInterrupt:
            print("\n  Agent stopped by user. Exiting.........")
            print("\n  Happyy tradinggg :).........")
            break


if __name__ == "__main__":
    main()