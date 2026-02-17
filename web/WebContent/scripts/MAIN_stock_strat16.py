"""
# =============================================================================
# VERSION HISTORY (v14 → v15 → v16) – keep track of improvements
# =============================================================================
#
# v14 (MAIN_stock_strat14):
# - Parabola detector: mathematical curve fitting for parabolic patterns;
#   end-of-bullish-parabola = SHORT signal, end-of-bearish-parabola = LONG.
# - Fixed thresholds (Buy=16, Sell=13), min strength ≥4/10, MTF advisory only.
# - 10-year cache with incremental tail extension, per-symbol progress output.
# - Webhook enabled for website / MegaBot (--send-webhook).
# - All prior indicators (RSI/MACD/Stoch RSI/OBV/BB/Keltner/Ichimoku/SuperTrend/etc.).
#
# v15 (MAIN_stock_strat15) – adds over v14:
# - Hard stop loss: e.g. 3% from entry, only after N days (e.g. 3) to avoid
#   premature exits (--use-hard-stop-loss, --hard-stop-loss-pct, --hard-stop-min-days).
# - Conservative take profit: lock in part of gains and let the rest run
#   (e.g. exit 50% at +2.5%; --use-conservative-tp, --conservative-tp-profit-pct,
#   --conservative-tp-exit-pct). Improves risk/reward when trend continues.
#
# v16 (MAIN_stock_strat16) – adds over v15:
# - Triple RSI bearish divergence buy-block: when ≥3 RSI bearish (or hidden
#   bearish) divergence *events* occur within a lookback (e.g. 120 bars), block
#   BUYs for N days (e.g. 14). SELLs are not blocked.
#   Rationale: trend-only can be naive; overextended names (e.g. silver in a
#   strong trend that then collapsed quickly) show that divergence gate helps
#   avoid buying into exhaustion. More strict = fewer longs, but plenty of
#   other assets to choose from.
#   Flags: --rsi-bear-div-block-use, --rsi-bear-div-block-days,
#   --rsi-bear-div-event-lookback, --rsi-bear-div-event-threshold,
#   --rsi-bear-div-include-hidden; disable with --no-rsi-bear-div-block-use.
# - Exit early on parabola break: close position when parabola breaks (trend
#   exhaustion); --exit-early-on-parabola-break / --no-exit-early-on-parabola-break.
# - Exit early on ADX drop: close when ADX falls below threshold (trend
#   weakening); --exit-early-on-adx-drop, --exit-adx-drop-threshold.
# - MTF monthly option: --mtf-monthly / --no-mtf-monthly.
# - Conservative TP and hard stop (same as v15) plus parameter sweep,
#   VWAP backtest (--vwap-backtest), components backtest (--components-backtest).
# - Ichimoku Tenkan/Kijun option: --ichimoku-tenkan-kijun.
# - Logging: --log-file, --log-level, --no-log-file.
#
# =============================================================================

cd /Users/olivia2/Desktop/Stock_Strats
python3 MAIN_stock_strat6.py --symbols XLK,XLY,XLP,XLI,XLB,XLRE,XLU,XLC,XLF,XLV,XLE,SOXX,NVDA,SPY,GLD,SLV,PPLT,PALL,USO,EEM,PCEF,HYG,MCHI,INDA,EWJ,EWG,EWT --interval 1d --debug
python3 MAIN_stock_strat6.py --symbols SPY --interval 1d --debug --no-use-mtf-confirmation  # Disable MTF
python3 MAIN_stock_strat6.py --symbols GLD,SLV,PPLT,PALL --interval 1d --debug  # Precious metals focus
python3 MAIN_stock_strat6.py --symbols EEM,MCHI,INDA,EWJ,EWG,EWT --interval 1d --debug  # International markets
python3 MAIN_stock_strat6.py --symbols PCEF,HYG --interval 1d --debug  # Credit/income markets

MAIN_stock_strat11.py - High-Conviction Strategy with Tightened Thresholds and Quality Filters

Enhancements over MAIN_stock_strat10.py (v11 NEW):
- **FIXED DEPRECATION WARNINGS**: Replaced deprecated 'M' frequency with 'ME' for monthly resampling
- **FIXED DIVIDE-BY-ZERO ERRORS**: Added guards in RSI divergence calculations to prevent RuntimeWarnings
- **CODE QUALITY**: Improved error handling and code robustness

Goal
- Comprehensive stock strategy that combines multiple indicators across all major categories
  for robust signal generation, with per-asset parameter optimization and email alerts.
- NEW in v5: Multi-timeframe confirmation using daily → weekly → monthly resampling
  to boost signal strength when multiple timeframes align (default ON).

Strategy Intent (per user)
- Focus on momentum in medium to large cap stocks (steady, grinding uptrends).
- NOT the micro-cap extreme-weakness dip-buy strategy (already covered elsewhere).
- Acknowledge the psychological "buying the top" feel in extended trends; design
  risk management with practical stops to avoid outsized losses if the trend has
  already run its course.

Included indicators (comprehensive set - 37 total)
- Trend: EMA fast vs EMA slow (trend direction), ADX(14) (trend strength), ADX Divergence (price vs ADX trend strength divergence), Parabolic SAR (trend following), Ichimoku Cloud (comprehensive trend system), SuperTrend (ATR-based trend/stop), SuperTrend Slope Divergence (price vs SuperTrend slope divergence), Parabola Detection (mathematical curve fitting for parabolic patterns)
- Momentum: RSI(14), RSI Divergence (price vs RSI divergence), Stochastic RSI(14,14,3), Stochastic RSI Divergence (price vs Stochastic RSI divergence), MACD(12,26,9), MACD Divergence (price vs MACD divergence), Williams %R(14), Williams %R Divergence (price vs W%R divergence), CCI(20), CCI Divergence (price vs CCI divergence), MFI(14), MFI Divergence (price vs MFI divergence), ROC(12), ROC Divergence (price vs ROC divergence)
- Volatility: ATR(14), ATR-SMA(20), Bollinger Bands(20,2.0), Bollinger Band Width Divergence (price vs BB width divergence), Keltner Channels(20,2.0), ATR Channels with squeeze/bounce/breakout
- Volume: Volume SMA(20) ratio, VWAP (daily session), OBV (On-Balance Volume), OBV Divergence (price vs OBV divergence), Volume Profile (HVN/LVN analysis), VROC (Volume Rate of Change), VROC Divergence (price vs VROC divergence)
- Support/Resistance: Donchian Channel(20) breakout as a simple S/R proxy
- Candlestick: Bullish/Bearish Engulfing patterns
- ML/Statistical: Z-Score(20) of Close
- Timing: Day-of-week filter (skip Fridays by default) [optional]

Enhancements over MAIN_Stock_strat5.py (v6 NEW):
- **TIGHTENED THRESHOLDS**: Buy=22 (58%), Sell=18 (47%) - requires majority indicator agreement
- **MINIMUM STRENGTH FILTER**: Only acts on signals ≥4/10 strength (eliminates weak noise)
- **MARKET BREADTH FILTER**: Requires ≥30% of symbols agreeing before acting (prevents countertrend trades)
- **ENFORCED MTF CONFIRMATION**: Requires weekly OR monthly timeframe alignment (no more "D-only" signals)
- **QUALITY OVER QUANTITY**: Reduces signal frequency from 100% to ~5-10%, targeting high-conviction setups only

Enhancements over MAIN_stock_strat4.py (v5):
- Added Multi-Timeframe Confirmation: Resamples daily data to weekly/monthly timeframes
  and boosts signal strength when multiple timeframes align (toggleable, default ON)
  - Daily only: Strength 1-3/10 (no higher timeframe confirmation)
  - Daily + Weekly: Strength boost of up to 50% (e.g., 2/10 → 3-4/10)
  - Daily + Weekly + Monthly: Strength boost of up to 100% (e.g., 2/10 → 4-6/10)
  - MTF indicator shows alignment: "MTF:W+M" (both), "MTF:W" (weekly only), "MTF:D-only" (daily only)

Enhancements over MAIN_stock_strat2.py:
- Added Bollinger Bands: volatility-based support/resistance with squeeze detection
- Added Keltner Channels: ATR-based volatility channels (complementary to Bollinger Bands)
- Added OBV: On-Balance Volume for cumulative volume flow and divergence detection
- Added Ichimoku Cloud: comprehensive trend analysis system with 5 components and dynamic support/resistance
- Added Stochastic RSI: enhanced momentum oscillator (0-100 scale)
- Added MACD: trend momentum confirmation with crossover signals
- Added Williams %R: additional momentum oscillator (-100 to 0 scale)
- Added CCI: Commodity Channel Index momentum oscillator (-200 to +200 scale)
- Added MFI: Money Flow Index volume-weighted momentum oscillator (0-100 scale)
- Added Parabolic SAR: trend-following stop and reverse indicator with dynamic stop levels
- Added ROC: Rate of Change momentum indicator measuring percentage price change
- Added ATR Channels: volatility-based dynamic support/resistance with squeeze/bounce/breakout signals
- Added Volume Profile: High Volume Nodes (HVN) and Low Volume Nodes (LVN) analysis for support/resistance and breakout zones
- Added VROC: Volume Rate of Change for volume momentum and acceleration/deceleration analysis
- Added RSI Divergence: Price vs RSI divergence detection for reversal signals (regular and hidden divergences)
- Added ADX Divergence: Price vs ADX trend strength divergence analysis for detecting when price moves lack trend conviction
- Per-asset parameter optimization via asset_params.json
- Email alerts integration with configurable thresholds
- CLI parameter overrides for real-time tuning
- Parameter sweep functionality for optimization

Notes
- Keeps dependencies light: pandas, numpy, yfinance, requests
- Default timeframe: 1h (aligned with your TV usage)
- Webhook payload matches your Main_MEGABOT expectation: {"action": "buy|sell", "symbol": "SYMBOL/USD"}
- Score-based voting system: requires multiple indicator confirmation for signals
- All parameters configurable per-asset via JSON config file

Future Enhancement Suggestion:
- Hidden Markov Model. Machine learning. K-means. RNN. Hidden forest. Decision tree.
- Custom built indicators such as parabola. Elliot wave. 
- Financial health analyzer. Done. But can we incorporate it?
- Give lesser known indicators less weight, like .5 of a vote.

TODO: Automation Features (for Interactive Brokers or other automated trading platforms)
- Risk-based position sizing: Calculate actual dollar/percentage position sizes based on:
  * Account equity
  * Risk per trade percentage (e.g., 2% of capital)
  * Stop loss distance (from ATR or fixed %)
  * Formula: position_size = (equity × risk_pct) / stop_distance_pct
  * This ensures consistent risk per trade regardless of stop distance
- Interactive Brokers API integration for automated order execution
- Real-time position tracking and portfolio management
- Automatic stop-loss and take-profit order placement
- Position sizing integration with conviction multipliers (multiply base risk-based size by conviction)
"""

from __future__ import annotations

import argparse
import glob
import gzip
import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional
from pathlib import Path

# Analysis timestamp tracking (persistent between sessions)
ANALYSIS_TIMESTAMP_FILE = Path("/Users/olivia2/Desktop/Stock_Strats/.last_analysis_timestamp")
MIN_HOURS_BETWEEN_ANALYSES = 11  # Minimum hours between analysis runs (default: 11 hours)

def get_last_analysis_time() -> Optional[datetime]:
    """Get the timestamp of the last analysis run from persistent file."""
    try:
        if ANALYSIS_TIMESTAMP_FILE.exists():
            with open(ANALYSIS_TIMESTAMP_FILE, 'r') as f:
                timestamp_str = f.read().strip()
                return datetime.fromisoformat(timestamp_str)
    except Exception as e:
        # Silently fail - if we can't read it, we'll just run analysis
        pass
    return None

def update_analysis_timestamp():
    """Update the timestamp file with current time (persistent between sessions)."""
    try:
        ANALYSIS_TIMESTAMP_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ANALYSIS_TIMESTAMP_FILE, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        # Silently fail - timestamp update is not critical
        pass

def should_skip_analysis(min_hours: float = MIN_HOURS_BETWEEN_ANALYSES) -> Tuple[bool, Optional[str]]:
    """
    Check if analysis should be skipped due to recent run.
    Returns: (should_skip, reason_message)
    """
    last_time = get_last_analysis_time()
    if last_time is None:
        return False, None
    
    hours_since = (datetime.now() - last_time).total_seconds() / 3600.0
    if hours_since < min_hours:
        reason = f"Last analysis was {hours_since:.1f} hours ago (minimum {min_hours} hours required). Next run in {min_hours - hours_since:.1f} hours."
        return True, reason
    return False, None

import math
import numpy as np
import pandas as pd
import requests
import yfinance as yf
from io import StringIO

# Global debug flag (set by main() from CLI args)
ARGS_DEBUG = False

# Import Bollinger Bands
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "Seperating_Funcs"))
from BollingerBands import bollinger_bands

# Push notification alerts integration
try:
    from pushover_alerts import PushoverAlerts
    PUSH_ALERTS_AVAILABLE = True
except ImportError:
    PUSH_ALERTS_AVAILABLE = False
    print("⚠️  Push alerts not available. Install pushover_alerts.py for mobile notifications.")

# Email alerts integration (fallback)
try:
    from email_alerts import StockAlertEmailer
    EMAIL_ALERTS_AVAILABLE = True
except ImportError:
    EMAIL_ALERTS_AVAILABLE = False
    print("⚠️  Email alerts not available. Install email_alerts.py for remote monitoring.")


# ----------------------------
# Data fetch with simple caching
# ----------------------------
def _cache_paths(symbol: str, start: str, end: str, interval: str) -> Tuple[str, str]:
    cache_dir = os.path.join(os.path.dirname(__file__), "data_cache")
    os.makedirs(cache_dir, exist_ok=True)
    base = f"{symbol}_{start}_{end}_{interval}"
    return os.path.join(cache_dir, base + ".csv"), os.path.join(cache_dir, base + ".meta")


def _find_large_cache(symbol: str, interval: str) -> Optional[str]:
    """
    Check data_cache_csv for 10-year cache files (2015-2025).
    Returns path to cache file if found, None otherwise.
    """
    cache_csv_dir = os.path.join(os.path.dirname(__file__), "data_cache_csv", symbol.upper(), interval)
    if not os.path.exists(cache_csv_dir):
        return None
    
    # Look for files with 2015 date range (10-year cache)
    pattern = os.path.join(cache_csv_dir, f"{symbol.upper()}_*_2015*.csv.gz")
    matches = glob.glob(pattern)
    if matches:
        # Return the most recent file
        return max(matches, key=os.path.getmtime)
    return None


def fetch_history(
    symbol: str,
    start: str,
    end: str,
    interval: str = "1h",
    max_age_hours: int = 6,
) -> pd.DataFrame:
    # Paths for per-window short-term CSV cache
    csv_path, meta_path = _cache_paths(symbol, start, end, interval)

    # FIRST: Try to use large cache from data_cache_csv (10-year files). For daily
    # data we allow the last bar to be up to 7 days old; if it's older, we try to
    # *extend* the large cache forward (from short-term cache or a small tail fetch)
    # instead of redownloading the entire 10-year history.
    large_cache_path = _find_large_cache(symbol, interval)
    if large_cache_path:
        try:
            df = pd.read_csv(
                gzip.open(large_cache_path, "rt"),
                parse_dates=["Datetime"],
                index_col="Datetime",
            )
            if not df.empty:
                use_large = True
                if interval == "1d":
                    # If the requested end date is in the past (i.e., historical backtest / optimization),
                    # we should NOT force-refresh just because the cache isn't up-to-today.
                    # As long as the cache covers the requested window, trust it.
                    try:
                        end_dt_req = pd.to_datetime(end)
                        latest_dt_cache = pd.to_datetime(df.index.max())
                        if end_dt_req <= latest_dt_cache:
                            start_dt_req = pd.to_datetime(start)
                            df_filtered = df.loc[(df.index >= start_dt_req) & (df.index <= end_dt_req)]
                            if not df_filtered.empty:
                                if ARGS_DEBUG:
                                    print(
                                        f"[data] Using large cache for {symbol} (historical window): "
                                        f"{len(df_filtered)} rows from {large_cache_path}"
                                    )
                                return df_filtered
                    except Exception:
                        # Fall back to staleness logic below if parsing fails.
                        pass

                    latest_dt = None
                    try:
                        latest_dt = pd.to_datetime(df.index.max())
                        today = pd.Timestamp.today().normalize()
                        latest_norm = pd.Timestamp(latest_dt).normalize()
                        age_days = (today - latest_norm).days

                        if age_days > 7:
                            if ARGS_DEBUG:
                                print(
                                    f"[data] Large cache for {symbol} is stale ({age_days} days since last bar {latest_dt.date()}); "
                                    f"will try to extend from local caches or incremental fetch…"
                                )
                            extended = False

                            # 1) If a fresh short-term CSV cache exists, sync large cache from it (no network).
                            if os.path.exists(csv_path) and os.path.exists(meta_path):
                                try:
                                    with open(meta_path, "r") as f:
                                        ts_str = f.read().strip()
                                    cached_at = datetime.fromisoformat(ts_str)
                                    age_hours = (datetime.now() - cached_at).total_seconds() / 3600.0
                                    if age_hours <= max_age_hours:
                                        df_short = pd.read_csv(
                                            csv_path, parse_dates=["Datetime"], index_col="Datetime"
                                        )
                                        if not df_short.empty:
                                            short_latest = pd.to_datetime(df_short.index.max())
                                            if short_latest > latest_dt:
                                                new_rows = df_short[df_short.index > latest_dt]
                                                merged = pd.concat([df, new_rows]).sort_index()
                                                merged = merged[~merged.index.duplicated(keep="last")]
                                                try:
                                                    with gzip.open(large_cache_path, "wt") as gz:
                                                        merged.to_csv(gz)
                                                    if ARGS_DEBUG:
                                                        print(
                                                            f"[data] Extended large cache for {symbol} from short-term CSV: "
                                                            f"{len(df)}→{len(merged)} rows (last={short_latest.date()})"
                                                        )
                                                except Exception as e2:
                                                    if ARGS_DEBUG:
                                                        print(f"[data] Failed to overwrite large cache for {symbol}: {e2}")
                                                df = merged
                                                latest_dt = short_latest
                                                extended = True
                                except Exception as e:
                                    if ARGS_DEBUG:
                                        print(f"[data] Short-term cache sync failed for {symbol}: {e}")

                            # 2) If still stale, fetch only the missing tail via yfinance.
                            if not extended and latest_dt is not None:
                                try:
                                    tail_start = (latest_dt + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
                                    if ARGS_DEBUG:
                                        print(
                                            f"[data] Fetching incremental tail for {symbol} from {tail_start} to {end} via yfinance…"
                                        )
                                    history_tail = yf.Ticker(symbol).history(
                                        start=tail_start, end=end, interval=interval, auto_adjust=False
                                    )
                                    if history_tail is None or history_tail.empty:
                                        history_tail = yf.download(
                                            symbol,
                                            start=tail_start,
                                            end=end,
                                            interval=interval,
                                            auto_adjust=False,
                                            progress=False,
                                            threads=False,
                                        )
                                    if history_tail is not None and not history_tail.empty:
                                        tail_df = history_tail.rename(
                                            columns={
                                                "Open": "Open",
                                                "High": "High",
                                                "Low": "Low",
                                                "Close": "Close",
                                                "Volume": "Volume",
                                            }
                                        ).copy()
                                        tail_df.index.name = "Datetime"
                                        tail_df = tail_df[tail_df.index > latest_dt]
                                        if not tail_df.empty:
                                            merged = pd.concat([df, tail_df]).sort_index()
                                            merged = merged[~merged.index.duplicated(keep="last")]
                                            try:
                                                with gzip.open(large_cache_path, "wt") as gz:
                                                    merged.to_csv(gz)
                                                if ARGS_DEBUG:
                                                    print(
                                                        f"[data] Extended large cache for {symbol} with {len(tail_df)} new rows "
                                                        f"(last={merged.index.max().date()})"
                                                    )
                                            except Exception as e2:
                                                if ARGS_DEBUG:
                                                    print(f"[data] Failed to overwrite large cache for {symbol}: {e2}")
                                            df = merged
                                            latest_dt = pd.to_datetime(df.index.max())
                                            extended = True
                                except Exception as e:
                                    if ARGS_DEBUG:
                                        print(f"[data] Incremental tail fetch failed for {symbol}: {e}")

                            # Recompute age_days after any extension attempt
                            try:
                                today = pd.Timestamp.today().normalize()
                                latest_norm = pd.Timestamp(latest_dt).normalize()
                                age_days = (today - latest_norm).days
                            except Exception:
                                age_days = 9999

                            if age_days > 7:
                                use_large = False
                                if ARGS_DEBUG:
                                    print(
                                        f"[data] Large cache for {symbol} remains stale after extension attempts "
                                        f"(last={latest_dt.date()}, {age_days} days old); will refresh via Stooq/yfinance…"
                                    )
                    except Exception as e:
                        if ARGS_DEBUG:
                            print(f"[data] Failed to inspect large cache for {symbol}: {e}")
                        use_large = False

                if use_large:
                    start_dt = pd.to_datetime(start)
                    end_dt = pd.to_datetime(end)
                    df_filtered = df.loc[(df.index >= start_dt) & (df.index <= end_dt)]
                    if not df_filtered.empty:
                        if ARGS_DEBUG:
                            print(
                                f"[data] Using large cache for {symbol}: {len(df_filtered)} rows from {large_cache_path}"
                            )
                        return df_filtered
        except Exception as e:
            if ARGS_DEBUG:
                print(f"[data] Failed to load large cache for {symbol}: {e}")

    # Try short-term CSV cache (prioritize very recent downloads). If we fetched
    # data within the last `max_age_hours`, we will reuse it regardless of how old
    # the last bar is, but emit a warning if the underlying data is very old.
    if os.path.exists(csv_path) and os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                ts_str = f.read().strip()
            cached_at = datetime.fromisoformat(ts_str)
            df = pd.read_csv(csv_path, parse_dates=["Datetime"], index_col="Datetime")
            if not df.empty:
                if interval == "1d":
                    try:
                        latest_dt = pd.to_datetime(df.index.max())
                        today = pd.Timestamp.today().normalize()
                        latest_norm = pd.Timestamp(latest_dt).normalize()
                        age_days = (today - latest_norm).days
                        age_hours = (datetime.now() - cached_at).total_seconds() / 3600.0

                        # If we fetched within the freshness window, always reuse,
                        # regardless of how old the last bar is. Warn if the data itself is old.
                        if age_hours <= max_age_hours:
                            if ARGS_DEBUG:
                                if age_days > 7:
                                    print(
                                        f"[data] WARNING: Using short-term daily cache for {symbol} "
                                        f"with old data (last bar={latest_dt.date()}, {age_days} days ago; "
                                        f"cache written {age_hours:.1f}h ago)."
                                    )
                                else:
                                    print(
                                        f"[data] Using short-term daily cache for {symbol}: "
                                        f"{len(df)} rows (last={latest_dt.date()}, cached {age_hours:.1f}h ago)"
                                    )
                            return df

                        # Otherwise, if the underlying data is very old, force refresh; else fall through.
                        if age_days > 7 and ARGS_DEBUG:
                            print(
                                f"[data] Cached daily data for {symbol} is stale (last={latest_dt.date()}, "
                                f"{age_days} days old); fetching fresh…"
                            )
                        # fall through to fresh fetch
                    except Exception:
                        # If staleness check fails, still use cache if it was written recently
                        if (datetime.now() - cached_at).total_seconds() <= max_age_hours * 3600:
                            if ARGS_DEBUG:
                                print(f"[data] Using short-term daily cache for {symbol} (staleness check failed)")
                            return df
                else:
                    age_hours = (datetime.now() - cached_at).total_seconds() / 3600.0
                    if age_hours <= max_age_hours:
                        if ARGS_DEBUG:
                            print(
                                f"[data] Using short-term intraday cache for {symbol}: "
                                f"{len(df)} rows (cached {age_hours:.1f}h ago)"
                            )
                        return df
        except Exception:
            pass

    # Fetch fresh - PRIORITIZE STOOQ FOR DAILY DATA (yfinance has been unreliable)
    history = None
    
    # For daily data, try Stooq FIRST
    if interval == "1d":
        def _try_stooq(sym: str) -> pd.DataFrame | None:
            url = f"https://stooq.com/q/d/l/?s={sym}&i=d"
            try:
                resp = requests.get(url, timeout=10)
                if resp.ok and resp.text and resp.text.strip():
                    df = pd.read_csv(StringIO(resp.text))
                    if not df.empty and {"Date","Open","High","Low","Close","Volume"}.issubset(df.columns):
                        df["Datetime"] = pd.to_datetime(df["Date"])
                        df = df.set_index("Datetime").sort_index()
                        df.index.name = "Datetime"
                        out = df[["Open","High","Low","Close","Volume"]].copy()
                        return out.loc[(out.index >= pd.to_datetime(start)) & (out.index <= pd.to_datetime(end))]
            except Exception:
                return None
            return None
        
        base = symbol.lower()
        candidates = [base, f"{base}.us"]
        for c in candidates:
            st = _try_stooq(c)
            if st is not None and not st.empty:
                latest_dt = pd.to_datetime(st.index.max())
                is_stale = False
                try:
                    today = pd.Timestamp.today().normalize()
                    latest_norm = pd.Timestamp(latest_dt).normalize()
                    is_stale = (today - latest_norm).days >= 3
                except Exception:
                    is_stale = False
                if not is_stale:
                    if ARGS_DEBUG:
                        print(f"[data] Using Stooq for {symbol} (latest: {latest_dt.date()})")
                    history = st
                    break
                else:
                    if ARGS_DEBUG:
                        print(f"[data] Stooq data for {symbol} appears stale (last={latest_dt.date()}); will try yfinance")
    
    # If Stooq failed or not daily interval, try yfinance
    if history is None or history.empty:
        try:
            if ARGS_DEBUG:
                print(f"[data] Fetching {symbol} from yfinance...")
            history = yf.Ticker(symbol).history(start=start, end=end, interval=interval, auto_adjust=False)
        except Exception as e:
            if ARGS_DEBUG:
                print(f"[data] yfinance Ticker failed for {symbol}: {e}")
            history = None
        
        if history is None or history.empty:
            # Fallback to download API
            try:
                if ARGS_DEBUG:
                    print(f"[data] Trying yfinance download API for {symbol}...")
                dl = yf.download(symbol, start=start, end=end, interval=interval, auto_adjust=False, progress=False, threads=False)
                if dl is not None and not dl.empty:
                    history = dl
            except Exception as e:
                if ARGS_DEBUG:
                    print(f"[data] yfinance download failed for {symbol}: {e}")
        
        if history is None or history.empty:
            raise RuntimeError(f"No data for {symbol}")

    # Normalize column names
    df = history.rename(columns={
        "Open": "Open", "High": "High", "Low": "Low", "Close": "Close", "Volume": "Volume"
    }).copy()
    df.index.name = "Datetime"

    # Save cache
    try:
        df.to_csv(csv_path)
        with open(meta_path, "w") as f:
            f.write(datetime.now().isoformat())
    except Exception:
        pass

    return df


# ----------------------------
# Indicator helpers (no TA-Lib)
# ----------------------------
def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    out = 100 - (100 / (1 + rs))
    return out.fillna(50)


def stochastic_rsi(close: pd.Series, rsi_period: int = 14, stoch_period: int = 14, k_period: int = 3, d_period: int = 3) -> pd.Series:
    """
    Calculate Stochastic RSI (StochRSI).
    
    StochRSI = (RSI - RSI_min) / (RSI_max - RSI_min)
    Where RSI_min and RSI_max are the minimum and maximum RSI values over the stoch_period.
    
    Args:
        close: Price series
        rsi_period: Period for RSI calculation
        stoch_period: Period for Stochastic calculation over RSI
        k_period: Smoothing period for %K
        d_period: Smoothing period for %D
    
    Returns:
        StochRSI %K values (0-100 scale)
    """
    # Calculate RSI first
    rsi_values = rsi(close, rsi_period)
    
    # Calculate Stochastic over RSI
    rsi_min = rsi_values.rolling(stoch_period).min()
    rsi_max = rsi_values.rolling(stoch_period).max()
    
    # Avoid division by zero
    rsi_range = rsi_max - rsi_min
    rsi_range = rsi_range.replace(0, 1)  # Replace 0 with 1 to avoid division by zero
    
    # StochRSI %K
    stoch_rsi_k = 100 * (rsi_values - rsi_min) / rsi_range
    
    # Smooth %K
    stoch_rsi_k = stoch_rsi_k.rolling(k_period).mean()
    
    return stoch_rsi_k.fillna(50)  # Fill NaN with neutral value


def macd(close: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.Series:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    MACD = EMA(fast) - EMA(slow)
    Signal = EMA(MACD, signal_period)
    Histogram = MACD - Signal
    
    Args:
        close: Price series
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line EMA period (default 9)
    
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    # Calculate EMAs
    ema_fast = ema(close, fast_period)
    ema_slow = ema(close, slow_period)
    
    # MACD line
    macd_line = ema_fast - ema_slow
    
    # Signal line (EMA of MACD)
    signal_line = ema(macd_line, signal_period)
    
    # Histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Williams %R.
    
    Williams %R = (Highest High - Close) / (Highest High - Lowest Low) * -100
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: Lookback period (default 14)
    
    Returns:
        Williams %R values (-100 to 0 scale)
    """
    # Calculate highest high and lowest low over the period
    highest_high = high.rolling(period).max()
    lowest_low = low.rolling(period).min()
    
    # Calculate Williams %R
    williams_r = ((highest_high - close) / (highest_high - lowest_low)) * -100
    
    return williams_r.fillna(-50)  # Fill NaN with neutral value


def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Commodity Channel Index (CCI).
    
    CCI measures the current price level relative to the average price level over a given period.
    Values above +100 indicate overbought conditions, values below -100 indicate oversold conditions.
    
    Args:
        high: High price series
        low: Low price series  
        close: Close price series
        period: Lookback period (default 20)
    
    Returns:
        CCI values (typically -200 to +200 range)
    """
    # Calculate Typical Price (TP)
    tp = (high + low + close) / 3
    
    # Calculate Simple Moving Average of TP
    tp_sma = tp.rolling(period).mean()
    
    # Calculate Mean Deviation
    mean_deviation = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    
    # Calculate CCI
    cci = (tp - tp_sma) / (0.015 * mean_deviation)
    
    return cci.fillna(0)  # Fill NaN with neutral value


def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Money Flow Index (MFI).
    
    MFI is a volume-weighted momentum oscillator that measures the strength of money flowing
    in and out of a security. It's often called the "volume-weighted RSI" because it's similar
    to RSI but incorporates volume data.
    
    Values above 80 indicate overbought conditions, values below 20 indicate oversold conditions.
    
    Args:
        high: High price series
        low: Low price series  
        close: Close price series
        volume: Volume series
        period: Lookback period (default 14)
    
    Returns:
        MFI values (0 to 100 scale)
    """
    # Calculate Typical Price
    tp = (high + low + close) / 3
    
    # Calculate Raw Money Flow
    raw_money_flow = tp * volume
    
    # Determine positive and negative money flow
    tp_diff = tp.diff()
    
    # Positive money flow (when typical price increases)
    positive_flow = raw_money_flow.where(tp_diff > 0, 0)
    positive_flow_sum = positive_flow.rolling(period).sum()
    
    # Negative money flow (when typical price decreases)
    negative_flow = raw_money_flow.where(tp_diff < 0, 0)
    negative_flow_sum = negative_flow.rolling(period).sum()
    
    # Calculate Money Flow Ratio
    money_flow_ratio = positive_flow_sum / negative_flow_sum
    
    # Calculate MFI
    mfi = 100 - (100 / (1 + money_flow_ratio))
    
    return mfi.fillna(50)  # Fill NaN with neutral value


def parabolic_sar(high: pd.Series, low: pd.Series, close: pd.Series, acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
    """
    Calculate Parabolic SAR (Stop and Reverse).
    
    PSAR is a trend-following indicator that provides dynamic stop-loss levels and trend direction.
    When PSAR is below price, trend is up (buy signal). When PSAR is above price, trend is down (sell signal).
    
    Args:
        high: High price series
        low: Low price series  
        close: Close price series
        acceleration: Acceleration factor (default 0.02)
        maximum: Maximum acceleration factor (default 0.2)
    
    Returns:
        PSAR values (trend-following stop levels)
    """
    psar = pd.Series(index=close.index, dtype=float)
    trend = pd.Series(index=close.index, dtype=int)  # 1 for uptrend, -1 for downtrend
    af = pd.Series(index=close.index, dtype=float)  # Acceleration factor
    ep = pd.Series(index=close.index, dtype=float)  # Extreme point
    
    # Initialize first values
    psar.iloc[0] = low.iloc[0]
    trend.iloc[0] = 1
    af.iloc[0] = acceleration
    ep.iloc[0] = high.iloc[0]
    
    for i in range(1, len(close)):
        # Calculate PSAR for current period
        psar.iloc[i] = psar.iloc[i-1] + af.iloc[i-1] * (ep.iloc[i-1] - psar.iloc[i-1])
        
        # Check for trend reversal
        if trend.iloc[i-1] == 1:  # Previous trend was up
            if low.iloc[i] <= psar.iloc[i]:  # Reversal to downtrend
                trend.iloc[i] = -1
                psar.iloc[i] = ep.iloc[i-1]  # Start from previous extreme point
                af.iloc[i] = acceleration
                ep.iloc[i] = low.iloc[i]
            else:  # Continue uptrend
                trend.iloc[i] = 1
                af.iloc[i] = af.iloc[i-1]
                if high.iloc[i] > ep.iloc[i-1]:  # New extreme point
                    ep.iloc[i] = high.iloc[i]
                    af.iloc[i] = min(af.iloc[i] + acceleration, maximum)
                else:
                    ep.iloc[i] = ep.iloc[i-1]
        else:  # Previous trend was down
            if high.iloc[i] >= psar.iloc[i]:  # Reversal to uptrend
                trend.iloc[i] = 1
                psar.iloc[i] = ep.iloc[i-1]  # Start from previous extreme point
                af.iloc[i] = acceleration
                ep.iloc[i] = high.iloc[i]
            else:  # Continue downtrend
                trend.iloc[i] = -1
                af.iloc[i] = af.iloc[i-1]
                if low.iloc[i] < ep.iloc[i-1]:  # New extreme point
                    ep.iloc[i] = low.iloc[i]
                    af.iloc[i] = min(af.iloc[i] + acceleration, maximum)
                else:
                    ep.iloc[i] = ep.iloc[i-1]
    
    return psar.ffill()


def roc(close: pd.Series, period: int = 12) -> pd.Series:
    """
    Calculate Rate of Change (ROC).
    
    ROC measures the percentage change in price over a specified period.
    Positive values indicate upward momentum, negative values indicate downward momentum.
    
    Args:
        close: Close price series
        period: Lookback period (default 12)
    
    Returns:
        ROC values as percentage change
    """
    # Calculate ROC: ((Current - Previous) / Previous) * 100
    roc = ((close - close.shift(period)) / close.shift(period)) * 100
    
    return roc.fillna(0)  # Fill NaN with neutral value


def kalman_ma(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    base_q: float = 0.0001,
    base_r: float = 0.01,
    use_adapt: bool = True,
    atr_len: int = 14,
    std_len: int = 20,
    vol_blend: float = 0.5,
    q_scale: float = 2.0,
    r_scale: float = 2.0,
    vol_floor: float = 0.0005,
) -> pd.Series:
    """
    Calculate Kalman Moving Average (Kalman MA).
    
    A 1D Kalman filter used as a moving average alternative.
    It can respond faster than an EMA for similar smoothness, with tunable process/measurement noise.
    
    Args:
        close: Close price series
        high: High price series (for ATR calculation)
        low: Low price series (for ATR calculation)
        base_q: Base process noise (Q) - Higher Q = more reactive (shorter EMA-like)
        base_r: Base measurement noise (R) - Higher R = more smoothing (longer EMA-like)
        use_adapt: Enable volatility-adaptive tuning
        atr_len: ATR length for volatility calculation
        std_len: StdDev length for volatility calculation
        vol_blend: Blend ATR vs StdDev (0=ATR only, 1=StdDev only)
        q_scale: Q scale multiplier at high volatility
        r_scale: R scale multiplier at low volatility
        vol_floor: Volatility floor to avoid division by zero
    
    Returns:
        Kalman MA values
    """
    result = pd.Series(index=close.index, dtype=float)
    
    # Initialize Kalman filter state
    kalman_estimate = None
    kalman_error = None
    
    # Calculate ATR for volatility (if needed)
    atr_series = None
    if use_adapt:
        # Calculate True Range
        tr1 = (high - low).abs()
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        # ATR is the rolling mean of TR
        atr_series = tr.rolling(window=atr_len, min_periods=1).mean()
    
    # Iterate through the series to maintain state
    for i in range(len(close)):
        src = close.iloc[i]
        
        # Initialize on first bar
        if kalman_estimate is None or pd.isna(kalman_estimate):
            kalman_estimate = src
            kalman_error = 1.0
            result.iloc[i] = kalman_estimate
            continue
        
        # Volatility-adaptive tuning
        if use_adapt and atr_series is not None and i >= max(atr_len, std_len):
            atr_val = atr_series.iloc[i]
            std_val = close.iloc[max(0, i - std_len + 1):i + 1].std()
            
            # Avoid division by zero
            src_abs = max(abs(src), vol_floor)
            atr_ratio = atr_val / src_abs if src_abs > 0 else 0
            std_ratio = std_val / src_abs if src_abs > 0 else 0
            
            # Blend ATR and StdDev
            vol_mix = vol_blend * std_ratio + (1 - vol_blend) * atr_ratio
            
            # Adaptive Q/R
            q_eff = base_q * (1 + q_scale * vol_mix)
            r_eff = base_r * (1 + r_scale * (1 - min(vol_mix, 1.0)))
        else:
            q_eff = base_q
            r_eff = base_r
        
        # Predict step
        pred_estimate = kalman_estimate
        pred_error = kalman_error + q_eff
        
        # Update step
        kalman_gain = pred_error / (pred_error + r_eff) if (pred_error + r_eff) > 0 else 0
        kalman_estimate = pred_estimate + kalman_gain * (src - pred_estimate)
        kalman_error = (1.0 - kalman_gain) * pred_error
        
        result.iloc[i] = kalman_estimate
    
    return result


def fetch_vix_data(start: str, end: str, interval: str = "1d") -> pd.Series:
    """
    Fetch VIX (Volatility Index) data and return as a Series.
    
    VIX measures market volatility expectations. Rising VIX indicates fear/uncertainty,
    falling VIX indicates complacency/confidence.
    
    Args:
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        interval: Data interval (default "1d" for daily)
    
    Returns:
        Series with VIX close prices, indexed by datetime
    """
    try:
        # VIX ticker symbol
        vix_symbol = "^VIX"
        
        # Fetch VIX data using yfinance
        vix_ticker = yf.Ticker(vix_symbol)
        vix_data = vix_ticker.history(start=start, end=end, interval=interval, auto_adjust=False)
        
        if vix_data is None or vix_data.empty:
            # Fallback to download API
            vix_data = yf.download(vix_symbol, start=start, end=end, interval=interval, 
                                  auto_adjust=False, progress=False, threads=False)
        
        if vix_data is None or vix_data.empty:
            # Return empty series if fetch fails
            return pd.Series(dtype=float)
        
        # Return Close prices as Series
        if "Close" in vix_data.columns:
            return vix_data["Close"].copy()
        else:
            # Handle MultiIndex columns
            if isinstance(vix_data.columns, pd.MultiIndex):
                vix_data.columns = vix_data.columns.droplevel(1)
            if "Close" in vix_data.columns:
                return vix_data["Close"].copy()
        
        return pd.Series(dtype=float)
    except Exception as e:
        if ARGS_DEBUG:
            print(f"[VIX] Error fetching VIX data: {e}")
        return pd.Series(dtype=float)


def keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20, multiplier: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Keltner Channels.
    
    Keltner Channels are volatility-based indicators that use ATR instead of standard deviation.
    They consist of three lines: upper channel, middle channel (EMA), and lower channel.
    
    Upper Channel = EMA + (ATR × multiplier)
    Middle Channel = EMA
    Lower Channel = EMA - (ATR × multiplier)
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: EMA and ATR period (default 20)
        multiplier: ATR multiplier (default 2.0)
    
    Returns:
        Tuple of (upper_channel, middle_channel, lower_channel)
    """
    # Calculate EMA (middle channel)
    middle_channel = ema(close, period)
    
    # Calculate ATR
    tr = true_range(high, low, close)
    atr = tr.rolling(period).mean()
    
    # Calculate upper and lower channels
    upper_channel = middle_channel + (atr * multiplier)
    lower_channel = middle_channel - (atr * multiplier)
    
    return upper_channel, middle_channel, lower_channel


def on_balance_volume(close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate On-Balance Volume (OBV).
    
    OBV is a cumulative volume indicator that adds volume on up days and subtracts
    volume on down days. It shows the flow of volume and can be used to detect
    divergences between price and volume.
    
    OBV = Previous OBV + (Volume if Close > Previous Close else -Volume if Close < Previous Close else 0)
    
    Args:
        close: Close price series
        volume: Volume series
        period: Smoothing period for OBV (default 14)
    
    Returns:
        Smoothed OBV series
    """
    # Calculate price change direction
    price_change = close.diff()
    
    # Calculate OBV: add volume on up days, subtract on down days
    obv = pd.Series(0.0, index=close.index)
    obv.iloc[0] = volume.iloc[0]  # Initialize with first volume
    
    for i in range(1, len(close)):
        if price_change.iloc[i] > 0:  # Up day
            obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
        elif price_change.iloc[i] < 0:  # Down day
            obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
        else:  # No change
            obv.iloc[i] = obv.iloc[i-1]
    
    # Smooth the OBV with EMA
    obv_smoothed = obv.ewm(span=period).mean()
    
    return obv_smoothed


def ichimoku_cloud(high: pd.Series, low: pd.Series, close: pd.Series, tenkan_period: int = 9, kijun_period: int = 26, senkou_b_period: int = 52, displacement: int = 26) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Calculate Ichimoku Cloud components.
    
    Ichimoku Cloud is a comprehensive trend analysis system with 5 main components:
    - Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
    - Kijun-sen (Base Line): (26-period high + 26-period low) / 2
    - Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, shifted 26 periods forward
    - Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, shifted 26 periods forward
    - Chikou Span (Lagging Span): Current Close, shifted 26 periods backward
    
    The cloud (Kumo) is formed by Senkou Span A and B, providing dynamic support/resistance.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        tenkan_period: Tenkan-sen period (default 9)
        kijun_period: Kijun-sen period (default 26)
        senkou_b_period: Senkou Span B period (default 52)
        displacement: Forward/backward shift periods (default 26)
    
    Returns:
        Tuple of (tenkan, kijun, senkou_a, senkou_b, chikou, cloud_upper, cloud_lower)
    """
    # Tenkan-sen (Conversion Line)
    tenkan_high = high.rolling(tenkan_period).max()
    tenkan_low = low.rolling(tenkan_period).min()
    tenkan = (tenkan_high + tenkan_low) / 2
    
    # Kijun-sen (Base Line)
    kijun_high = high.rolling(kijun_period).max()
    kijun_low = low.rolling(kijun_period).min()
    kijun = (kijun_high + kijun_low) / 2
    
    # Senkou Span A (Leading Span A)
    senkou_a = (tenkan + kijun) / 2
    senkou_a = senkou_a.shift(displacement)  # Shift forward
    
    # Senkou Span B (Leading Span B)
    senkou_b_high = high.rolling(senkou_b_period).max()
    senkou_b_low = low.rolling(senkou_b_period).min()
    senkou_b = (senkou_b_high + senkou_b_low) / 2
    senkou_b = senkou_b.shift(displacement)  # Shift forward
    
    # Chikou Span (Lagging Span)
    chikou = close.shift(-displacement)  # Shift backward
    
    # Cloud (Kumo) - upper and lower boundaries
    cloud_upper = pd.concat([senkou_a, senkou_b], axis=1).max(axis=1)
    cloud_lower = pd.concat([senkou_a, senkou_b], axis=1).min(axis=1)
    
    return tenkan, kijun, senkou_a, senkou_b, chikou, cloud_upper, cloud_lower


def supertrend(df: pd.DataFrame, atr_period: int = 10, multiplier: float = 3.0) -> tuple[pd.Series, pd.Series]:
    """
    Compute SuperTrend line and direction.

    Returns:
        (st_line, st_dir) where st_dir is +1 for bullish, -1 for bearish
    """
    high = df["High"].copy()
    low = df["Low"].copy()
    close = df["Close"].copy()

    tr = true_range(high, low, close)
    atr_series = tr.rolling(atr_period).mean()

    hl2 = (high + low) / 2.0
    upper_basic = hl2 + multiplier * atr_series
    lower_basic = hl2 - multiplier * atr_series

    upper_band = upper_basic.copy()
    lower_band = lower_basic.copy()

    for i in range(1, len(close)):
        if not pd.isna(upper_band.iloc[i-1]) and not pd.isna(close.iloc[i-1]):
            upper_band.iloc[i] = min(upper_basic.iloc[i], upper_band.iloc[i-1]) if close.iloc[i-1] <= upper_band.iloc[i-1] else upper_basic.iloc[i]
        if not pd.isna(lower_band.iloc[i-1]) and not pd.isna(close.iloc[i-1]):
            lower_band.iloc[i] = max(lower_basic.iloc[i], lower_band.iloc[i-1]) if close.iloc[i-1] >= lower_band.iloc[i-1] else lower_basic.iloc[i]

    st_line = pd.Series(index=close.index, dtype=float)
    st_dir = pd.Series(index=close.index, dtype=float)

    # Initialize
    st_line.iloc[0] = np.nan
    st_dir.iloc[0] = 1

    for i in range(1, len(close)):
        prev_st = st_line.iloc[i-1]
        prev_dir = st_dir.iloc[i-1]
        if prev_dir == 1:
            st_line.iloc[i] = lower_band.iloc[i]
            st_dir.iloc[i] = 1 if close.iloc[i] > lower_band.iloc[i] else -1
        else:
            st_line.iloc[i] = upper_band.iloc[i]
            st_dir.iloc[i] = -1 if close.iloc[i] < upper_band.iloc[i] else 1

        # Flip logic
        if prev_dir == -1 and close.iloc[i] > upper_band.iloc[i]:
            st_dir.iloc[i] = 1
            st_line.iloc[i] = lower_band.iloc[i]
        elif prev_dir == 1 and close.iloc[i] < lower_band.iloc[i]:
            st_dir.iloc[i] = -1
            st_line.iloc[i] = upper_band.iloc[i]

    return st_line, st_dir


def volume_profile(df: pd.DataFrame, lookback: int = 20, volume_threshold: float = 1.5) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Compute Volume Profile indicators.
    
    Volume Profile analyzes volume distribution at different price levels to identify:
    - High Volume Nodes (HVN): Price levels with high volume (support/resistance)
    - Low Volume Nodes (LVN): Price levels with low volume (breakout zones)
    - Volume Weighted Average Price (VWAP) deviation
    - Volume trend analysis
    
    Args:
        df: DataFrame with OHLCV data
        lookback: Period for volume profile calculation
        volume_threshold: Multiplier for identifying high volume nodes
        
    Returns:
        (hvn_strength, lvn_strength, vwap_deviation, volume_trend)
    """
    high = df["High"].copy()
    low = df["Low"].copy()
    close = df["Close"].copy()
    volume = df["Volume"].copy()
    
    # Calculate VWAP
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).rolling(lookback).sum() / volume.rolling(lookback).sum()
    
    # Volume Profile: Analyze volume distribution at price levels
    hvn_strength = pd.Series(index=df.index, dtype=float)
    lvn_strength = pd.Series(index=df.index, dtype=float)
    vwap_deviation = pd.Series(index=df.index, dtype=float)
    volume_trend = pd.Series(index=df.index, dtype=float)
    
    for i in range(lookback, len(df)):
        # Get recent price and volume data
        recent_high = high.iloc[i-lookback+1:i+1]
        recent_low = low.iloc[i-lookback+1:i+1]
        recent_close = close.iloc[i-lookback+1:i+1]
        recent_volume = volume.iloc[i-lookback+1:i+1]
        
        # Create price levels (simplified approach)
        price_range = recent_high.max() - recent_low.min()
        if price_range > 0:
            # Divide price range into bins
            num_bins = min(20, lookback)  # Limit bins for performance
            bin_size = price_range / num_bins
            price_bins = [recent_low.min() + j * bin_size for j in range(num_bins + 1)]
            
            # Calculate volume at each price level
            volume_at_price = []
            for j in range(num_bins):
                bin_low = price_bins[j]
                bin_high = price_bins[j + 1]
                
                # Find bars where price was in this range
                in_range = ((recent_high >= bin_low) & (recent_low <= bin_high))
                bin_volume = recent_volume[in_range].sum()
                volume_at_price.append(bin_volume)
            
            if volume_at_price:
                # Calculate HVN and LVN strength
                avg_volume = sum(volume_at_price) / len(volume_at_price)
                max_volume = max(volume_at_price)
                
                # HVN: High volume nodes (support/resistance)
                hvn_count = sum(1 for vol in volume_at_price if vol > avg_volume * volume_threshold)
                hvn_strength.iloc[i] = hvn_count / len(volume_at_price)
                
                # LVN: Low volume nodes (breakout zones)
                lvn_count = sum(1 for vol in volume_at_price if vol < avg_volume * 0.5)
                lvn_strength.iloc[i] = lvn_count / len(volume_at_price)
                
                # VWAP deviation
                current_price = close.iloc[i]
                current_vwap = vwap.iloc[i]
                if current_vwap > 0:
                    vwap_deviation.iloc[i] = (current_price - current_vwap) / current_vwap
                
                # Volume trend (comparing recent vs older volume)
                if len(recent_volume) >= 10:
                    recent_vol_avg = recent_volume.iloc[-5:].mean()
                    older_vol_avg = recent_volume.iloc[-10:-5].mean()
                    if older_vol_avg > 0:
                        volume_trend.iloc[i] = (recent_vol_avg - older_vol_avg) / older_vol_avg
    
    return hvn_strength, lvn_strength, vwap_deviation, volume_trend


def volume_rate_of_change(volume: pd.Series, period: int = 10) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Compute Volume Rate of Change (VROC) indicators.
    
    VROC measures the percentage change in volume over a specified period, providing
    insights into volume momentum and acceleration/deceleration patterns.
    
    Args:
        volume: Volume series
        period: Period for VROC calculation
        
    Returns:
        (vroc, vroc_sma, vroc_momentum) where:
        - vroc: Raw VROC percentage
        - vroc_sma: Smoothed VROC using SMA
        - vroc_momentum: VROC momentum (rate of change of VROC)
    """
    # Calculate VROC as percentage change in volume
    vroc = ((volume - volume.shift(period)) / volume.shift(period)) * 100
    
    # Smooth VROC with SMA to reduce noise
    vroc_sma = vroc.rolling(window=5).mean()
    
    # Calculate VROC momentum (rate of change of VROC itself)
    vroc_momentum = vroc - vroc.shift(1)
    
    return vroc, vroc_sma, vroc_momentum


def rsi_divergence(close: pd.Series, rsi: pd.Series, lookback: int = 20, min_swings: int = 2, 
                  min_change: float = 0.02, persistence_bars: int = 3) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Compute RSI Divergence indicators with improved reliability.
    
    RSI Divergence detects when price and RSI are moving in opposite directions,
    which often signals potential trend reversals. This includes both regular
    and hidden divergences.
    
    IMPROVEMENTS:
    - Uses only close prices to eliminate repainting
    - Requires minimum price change for swing significance
    - Adds signal persistence to prevent flickering
    - More robust peak/trough detection
    
    Args:
        close: Price series (close prices only to avoid repainting)
        rsi: RSI series
        lookback: Period for divergence analysis
        min_swings: Minimum number of swings required for divergence
        min_change: Minimum price change required for significant swing (2% default)
        persistence_bars: Number of bars signal must persist before confirming
        
    Returns:
        (bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div) where:
        - bullish_div: Regular bullish divergence (price lower low, RSI higher low)
        - bearish_div: Regular bearish divergence (price higher high, RSI lower high)
        - hidden_bullish_div: Hidden bullish divergence (price higher low, RSI lower low)
        - hidden_bearish_div: Hidden bearish divergence (price lower high, RSI higher high)
    """
    bullish_div = pd.Series(False, index=close.index)
    bearish_div = pd.Series(False, index=close.index)
    hidden_bullish_div = pd.Series(False, index=close.index)
    hidden_bearish_div = pd.Series(False, index=close.index)
    
    # Signal persistence tracking
    bullish_persistence = pd.Series(0, index=close.index)
    bearish_persistence = pd.Series(0, index=close.index)
    hidden_bullish_persistence = pd.Series(0, index=close.index)
    hidden_bearish_persistence = pd.Series(0, index=close.index)
    
    def find_significant_swings(series: pd.Series, min_change: float) -> list:
        """Find significant swings with minimum change requirement."""
        swings = []
        for j in range(2, len(series) - 2):  # Need more context for significance
            # Check for peaks (local maxima with significance)
            if (series.iloc[j] > series.iloc[j-1] and 
                series.iloc[j] > series.iloc[j+1] and
                series.iloc[j] > series.iloc[j-2] and 
                series.iloc[j] > series.iloc[j+2]):
                
                # Check if this peak represents significant change
                if j >= 2:
                    prev_val = series.iloc[j-2]
                    change_pct = abs(series.iloc[j] - prev_val) / prev_val if prev_val != 0 else 0
                    if change_pct >= min_change:
                        swings.append((j, series.iloc[j]))
            
            # Check for troughs (local minima with significance)
            if (series.iloc[j] < series.iloc[j-1] and 
                series.iloc[j] < series.iloc[j+1] and
                series.iloc[j] < series.iloc[j-2] and 
                series.iloc[j] < series.iloc[j+2]):
                
                # Check if this trough represents significant change
                if j >= 2:
                    prev_val = series.iloc[j-2]
                    change_pct = abs(series.iloc[j] - prev_val) / prev_val if prev_val != 0 else 0
                    if change_pct >= min_change:
                        swings.append((j, series.iloc[j]))
        
        return swings
    
    for i in range(lookback + persistence_bars, len(close)):
        # Get recent data for analysis (use close prices only)
        recent_close = close.iloc[i-lookback+1:i+1]
        recent_rsi = rsi.iloc[i-lookback+1:i+1]
        
        # Find significant swings using close prices only
        price_swings = find_significant_swings(recent_close, min_change)
        rsi_swings = find_significant_swings(recent_rsi, min_change * 0.1)  # Lower threshold for RSI
        
        # Separate peaks and troughs
        price_peaks = [(j, val) for j, val in price_swings if val > recent_close.iloc[j-1] and val > recent_close.iloc[j+1]]
        price_troughs = [(j, val) for j, val in price_swings if val < recent_close.iloc[j-1] and val < recent_close.iloc[j+1]]
        rsi_peaks = [(j, val) for j, val in rsi_swings if val > recent_rsi.iloc[j-1] and val > recent_rsi.iloc[j+1]]
        rsi_troughs = [(j, val) for j, val in rsi_swings if val < recent_rsi.iloc[j-1] and val < recent_rsi.iloc[j+1]]
        
        # Check for divergences if we have enough swings
        current_bullish = False
        current_bearish = False
        current_hidden_bullish = False
        current_hidden_bearish = False
        
        if len(price_troughs) >= min_swings and len(rsi_troughs) >= min_swings:
            # Regular Bullish Divergence: Price makes lower low, RSI makes higher low
            if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
                latest_price_trough = price_troughs[-1]
                prev_price_trough = price_troughs[-2]
                latest_rsi_trough = rsi_troughs[-1]
                prev_rsi_trough = rsi_troughs[-2]
                
                # Require minimum divergence strength
                # Guard against divide-by-zero errors
                if prev_price_trough[1] != 0:
                    price_change = (latest_price_trough[1] - prev_price_trough[1]) / prev_price_trough[1]
                else:
                    price_change = 0
                
                if prev_rsi_trough[1] != 0:
                    rsi_change = (latest_rsi_trough[1] - prev_rsi_trough[1]) / prev_rsi_trough[1]
                else:
                    rsi_change = 0
                
                if (price_change < -min_change and rsi_change > min_change * 0.5):
                    current_bullish = True
            
            # Hidden Bullish Divergence: Price makes higher low, RSI makes lower low
            if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
                latest_price_trough = price_troughs[-1]
                prev_price_trough = price_troughs[-2]
                latest_rsi_trough = rsi_troughs[-1]
                prev_rsi_trough = rsi_troughs[-2]
                
                # Guard against divide-by-zero errors
                if prev_price_trough[1] != 0:
                    price_change = (latest_price_trough[1] - prev_price_trough[1]) / prev_price_trough[1]
                else:
                    price_change = 0
                
                if prev_rsi_trough[1] != 0:
                    rsi_change = (latest_rsi_trough[1] - prev_rsi_trough[1]) / prev_rsi_trough[1]
                else:
                    rsi_change = 0
                
                if (price_change > min_change and rsi_change < -min_change * 0.5):
                    current_hidden_bullish = True
        
        if len(price_peaks) >= min_swings and len(rsi_peaks) >= min_swings:
            # Regular Bearish Divergence: Price makes higher high, RSI makes lower high
            if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
                latest_price_peak = price_peaks[-1]
                prev_price_peak = price_peaks[-2]
                latest_rsi_peak = rsi_peaks[-1]
                prev_rsi_peak = rsi_peaks[-2]
                
                # Guard against divide-by-zero errors
                if prev_price_peak[1] != 0:
                    price_change = (latest_price_peak[1] - prev_price_peak[1]) / prev_price_peak[1]
                else:
                    price_change = 0
                
                if prev_rsi_peak[1] != 0:
                    rsi_change = (latest_rsi_peak[1] - prev_rsi_peak[1]) / prev_rsi_peak[1]
                else:
                    rsi_change = 0
                
                if (price_change > min_change and rsi_change < -min_change * 0.5):
                    current_bearish = True
            
            # Hidden Bearish Divergence: Price makes lower high, RSI makes higher high
            if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
                latest_price_peak = price_peaks[-1]
                prev_price_peak = price_peaks[-2]
                latest_rsi_peak = rsi_peaks[-1]
                prev_rsi_peak = rsi_peaks[-2]
                
                # Guard against divide-by-zero errors
                if prev_price_peak[1] != 0:
                    price_change = (latest_price_peak[1] - prev_price_peak[1]) / prev_price_peak[1]
                else:
                    price_change = 0
                
                if prev_rsi_peak[1] != 0:
                    rsi_change = (latest_rsi_peak[1] - prev_rsi_peak[1]) / prev_rsi_peak[1]
                else:
                    rsi_change = 0
                
                if (price_change < -min_change and rsi_change > min_change * 0.5):
                    current_hidden_bearish = True
        
        # Update persistence counters - only increment if current condition is met
        if current_bullish:
            bullish_persistence.iloc[i] = bullish_persistence.iloc[i-1] + 1
        else:
            bullish_persistence.iloc[i] = 0
            
        if current_bearish:
            bearish_persistence.iloc[i] = bearish_persistence.iloc[i-1] + 1
        else:
            bearish_persistence.iloc[i] = 0
            
        if current_hidden_bullish:
            hidden_bullish_persistence.iloc[i] = hidden_bullish_persistence.iloc[i-1] + 1
        else:
            hidden_bullish_persistence.iloc[i] = 0
            
        if current_hidden_bearish:
            hidden_bearish_persistence.iloc[i] = hidden_bearish_persistence.iloc[i-1] + 1
        else:
            hidden_bearish_persistence.iloc[i] = 0
        
        # Confirm signals only after persistence requirement AND only for the current bar
        # This ensures divergence is only true when conditions are actually met
        bullish_div.iloc[i] = current_bullish and bullish_persistence.iloc[i] >= persistence_bars
        bearish_div.iloc[i] = current_bearish and bearish_persistence.iloc[i] >= persistence_bars
        hidden_bullish_div.iloc[i] = current_hidden_bullish and hidden_bullish_persistence.iloc[i] >= persistence_bars
        hidden_bearish_div.iloc[i] = current_hidden_bearish and hidden_bearish_persistence.iloc[i] >= persistence_bars
    
    return bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div


def macd_divergence(close: pd.Series, macd_line: pd.Series, macd_histogram: pd.Series, lookback: int = 20, min_swings: int = 2, 
                   min_change: float = 0.02, persistence_bars: int = 3) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Compute MACD Divergence indicators with improved reliability.
    
    MACD Divergence detects when price and MACD are moving in opposite directions,
    which often signals potential trend reversals. This includes both regular
    and hidden divergences using both MACD line and histogram.
    
    IMPROVEMENTS:
    - Uses only close prices to eliminate repainting
    - Requires minimum price change for swing significance
    - Adds signal persistence to prevent flickering
    - More robust peak/trough detection
    - Uses both MACD line and histogram for confirmation
    
    Args:
        close: Price series (close prices only to avoid repainting)
        macd_line: MACD line series
        macd_histogram: MACD histogram series
        lookback: Period for divergence analysis
        min_swings: Minimum number of swings required for divergence
        min_change: Minimum price change required for significant swing (2% default)
        persistence_bars: Number of bars signal must persist before confirming
        
    Returns:
        (bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div) where:
        - bullish_div: Regular bullish divergence (price lower low, MACD higher low)
        - bearish_div: Regular bearish divergence (price higher high, MACD lower high)
        - hidden_bullish_div: Hidden bullish divergence (price higher low, MACD lower low)
        - hidden_bearish_div: Hidden bearish divergence (price lower high, MACD higher high)
    """
    bullish_div = pd.Series(False, index=close.index)
    bearish_div = pd.Series(False, index=close.index)
    hidden_bullish_div = pd.Series(False, index=close.index)
    hidden_bearish_div = pd.Series(False, index=close.index)
    
    # Signal persistence tracking
    bullish_persistence = pd.Series(0, index=close.index)
    bearish_persistence = pd.Series(0, index=close.index)
    hidden_bullish_persistence = pd.Series(0, index=close.index)
    hidden_bearish_persistence = pd.Series(0, index=close.index)
    
    def find_significant_swings(series: pd.Series, min_change: float) -> list:
        """Find significant swings with minimum change requirement."""
        swings = []
        for j in range(2, len(series) - 2):  # Need more context for significance
            # Check for peaks (local maxima with significance)
            if (series.iloc[j] > series.iloc[j-1] and 
                series.iloc[j] > series.iloc[j+1] and
                series.iloc[j] > series.iloc[j-2] and 
                series.iloc[j] > series.iloc[j+2]):
                
                # Check if this peak represents significant change
                if j >= 2:
                    prev_val = series.iloc[j-2]
                    change_pct = abs(series.iloc[j] - prev_val) / abs(prev_val) if prev_val != 0 else 0
                    if change_pct >= min_change:
                        swings.append((j, series.iloc[j]))
            
            # Check for troughs (local minima with significance)
            if (series.iloc[j] < series.iloc[j-1] and 
                series.iloc[j] < series.iloc[j+1] and
                series.iloc[j] < series.iloc[j-2] and 
                series.iloc[j] < series.iloc[j+2]):
                
                # Check if this trough represents significant change
                if j >= 2:
                    prev_val = series.iloc[j-2]
                    change_pct = abs(series.iloc[j] - prev_val) / abs(prev_val) if prev_val != 0 else 0
                    if change_pct >= min_change:
                        swings.append((j, series.iloc[j]))
        
        return swings
    
    for i in range(lookback + persistence_bars, len(close)):
        # Get recent data for analysis (use close prices only)
        recent_close = close.iloc[i-lookback+1:i+1]
        recent_macd_line = macd_line.iloc[i-lookback+1:i+1]
        recent_macd_hist = macd_histogram.iloc[i-lookback+1:i+1]
        
        # Find significant swings using close prices only
        price_swings = find_significant_swings(recent_close, min_change)
        macd_line_swings = find_significant_swings(recent_macd_line, min_change * 0.1)  # Lower threshold for MACD
        macd_hist_swings = find_significant_swings(recent_macd_hist, min_change * 0.05)  # Even lower for histogram
        
        # Separate peaks and troughs for price
        price_peaks = [(j, val) for j, val in price_swings if val > recent_close.iloc[j-1] and val > recent_close.iloc[j+1]]
        price_troughs = [(j, val) for j, val in price_swings if val < recent_close.iloc[j-1] and val < recent_close.iloc[j+1]]
        
        # Separate peaks and troughs for MACD line
        macd_line_peaks = [(j, val) for j, val in macd_line_swings if val > recent_macd_line.iloc[j-1] and val > recent_macd_line.iloc[j+1]]
        macd_line_troughs = [(j, val) for j, val in macd_line_swings if val < recent_macd_line.iloc[j-1] and val < recent_macd_line.iloc[j+1]]
        
        # Separate peaks and troughs for MACD histogram
        macd_hist_peaks = [(j, val) for j, val in macd_hist_swings if val > recent_macd_hist.iloc[j-1] and val > recent_macd_hist.iloc[j+1]]
        macd_hist_troughs = [(j, val) for j, val in macd_hist_swings if val < recent_macd_hist.iloc[j-1] and val < recent_macd_hist.iloc[j+1]]
        
        # Check for divergences if we have enough swings
        current_bullish = False
        current_bearish = False
        current_hidden_bullish = False
        current_hidden_bearish = False
        
        # Check MACD line divergences
        if len(price_troughs) >= min_swings and len(macd_line_troughs) >= min_swings:
            # Regular Bullish Divergence: Price makes lower low, MACD makes higher low
            if len(price_troughs) >= 2 and len(macd_line_troughs) >= 2:
                latest_price_trough = price_troughs[-1]
                prev_price_trough = price_troughs[-2]
                latest_macd_trough = macd_line_troughs[-1]
                prev_macd_trough = macd_line_troughs[-2]
                
                # Require minimum divergence strength
                price_change = (latest_price_trough[1] - prev_price_trough[1]) / prev_price_trough[1]
                macd_change = (latest_macd_trough[1] - prev_macd_trough[1]) / abs(prev_macd_trough[1]) if prev_macd_trough[1] != 0 else 0
                
                if (price_change < -min_change and macd_change > min_change * 0.5):
                    current_bullish = True
            
            # Hidden Bullish Divergence: Price makes higher low, MACD makes lower low
            if len(price_troughs) >= 2 and len(macd_line_troughs) >= 2:
                latest_price_trough = price_troughs[-1]
                prev_price_trough = price_troughs[-2]
                latest_macd_trough = macd_line_troughs[-1]
                prev_macd_trough = macd_line_troughs[-2]
                
                price_change = (latest_price_trough[1] - prev_price_trough[1]) / prev_price_trough[1]
                macd_change = (latest_macd_trough[1] - prev_macd_trough[1]) / abs(prev_macd_trough[1]) if prev_macd_trough[1] != 0 else 0
                
                if (price_change > min_change and macd_change < -min_change * 0.5):
                    current_hidden_bullish = True
        
        if len(price_peaks) >= min_swings and len(macd_line_peaks) >= min_swings:
            # Regular Bearish Divergence: Price makes higher high, MACD makes lower high
            if len(price_peaks) >= 2 and len(macd_line_peaks) >= 2:
                latest_price_peak = price_peaks[-1]
                prev_price_peak = price_peaks[-2]
                latest_macd_peak = macd_line_peaks[-1]
                prev_macd_peak = macd_line_peaks[-2]
                
                price_change = (latest_price_peak[1] - prev_price_peak[1]) / prev_price_peak[1]
                macd_change = (latest_macd_peak[1] - prev_macd_peak[1]) / abs(prev_macd_peak[1]) if prev_macd_peak[1] != 0 else 0
                
                if (price_change > min_change and macd_change < -min_change * 0.5):
                    current_bearish = True
            
            # Hidden Bearish Divergence: Price makes lower high, MACD makes higher high
            if len(price_peaks) >= 2 and len(macd_line_peaks) >= 2:
                latest_price_peak = price_peaks[-1]
                prev_price_peak = price_peaks[-2]
                latest_macd_peak = macd_line_peaks[-1]
                prev_macd_peak = macd_line_peaks[-2]
                
                price_change = (latest_price_peak[1] - prev_price_peak[1]) / prev_price_peak[1]
                macd_change = (latest_macd_peak[1] - prev_macd_peak[1]) / abs(prev_macd_peak[1]) if prev_macd_peak[1] != 0 else 0
                
                if (price_change < -min_change and macd_change > min_change * 0.5):
                    current_hidden_bearish = True
        
        # Additional confirmation using MACD histogram
        if current_bullish and len(macd_hist_troughs) >= 2:
            # Check if histogram also shows bullish divergence
            latest_hist_trough = macd_hist_troughs[-1]
            prev_hist_trough = macd_hist_troughs[-2]
            hist_change = (latest_hist_trough[1] - prev_hist_trough[1]) / abs(prev_hist_trough[1]) if prev_hist_trough[1] != 0 else 0
            if hist_change < min_change * 0.5:  # Histogram should be improving (less negative)
                current_bullish = True
            else:
                current_bullish = False
        
        if current_bearish and len(macd_hist_peaks) >= 2:
            # Check if histogram also shows bearish divergence
            latest_hist_peak = macd_hist_peaks[-1]
            prev_hist_peak = macd_hist_peaks[-2]
            hist_change = (latest_hist_peak[1] - prev_hist_peak[1]) / abs(prev_hist_peak[1]) if prev_hist_peak[1] != 0 else 0
            if hist_change > -min_change * 0.5:  # Histogram should be weakening (less positive)
                current_bearish = True
            else:
                current_bearish = False
        
        # Update persistence counters - only increment if current condition is met
        if current_bullish:
            bullish_persistence.iloc[i] = bullish_persistence.iloc[i-1] + 1
        else:
            bullish_persistence.iloc[i] = 0
            
        if current_bearish:
            bearish_persistence.iloc[i] = bearish_persistence.iloc[i-1] + 1
        else:
            bearish_persistence.iloc[i] = 0
            
        if current_hidden_bullish:
            hidden_bullish_persistence.iloc[i] = hidden_bullish_persistence.iloc[i-1] + 1
        else:
            hidden_bullish_persistence.iloc[i] = 0
            
        if current_hidden_bearish:
            hidden_bearish_persistence.iloc[i] = hidden_bearish_persistence.iloc[i-1] + 1
        else:
            hidden_bearish_persistence.iloc[i] = 0
        
        # Confirm signals only after persistence requirement AND only for the current bar
        # This ensures divergence is only true when conditions are actually met
        bullish_div.iloc[i] = current_bullish and bullish_persistence.iloc[i] >= persistence_bars
        bearish_div.iloc[i] = current_bearish and bearish_persistence.iloc[i] >= persistence_bars
        hidden_bullish_div.iloc[i] = current_hidden_bullish and hidden_bullish_persistence.iloc[i] >= persistence_bars
        hidden_bearish_div.iloc[i] = current_hidden_bearish and hidden_bearish_persistence.iloc[i] >= persistence_bars
    
    return bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div


def parabola_detector(prices, lookback=50, confidence_threshold=0.70, deviation_threshold=0.02, 
                     use_atr_filter=True, use_adx_filter=True, atr_period=14, adx_period=14, 
                     adx_threshold=15, atr_threshold=0.3, persistence_bars=3):
    """
    Detect parabolic price patterns and generate signals when parabolas END.
    
    Trading Logic:
    - End of Bullish Parabola = SHORT signal (bubble popping)
    - End of Bearish Parabola = LONG signal (crash bottoming)
    
    Args:
        prices: Series of closing prices
        lookback: Number of bars to analyze for parabola fitting
        confidence_threshold: Minimum R² for valid parabola (0.0-1.0)
        deviation_threshold: Price deviation to trigger break (0.01-0.1)
        use_atr_filter: Enable ATR volatility filter
        use_adx_filter: Enable ADX trend strength filter
        atr_period: ATR calculation period
        adx_period: ADX calculation period
        adx_threshold: Minimum ADX for trend strength
        atr_threshold: ATR multiplier for volatility filter
        persistence_bars: Bars to maintain signal after parabola break
    
    Returns:
        tuple: (parabola_bullish_end, parabola_bearish_end, parabola_confidence, parabola_active)
    """
    if len(prices) < lookback:
        return pd.Series(False, index=prices.index), pd.Series(False, index=prices.index), pd.Series(0.0, index=prices.index), pd.Series(False, index=prices.index)
    
    # Initialize output series
    parabola_bullish_end = pd.Series(False, index=prices.index)  # SHORT signal
    parabola_bearish_end = pd.Series(False, index=prices.index)  # LONG signal
    parabola_confidence = pd.Series(0.0, index=prices.index)
    parabola_active = pd.Series(False, index=prices.index)
    
    # Track parabola state
    in_parabola = False
    parabola_direction = ''
    parabola_start_idx = -1
    parabola_break_count = 0
    
    # Calculate ATR and ADX for filters
    if use_atr_filter or use_adx_filter:
        df_temp = pd.DataFrame({'Close': prices, 'High': prices, 'Low': prices, 'Open': prices})
        df_temp['High'] = df_temp['Close'] * 1.01  # Approximate high
        df_temp['Low'] = df_temp['Close'] * 0.99   # Approximate low
        df_temp['Open'] = df_temp['Close'].shift(1)
        
        if use_atr_filter:
            atr_values = atr(df_temp, atr_period)
            atr_sma = atr_values.rolling(window=20, min_periods=1).mean()
        else:
            atr_values = pd.Series(1.0, index=prices.index)
            atr_sma = pd.Series(1.0, index=prices.index)
            
        if use_adx_filter:
            adx_values = adx(df_temp, adx_period)
        else:
            adx_values = pd.Series(50.0, index=prices.index)
    
    # Parabola fitting function
    def fit_parabola(price_array):
        if len(price_array) < 3:
            return None, None, None, 0.0
        
        n = len(price_array)
        x = np.arange(n)
        y = np.array(price_array)
        
        # Least squares regression for parabola: y = ax² + bx + c
        # Create design matrix: [x², x, 1]
        X = np.column_stack([x**2, x, np.ones(n)])
        
        try:
            # Solve normal equations: (X'X)β = X'y
            coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
            a, b, c = coeffs
            
            # Calculate R-squared
            y_pred = a * x**2 + b * x + c
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            return a, b, c, r_squared
        except:
            return None, None, None, 0.0
    
    # Rolling parabola detection
    for i in range(lookback, len(prices)):
        # Get lookback window
        window_prices = prices.iloc[i-lookback+1:i+1].values
        
        # Apply filters
        if use_atr_filter and i >= atr_period:
            has_volatility = atr_values.iloc[i] > (atr_sma.iloc[i] * atr_threshold)
        else:
            has_volatility = True
            
        if use_adx_filter and i >= adx_period:
            is_trending = adx_values.iloc[i] > adx_threshold
        else:
            is_trending = True
        
        if has_volatility and is_trending:
            # Fit parabola
            a, b, c, r_squared = fit_parabola(window_prices)
            
            if a is not None and r_squared >= confidence_threshold:
                # New parabola detected
                if not in_parabola:
                    in_parabola = True
                    parabola_direction = 'up' if a > 0 else 'down'
                    parabola_start_idx = i
                    parabola_break_count = 0
                    parabola_active.iloc[i] = True
                    parabola_confidence.iloc[i] = r_squared
                else:
                    # Continue existing parabola
                    parabola_active.iloc[i] = True
                    parabola_confidence.iloc[i] = r_squared
                
                # Check for parabola break (price deviates significantly from expected path)
                if in_parabola:
                    # Calculate expected price based on parabola
                    time_diff = lookback - 1  # Current position in the parabola
                    expected_price = a * (time_diff ** 2) + b * time_diff + c
                    actual_price = prices.iloc[i]
                    
                    # Check if price deviates beyond threshold
                    price_deviation = abs(actual_price - expected_price) / expected_price
                    if price_deviation > deviation_threshold:
                        parabola_break_count += 1
                        
                        # Generate signal when parabola breaks (END of parabola)
                        if parabola_break_count >= 2:  # Require 2 consecutive breaks for confirmation
                            if parabola_direction == 'up':
                                # End of bullish parabola = SHORT signal
                                parabola_bullish_end.iloc[i] = True
                            elif parabola_direction == 'down':
                                # End of bearish parabola = LONG signal
                                parabola_bearish_end.iloc[i] = True
                            
                            # Reset parabola state
                            in_parabola = False
                            parabola_direction = ''
                            parabola_start_idx = -1
                            parabola_break_count = 0
                    else:
                        # Reset break count if price returns to parabola
                        parabola_break_count = 0
            else:
                # No valid parabola detected
                if in_parabola:
                    # Parabola ended without clear break - still generate signal
                    if parabola_direction == 'up':
                        parabola_bullish_end.iloc[i] = True
                    elif parabola_direction == 'down':
                        parabola_bearish_end.iloc[i] = True
                    
                    # Reset parabola state
                    in_parabola = False
                    parabola_direction = ''
                    parabola_start_idx = -1
                    parabola_break_count = 0
    
    return parabola_bullish_end, parabola_bearish_end, parabola_confidence, parabola_active


def stoch_rsi_divergence(close: pd.Series, stoch_rsi: pd.Series, lookback: int = 20, min_swings: int = 2, 
                        min_change: float = 0.02, persistence_bars: int = 3) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Compute Stochastic RSI Divergence indicators with improved reliability.
    
    Stochastic RSI Divergence detects when price and Stochastic RSI are moving in opposite directions,
    which often signals potential trend reversals. This includes both regular
    and hidden divergences.
    
    IMPROVEMENTS:
    - Uses only close prices to eliminate repainting
    - Requires minimum price change for swing significance
    - Adds signal persistence to prevent flickering
    - More robust peak/trough detection
    - Uses Stochastic RSI's 0-100 scale for better divergence detection
    
    Args:
        close: Price series (close prices only to avoid repainting)
        stoch_rsi: Stochastic RSI series (0-100 scale)
        lookback: Period for divergence analysis
        min_swings: Minimum number of swings required for divergence
        min_change: Minimum price change required for significant swing (2% default)
        persistence_bars: Number of bars signal must persist before confirming
        
    Returns:
        (bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div) where:
        - bullish_div: Regular bullish divergence (price lower low, Stoch RSI higher low)
        - bearish_div: Regular bearish divergence (price higher high, Stoch RSI lower high)
        - hidden_bullish_div: Hidden bullish divergence (price higher low, Stoch RSI lower low)
        - hidden_bearish_div: Hidden bearish divergence (price lower high, Stoch RSI higher high)
    """
    bullish_div = pd.Series(False, index=close.index)
    bearish_div = pd.Series(False, index=close.index)
    hidden_bullish_div = pd.Series(False, index=close.index)
    hidden_bearish_div = pd.Series(False, index=close.index)
    
    # Signal persistence tracking
    bullish_persistence = pd.Series(0, index=close.index)
    bearish_persistence = pd.Series(0, index=close.index)
    hidden_bullish_persistence = pd.Series(0, index=close.index)
    hidden_bearish_persistence = pd.Series(0, index=close.index)
    
    def find_significant_swings(series: pd.Series, min_change: float) -> list:
        """Find significant swings with minimum change requirement."""
        swings = []
        for j in range(2, len(series) - 2):  # Need more context for significance
            # Check for peaks (local maxima with significance)
            if (series.iloc[j] > series.iloc[j-1] and 
                series.iloc[j] > series.iloc[j+1] and
                series.iloc[j] > series.iloc[j-2] and 
                series.iloc[j] > series.iloc[j+2]):
                
                # Check if this peak represents significant change
                if j >= 2:
                    prev_val = series.iloc[j-2]
                    change_pct = abs(series.iloc[j] - prev_val) / abs(prev_val) if prev_val != 0 else 0
                    if change_pct >= min_change:
                        swings.append((j, series.iloc[j]))
            
            # Check for troughs (local minima with significance)
            if (series.iloc[j] < series.iloc[j-1] and 
                series.iloc[j] < series.iloc[j+1] and
                series.iloc[j] < series.iloc[j-2] and 
                series.iloc[j] < series.iloc[j+2]):
                
                # Check if this trough represents significant change
                if j >= 2:
                    prev_val = series.iloc[j-2]
                    change_pct = abs(series.iloc[j] - prev_val) / abs(prev_val) if prev_val != 0 else 0
                    if change_pct >= min_change:
                        swings.append((j, series.iloc[j]))
        
        return swings
    
    for i in range(lookback + persistence_bars, len(close)):
        # Get recent data for analysis (use close prices only)
        recent_close = close.iloc[i-lookback+1:i+1]
        recent_stoch_rsi = stoch_rsi.iloc[i-lookback+1:i+1]
        
        # Find significant swings using close prices only
        price_swings = find_significant_swings(recent_close, min_change)
        stoch_rsi_swings = find_significant_swings(recent_stoch_rsi, min_change * 0.05)  # Lower threshold for Stoch RSI (0-100 scale)
        
        # Separate peaks and troughs for price
        price_peaks = [(j, val) for j, val in price_swings if val > recent_close.iloc[j-1] and val > recent_close.iloc[j+1]]
        price_troughs = [(j, val) for j, val in price_swings if val < recent_close.iloc[j-1] and val < recent_close.iloc[j+1]]
        
        # Separate peaks and troughs for Stochastic RSI
        stoch_rsi_peaks = [(j, val) for j, val in stoch_rsi_swings if val > recent_stoch_rsi.iloc[j-1] and val > recent_stoch_rsi.iloc[j+1]]
        stoch_rsi_troughs = [(j, val) for j, val in stoch_rsi_swings if val < recent_stoch_rsi.iloc[j-1] and val < recent_stoch_rsi.iloc[j+1]]
        
        # Check for divergences if we have enough swings
        current_bullish = False
        current_bearish = False
        current_hidden_bullish = False
        current_hidden_bearish = False
        
        if len(price_troughs) >= min_swings and len(stoch_rsi_troughs) >= min_swings:
            # Regular Bullish Divergence: Price makes lower low, Stoch RSI makes higher low
            if len(price_troughs) >= 2 and len(stoch_rsi_troughs) >= 2:
                latest_price_trough = price_troughs[-1]
                prev_price_trough = price_troughs[-2]
                latest_stoch_trough = stoch_rsi_troughs[-1]
                prev_stoch_trough = stoch_rsi_troughs[-2]
                
                # Require minimum divergence strength
                price_change = (latest_price_trough[1] - prev_price_trough[1]) / prev_price_trough[1]
                stoch_change = (latest_stoch_trough[1] - prev_stoch_trough[1]) / 100.0  # Normalize to 0-1 scale
                
                if (price_change < -min_change and stoch_change > min_change * 0.1):  # 0.1 = 10% of 0-100 scale
                    current_bullish = True
            
            # Hidden Bullish Divergence: Price makes higher low, Stoch RSI makes lower low
            if len(price_troughs) >= 2 and len(stoch_rsi_troughs) >= 2:
                latest_price_trough = price_troughs[-1]
                prev_price_trough = price_troughs[-2]
                latest_stoch_trough = stoch_rsi_troughs[-1]
                prev_stoch_trough = stoch_rsi_troughs[-2]
                
                price_change = (latest_price_trough[1] - prev_price_trough[1]) / prev_price_trough[1]
                stoch_change = (latest_stoch_trough[1] - prev_stoch_trough[1]) / 100.0  # Normalize to 0-1 scale
                
                if (price_change > min_change and stoch_change < -min_change * 0.1):  # 0.1 = 10% of 0-100 scale
                    current_hidden_bullish = True
        
        if len(price_peaks) >= min_swings and len(stoch_rsi_peaks) >= min_swings:
            # Regular Bearish Divergence: Price makes higher high, Stoch RSI makes lower high
            if len(price_peaks) >= 2 and len(stoch_rsi_peaks) >= 2:
                latest_price_peak = price_peaks[-1]
                prev_price_peak = price_peaks[-2]
                latest_stoch_peak = stoch_rsi_peaks[-1]
                prev_stoch_peak = stoch_rsi_peaks[-2]
                
                price_change = (latest_price_peak[1] - prev_price_peak[1]) / prev_price_peak[1]
                stoch_change = (latest_stoch_peak[1] - prev_stoch_peak[1]) / 100.0  # Normalize to 0-1 scale
                
                if (price_change > min_change and stoch_change < -min_change * 0.1):  # 0.1 = 10% of 0-100 scale
                    current_bearish = True
            
            # Hidden Bearish Divergence: Price makes lower high, Stoch RSI makes higher high
            if len(price_peaks) >= 2 and len(stoch_rsi_peaks) >= 2:
                latest_price_peak = price_peaks[-1]
                prev_price_peak = price_peaks[-2]
                latest_stoch_peak = stoch_rsi_peaks[-1]
                prev_stoch_peak = stoch_rsi_peaks[-2]
                
                price_change = (latest_price_peak[1] - prev_price_peak[1]) / prev_price_peak[1]
                stoch_change = (latest_stoch_peak[1] - prev_stoch_peak[1]) / 100.0  # Normalize to 0-1 scale
                
                if (price_change < -min_change and stoch_change > min_change * 0.1):  # 0.1 = 10% of 0-100 scale
                    current_hidden_bearish = True
        
        # Update persistence counters - only increment if current condition is met
        if current_bullish:
            bullish_persistence.iloc[i] = bullish_persistence.iloc[i-1] + 1
        else:
            bullish_persistence.iloc[i] = 0
            
        if current_bearish:
            bearish_persistence.iloc[i] = bearish_persistence.iloc[i-1] + 1
        else:
            bearish_persistence.iloc[i] = 0
            
        if current_hidden_bullish:
            hidden_bullish_persistence.iloc[i] = hidden_bullish_persistence.iloc[i-1] + 1
        else:
            hidden_bullish_persistence.iloc[i] = 0
            
        if current_hidden_bearish:
            hidden_bearish_persistence.iloc[i] = hidden_bearish_persistence.iloc[i-1] + 1
        else:
            hidden_bearish_persistence.iloc[i] = 0
        
        # Confirm signals only after persistence requirement AND only for the current bar
        # This ensures divergence is only true when conditions are actually met
        bullish_div.iloc[i] = current_bullish and bullish_persistence.iloc[i] >= persistence_bars
        bearish_div.iloc[i] = current_bearish and bearish_persistence.iloc[i] >= persistence_bars
        hidden_bullish_div.iloc[i] = current_hidden_bullish and hidden_bullish_persistence.iloc[i] >= persistence_bars
        hidden_bearish_div.iloc[i] = current_hidden_bearish and hidden_bearish_persistence.iloc[i] >= persistence_bars
    
    return bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div


def cci_divergence(close: pd.Series, cci: pd.Series, lookback: int = 20, min_swings: int = 2, 
                  min_change: float = 0.02, persistence_bars: int = 3) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Compute CCI Divergence indicators with improved reliability.
    
    CCI Divergence detects when price and CCI are moving in opposite directions,
    which often signals potential trend reversals. This includes both regular
    and hidden divergences.
    
    IMPROVEMENTS:
    - Uses only close prices to eliminate repainting
    - Requires minimum price change for swing significance
    - Adds signal persistence to prevent flickering
    - More robust peak/trough detection
    - Uses CCI's unbounded scale for better divergence detection
    
    Args:
        close: Price series (close prices only to avoid repainting)
        cci: CCI series (unbounded scale, typically -100 to +100 range)
        lookback: Period for divergence analysis
        min_swings: Minimum number of swings required for divergence
        min_change: Minimum price change required for significant swing (2% default)
        persistence_bars: Number of bars signal must persist before confirming
        
    Returns:
        (bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div) where:
        - bullish_div: Regular bullish divergence (price lower low, CCI higher low)
        - bearish_div: Regular bearish divergence (price higher high, CCI lower high)
        - hidden_bullish_div: Hidden bullish divergence (price higher low, CCI lower low)
        - hidden_bearish_div: Hidden bearish divergence (price lower high, CCI higher high)
    """
    bullish_div = pd.Series(False, index=close.index)
    bearish_div = pd.Series(False, index=close.index)
    hidden_bullish_div = pd.Series(False, index=close.index)
    hidden_bearish_div = pd.Series(False, index=close.index)
    
    # Signal persistence tracking
    bullish_persistence = pd.Series(0, index=close.index)
    bearish_persistence = pd.Series(0, index=close.index)
    hidden_bullish_persistence = pd.Series(0, index=close.index)
    hidden_bearish_persistence = pd.Series(0, index=close.index)
    
    def find_significant_swings(series: pd.Series, min_change: float) -> list:
        """Find significant swings with minimum change requirement."""
        swings = []
        for j in range(2, len(series) - 2):  # Need more context for significance
            # Check for peaks (local maxima with significance)
            if (series.iloc[j] > series.iloc[j-1] and 
                series.iloc[j] > series.iloc[j+1] and
                series.iloc[j] > series.iloc[j-2] and 
                series.iloc[j] > series.iloc[j+2]):
                
                # Check if this peak represents significant change
                if j >= 2:
                    prev_val = series.iloc[j-2]
                    change_pct = abs(series.iloc[j] - prev_val) / abs(prev_val) if prev_val != 0 else 0
                    if change_pct >= min_change:
                        swings.append((j, series.iloc[j]))
            
            # Check for troughs (local minima with significance)
            if (series.iloc[j] < series.iloc[j-1] and 
                series.iloc[j] < series.iloc[j+1] and
                series.iloc[j] < series.iloc[j-2] and 
                series.iloc[j] < series.iloc[j+2]):
                
                # Check if this trough represents significant change
                if j >= 2:
                    prev_val = series.iloc[j-2]
                    change_pct = abs(series.iloc[j] - prev_val) / abs(prev_val) if prev_val != 0 else 0
                    if change_pct >= min_change:
                        swings.append((j, series.iloc[j]))
        
        return swings
    
    for i in range(lookback + persistence_bars, len(close)):
        # Get recent data for analysis (use close prices only)
        recent_close = close.iloc[i-lookback+1:i+1]
        recent_cci = cci.iloc[i-lookback+1:i+1]
        
        # Find significant swings using close prices only
        price_swings = find_significant_swings(recent_close, min_change)
        cci_swings = find_significant_swings(recent_cci, min_change * 0.1)  # Lower threshold for CCI (unbounded scale)
        
        # Separate peaks and troughs for price
        price_peaks = [(j, val) for j, val in price_swings if val > recent_close.iloc[j-1] and val > recent_close.iloc[j+1]]
        price_troughs = [(j, val) for j, val in price_swings if val < recent_close.iloc[j-1] and val < recent_close.iloc[j+1]]
        
        # Separate peaks and troughs for CCI
        cci_peaks = [(j, val) for j, val in cci_swings if val > recent_cci.iloc[j-1] and val > recent_cci.iloc[j+1]]
        cci_troughs = [(j, val) for j, val in cci_swings if val < recent_cci.iloc[j-1] and val < recent_cci.iloc[j+1]]
        
        # Check for divergences if we have enough swings
        current_bullish = False
        current_bearish = False
        current_hidden_bullish = False
        current_hidden_bearish = False
        
        if len(price_troughs) >= min_swings and len(cci_troughs) >= min_swings:
            # Regular Bullish Divergence: Price makes lower low, CCI makes higher low
            if len(price_troughs) >= 2 and len(cci_troughs) >= 2:
                latest_price_trough = price_troughs[-1]
                prev_price_trough = price_troughs[-2]
                latest_cci_trough = cci_troughs[-1]
                prev_cci_trough = cci_troughs[-2]
                
                # Require minimum divergence strength
                price_change = (latest_price_trough[1] - prev_price_trough[1]) / prev_price_trough[1]
                cci_change = (latest_cci_trough[1] - prev_cci_trough[1]) / 100.0  # Normalize to typical CCI range
                
                if (price_change < -min_change and cci_change > min_change * 0.1):  # 0.1 = 10% of typical CCI range
                    current_bullish = True
            
            # Hidden Bullish Divergence: Price makes higher low, CCI makes lower low
            if len(price_troughs) >= 2 and len(cci_troughs) >= 2:
                latest_price_trough = price_troughs[-1]
                prev_price_trough = price_troughs[-2]
                latest_cci_trough = cci_troughs[-1]
                prev_cci_trough = cci_troughs[-2]
                
                price_change = (latest_price_trough[1] - prev_price_trough[1]) / prev_price_trough[1]
                cci_change = (latest_cci_trough[1] - prev_cci_trough[1]) / 100.0  # Normalize to typical CCI range
                
                if (price_change > min_change and cci_change < -min_change * 0.1):  # 0.1 = 10% of typical CCI range
                    current_hidden_bullish = True
        
        if len(price_peaks) >= min_swings and len(cci_peaks) >= min_swings:
            # Regular Bearish Divergence: Price makes higher high, CCI makes lower high
            if len(price_peaks) >= 2 and len(cci_peaks) >= 2:
                latest_price_peak = price_peaks[-1]
                prev_price_peak = price_peaks[-2]
                latest_cci_peak = cci_peaks[-1]
                prev_cci_peak = cci_peaks[-2]
                
                price_change = (latest_price_peak[1] - prev_price_peak[1]) / prev_price_peak[1]
                cci_change = (latest_cci_peak[1] - prev_cci_peak[1]) / 100.0  # Normalize to typical CCI range
                
                if (price_change > min_change and cci_change < -min_change * 0.1):  # 0.1 = 10% of typical CCI range
                    current_bearish = True
            
            # Hidden Bearish Divergence: Price makes lower high, CCI makes higher high
            if len(price_peaks) >= 2 and len(cci_peaks) >= 2:
                latest_price_peak = price_peaks[-1]
                prev_price_peak = price_peaks[-2]
                latest_cci_peak = cci_peaks[-1]
                prev_cci_peak = cci_peaks[-2]
                
                price_change = (latest_price_peak[1] - prev_price_peak[1]) / prev_price_peak[1]
                cci_change = (latest_cci_peak[1] - prev_cci_peak[1]) / 100.0  # Normalize to typical CCI range
                
                if (price_change < -min_change and cci_change > min_change * 0.1):  # 0.1 = 10% of typical CCI range
                    current_hidden_bearish = True
        
        # Update persistence counters - only increment if current condition is met
        if current_bullish:
            bullish_persistence.iloc[i] = bullish_persistence.iloc[i-1] + 1
        else:
            bullish_persistence.iloc[i] = 0
            
        if current_bearish:
            bearish_persistence.iloc[i] = bearish_persistence.iloc[i-1] + 1
        else:
            bearish_persistence.iloc[i] = 0
            
        if current_hidden_bullish:
            hidden_bullish_persistence.iloc[i] = hidden_bullish_persistence.iloc[i-1] + 1
        else:
            hidden_bullish_persistence.iloc[i] = 0
            
        if current_hidden_bearish:
            hidden_bearish_persistence.iloc[i] = hidden_bearish_persistence.iloc[i-1] + 1
        else:
            hidden_bearish_persistence.iloc[i] = 0
        
        # Confirm signals only after persistence requirement AND only for the current bar
        # This ensures divergence is only true when conditions are actually met
        bullish_div.iloc[i] = current_bullish and bullish_persistence.iloc[i] >= persistence_bars
        bearish_div.iloc[i] = current_bearish and bearish_persistence.iloc[i] >= persistence_bars
        hidden_bullish_div.iloc[i] = current_hidden_bullish and hidden_bullish_persistence.iloc[i] >= persistence_bars
        hidden_bearish_div.iloc[i] = current_hidden_bearish and hidden_bearish_persistence.iloc[i] >= persistence_bars
    
    return bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div


def mfi_divergence(close: pd.Series, mfi: pd.Series, lookback: int = 20, min_swings: int = 2, 
                  min_change: float = 0.02, persistence_bars: int = 3) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Compute MFI Divergence indicators with improved reliability.
    
    MFI Divergence detects when price and MFI are moving in opposite directions,
    which often signals potential trend reversals. This includes both regular
    and hidden divergences.
    
    IMPROVEMENTS:
    - Uses only close prices to eliminate repainting
    - Requires minimum price change for swing significance
    - Adds signal persistence to prevent flickering
    - More robust peak/trough detection
    - Uses MFI's 0-100 scale for better divergence detection
    
    Args:
        close: Price series (close prices only to avoid repainting)
        mfi: MFI series (0-100 scale)
        lookback: Period for divergence analysis
        min_swings: Minimum number of swings required for divergence
        min_change: Minimum price change required for significant swing (2% default)
        persistence_bars: Number of bars signal must persist before confirming
        
    Returns:
        (bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div) where:
        - bullish_div: Regular bullish divergence (price lower low, MFI higher low)
        - bearish_div: Regular bearish divergence (price higher high, MFI lower high)
        - hidden_bullish_div: Hidden bullish divergence (price higher low, MFI lower low)
        - hidden_bearish_div: Hidden bearish divergence (price lower high, MFI higher high)
    """
    bullish_div = pd.Series(False, index=close.index)
    bearish_div = pd.Series(False, index=close.index)
    hidden_bullish_div = pd.Series(False, index=close.index)
    hidden_bearish_div = pd.Series(False, index=close.index)
    
    # Signal persistence tracking
    bullish_persistence = pd.Series(0, index=close.index)
    bearish_persistence = pd.Series(0, index=close.index)
    hidden_bullish_persistence = pd.Series(0, index=close.index)
    hidden_bearish_persistence = pd.Series(0, index=close.index)
    
    def find_significant_swings(series: pd.Series, min_change: float) -> list:
        """Find significant swings with minimum change requirement."""
        swings = []
        for j in range(2, len(series) - 2):  # Need more context for significance
            # Check for peaks (local maxima with significance)
            if (series.iloc[j] > series.iloc[j-1] and 
                series.iloc[j] > series.iloc[j+1] and
                series.iloc[j] > series.iloc[j-2] and 
                series.iloc[j] > series.iloc[j+2]):
                
                # Check if this peak represents significant change
                if j >= 2:
                    prev_val = series.iloc[j-2]
                    change_pct = abs(series.iloc[j] - prev_val) / abs(prev_val) if prev_val != 0 else 0
                    if change_pct >= min_change:
                        swings.append((j, series.iloc[j]))
            
            # Check for troughs (local minima with significance)
            if (series.iloc[j] < series.iloc[j-1] and 
                series.iloc[j] < series.iloc[j+1] and
                series.iloc[j] < series.iloc[j-2] and 
                series.iloc[j] < series.iloc[j+2]):
                
                # Check if this trough represents significant change
                if j >= 2:
                    prev_val = series.iloc[j-2]
                    change_pct = abs(series.iloc[j] - prev_val) / abs(prev_val) if prev_val != 0 else 0
                    if change_pct >= min_change:
                        swings.append((j, series.iloc[j]))
        
        return swings
    
    for i in range(lookback + persistence_bars, len(close)):
        # Get recent data for analysis (use close prices only)
        recent_close = close.iloc[i-lookback+1:i+1]
        recent_mfi = mfi.iloc[i-lookback+1:i+1]
        
        # Find significant swings using close prices only
        price_swings = find_significant_swings(recent_close, min_change)
        mfi_swings = find_significant_swings(recent_mfi, min_change * 0.05)  # Lower threshold for MFI (0-100 scale)
        
        # Separate peaks and troughs for price
        price_peaks = [(j, val) for j, val in price_swings if val > recent_close.iloc[j-1] and val > recent_close.iloc[j+1]]
        price_troughs = [(j, val) for j, val in price_swings if val < recent_close.iloc[j-1] and val < recent_close.iloc[j+1]]
        
        # Separate peaks and troughs for MFI
        mfi_peaks = [(j, val) for j, val in mfi_swings if val > recent_mfi.iloc[j-1] and val > recent_mfi.iloc[j+1]]
        mfi_troughs = [(j, val) for j, val in mfi_swings if val < recent_mfi.iloc[j-1] and val < recent_mfi.iloc[j+1]]
        
        # Check for divergences if we have enough swings
        current_bullish = False
        current_bearish = False
        current_hidden_bullish = False
        current_hidden_bearish = False
        
        if len(price_troughs) >= min_swings and len(mfi_troughs) >= min_swings:
            # Regular Bullish Divergence: Price makes lower low, MFI makes higher low
            if len(price_troughs) >= 2 and len(mfi_troughs) >= 2:
                latest_price_trough = price_troughs[-1]
                prev_price_trough = price_troughs[-2]
                latest_mfi_trough = mfi_troughs[-1]
                prev_mfi_trough = mfi_troughs[-2]
                
                # Require minimum divergence strength
                price_change = (latest_price_trough[1] - prev_price_trough[1]) / prev_price_trough[1]
                mfi_change = (latest_mfi_trough[1] - prev_mfi_trough[1]) / 100.0  # Normalize to 0-1 scale
                
                if (price_change < -min_change and mfi_change > min_change * 0.1):  # 0.1 = 10% of 0-100 scale
                    current_bullish = True
            
            # Hidden Bullish Divergence: Price makes higher low, MFI makes lower low
            if len(price_troughs) >= 2 and len(mfi_troughs) >= 2:
                latest_price_trough = price_troughs[-1]
                prev_price_trough = price_troughs[-2]
                latest_mfi_trough = mfi_troughs[-1]
                prev_mfi_trough = mfi_troughs[-2]
                
                price_change = (latest_price_trough[1] - prev_price_trough[1]) / prev_price_trough[1]
                mfi_change = (latest_mfi_trough[1] - prev_mfi_trough[1]) / 100.0  # Normalize to 0-1 scale
                
                if (price_change > min_change and mfi_change < -min_change * 0.1):  # 0.1 = 10% of 0-100 scale
                    current_hidden_bullish = True
        
        if len(price_peaks) >= min_swings and len(mfi_peaks) >= min_swings:
            # Regular Bearish Divergence: Price makes higher high, MFI makes lower high
            if len(price_peaks) >= 2 and len(mfi_peaks) >= 2:
                latest_price_peak = price_peaks[-1]
                prev_price_peak = price_peaks[-2]
                latest_mfi_peak = mfi_peaks[-1]
                prev_mfi_peak = mfi_peaks[-2]
                
                price_change = (latest_price_peak[1] - prev_price_peak[1]) / prev_price_peak[1]
                mfi_change = (latest_mfi_peak[1] - prev_mfi_peak[1]) / 100.0  # Normalize to 0-1 scale
                
                if (price_change > min_change and mfi_change < -min_change * 0.1):  # 0.1 = 10% of 0-100 scale
                    current_bearish = True
            
            # Hidden Bearish Divergence: Price makes lower high, MFI makes higher high
            if len(price_peaks) >= 2 and len(mfi_peaks) >= 2:
                latest_price_peak = price_peaks[-1]
                prev_price_peak = price_peaks[-2]
                latest_mfi_peak = mfi_peaks[-1]
                prev_mfi_peak = mfi_peaks[-2]
                
                price_change = (latest_price_peak[1] - prev_price_peak[1]) / prev_price_peak[1]
                mfi_change = (latest_mfi_peak[1] - prev_mfi_peak[1]) / 100.0  # Normalize to 0-1 scale
                
                if (price_change < -min_change and mfi_change > min_change * 0.1):  # 0.1 = 10% of 0-100 scale
                    current_hidden_bearish = True
        
        # Update persistence counters - only increment if current condition is met
        if current_bullish:
            bullish_persistence.iloc[i] = bullish_persistence.iloc[i-1] + 1
        else:
            bullish_persistence.iloc[i] = 0
            
        if current_bearish:
            bearish_persistence.iloc[i] = bearish_persistence.iloc[i-1] + 1
        else:
            bearish_persistence.iloc[i] = 0
            
        if current_hidden_bullish:
            hidden_bullish_persistence.iloc[i] = hidden_bullish_persistence.iloc[i-1] + 1
        else:
            hidden_bullish_persistence.iloc[i] = 0
            
        if current_hidden_bearish:
            hidden_bearish_persistence.iloc[i] = hidden_bearish_persistence.iloc[i-1] + 1
        else:
            hidden_bearish_persistence.iloc[i] = 0
        
        # Confirm signals only after persistence requirement AND only for the current bar
        # This ensures divergence is only true when conditions are actually met
        bullish_div.iloc[i] = current_bullish and bullish_persistence.iloc[i] >= persistence_bars
        bearish_div.iloc[i] = current_bearish and bearish_persistence.iloc[i] >= persistence_bars
        hidden_bullish_div.iloc[i] = current_hidden_bullish and hidden_bullish_persistence.iloc[i] >= persistence_bars
        hidden_bearish_div.iloc[i] = current_hidden_bearish and hidden_bearish_persistence.iloc[i] >= persistence_bars
    
    return bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div


def atr_divergence(close: pd.Series, atr: pd.Series, lookback: int = 20, min_swings: int = 2, 
                  min_change: float = 0.02, persistence_bars: int = 3) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Detect ATR Divergence - when price makes new extremes but ATR (volatility) doesn't confirm.
    
    ATR Divergence Types:
    - Regular Bullish: Price makes lower low, ATR makes higher low (decreasing volatility at lower prices)
    - Regular Bearish: Price makes higher high, ATR makes lower high (decreasing volatility at higher prices)
    - Hidden Bullish: Price makes higher low, ATR makes lower low (increasing volatility at higher lows)
    - Hidden Bearish: Price makes lower high, ATR makes higher high (increasing volatility at lower highs)
    
    Args:
        close: Series of closing prices
        atr: Series of ATR values
        lookback: Number of bars to look back for swing analysis
        min_swings: Minimum number of swings required for divergence
        min_change: Minimum price change for significant swing (0.01-0.1)
        persistence_bars: Number of bars to maintain signal after detection
    
    Returns:
        Tuple of (bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div)
    """
    if len(close) < lookback or len(atr) < lookback:
        return pd.Series(False, index=close.index), pd.Series(False, index=close.index), pd.Series(False, index=close.index), pd.Series(False, index=close.index)
    
    # Normalize ATR to 0-100 scale for divergence detection
    atr_normalized = ((atr - atr.rolling(50).min()) / (atr.rolling(50).max() - atr.rolling(50).min()) * 100).fillna(50)
    
    # Initialize output series
    bullish_div = pd.Series(False, index=close.index)
    bearish_div = pd.Series(False, index=close.index)
    hidden_bullish_div = pd.Series(False, index=close.index)
    hidden_bearish_div = pd.Series(False, index=close.index)
    
    # Persistence tracking
    bullish_persistence = pd.Series(0, index=close.index)
    bearish_persistence = pd.Series(0, index=close.index)
    hidden_bullish_persistence = pd.Series(0, index=close.index)
    hidden_bearish_persistence = pd.Series(0, index=close.index)
    
    for i in range(lookback, len(close)):
        # Get recent data for swing analysis
        recent_close = close.iloc[i-lookback:i+1]
        recent_atr = atr_normalized.iloc[i-lookback:i+1]
        
        # Find peaks and troughs in price
        price_peaks = []
        price_troughs = []
        atr_peaks = []
        atr_troughs = []
        
        for j in range(1, len(recent_close) - 1):
            # Price peaks (local maxima)
            if (recent_close.iloc[j] > recent_close.iloc[j-1] and 
                recent_close.iloc[j] > recent_close.iloc[j+1]):
                price_peaks.append((j, recent_close.iloc[j]))
            
            # Price troughs (local minima)
            if (recent_close.iloc[j] < recent_close.iloc[j-1] and 
                recent_close.iloc[j] < recent_close.iloc[j+1]):
                price_troughs.append((j, recent_close.iloc[j]))
            
            # ATR peaks (local maxima)
            if (recent_atr.iloc[j] > recent_atr.iloc[j-1] and 
                recent_atr.iloc[j] > recent_atr.iloc[j+1]):
                atr_peaks.append((j, recent_atr.iloc[j]))
            
            # ATR troughs (local minima)
            if (recent_atr.iloc[j] < recent_atr.iloc[j-1] and 
                recent_atr.iloc[j] < recent_atr.iloc[j+1]):
                atr_troughs.append((j, recent_atr.iloc[j]))
        
        # Need at least min_swings for divergence analysis
        if len(price_peaks) < min_swings or len(price_troughs) < min_swings:
            continue
        
        # Regular Bullish Divergence: Price lower low, ATR higher low
        if len(price_troughs) >= 2 and len(atr_troughs) >= 2:
            recent_troughs = price_troughs[-2:]
            recent_atr_troughs = atr_troughs[-2:]
            
            if (recent_troughs[1][1] < recent_troughs[0][1] and  # Price lower low
                recent_atr_troughs[1][1] > recent_atr_troughs[0][1] and  # ATR higher low
                abs(recent_troughs[1][1] - recent_troughs[0][1]) / recent_troughs[0][1] >= min_change):  # Significant change
                bullish_persistence.iloc[i] = bullish_persistence.iloc[i-1] + 1
            else:
                bullish_persistence.iloc[i] = 0
        
        # Regular Bearish Divergence: Price higher high, ATR lower high
        if len(price_peaks) >= 2 and len(atr_peaks) >= 2:
            recent_peaks = price_peaks[-2:]
            recent_atr_peaks = atr_peaks[-2:]
            
            if (recent_peaks[1][1] > recent_peaks[0][1] and  # Price higher high
                recent_atr_peaks[1][1] < recent_atr_peaks[0][1] and  # ATR lower high
                abs(recent_peaks[1][1] - recent_peaks[0][1]) / recent_peaks[0][1] >= min_change):  # Significant change
                bearish_persistence.iloc[i] = bearish_persistence.iloc[i-1] + 1
            else:
                bearish_persistence.iloc[i] = 0
        
        # Hidden Bullish Divergence: Price higher low, ATR lower low
        if len(price_troughs) >= 2 and len(atr_troughs) >= 2:
            recent_troughs = price_troughs[-2:]
            recent_atr_troughs = atr_troughs[-2:]
            
            if (recent_troughs[1][1] > recent_troughs[0][1] and  # Price higher low
                recent_atr_troughs[1][1] < recent_atr_troughs[0][1] and  # ATR lower low
                abs(recent_troughs[1][1] - recent_troughs[0][1]) / recent_troughs[0][1] >= min_change):  # Significant change
                hidden_bullish_persistence.iloc[i] = hidden_bullish_persistence.iloc[i-1] + 1
            else:
                hidden_bullish_persistence.iloc[i] = 0
        
        # Hidden Bearish Divergence: Price lower high, ATR higher high
        if len(price_peaks) >= 2 and len(atr_peaks) >= 2:
            recent_peaks = price_peaks[-2:]
            recent_atr_peaks = atr_peaks[-2:]
            
            if (recent_peaks[1][1] < recent_peaks[0][1] and  # Price lower high
                recent_atr_peaks[1][1] > recent_atr_peaks[0][1] and  # ATR higher high
                abs(recent_peaks[1][1] - recent_peaks[0][1]) / recent_peaks[0][1] >= min_change):  # Significant change
                hidden_bearish_persistence.iloc[i] = hidden_bearish_persistence.iloc[i-1] + 1
            else:
                hidden_bearish_persistence.iloc[i] = 0
        
        # Check current divergence conditions
        current_bullish = bullish_persistence.iloc[i] > 0
        current_bearish = bearish_persistence.iloc[i] > 0
        current_hidden_bullish = hidden_bullish_persistence.iloc[i] > 0
        current_hidden_bearish = hidden_bearish_persistence.iloc[i] > 0
        
        # Apply persistence logic - signals only persist as long as conditions are met
        # This ensures divergence is only true when conditions are actually met
        bullish_div.iloc[i] = current_bullish and bullish_persistence.iloc[i] >= persistence_bars
        bearish_div.iloc[i] = current_bearish and bearish_persistence.iloc[i] >= persistence_bars
        hidden_bullish_div.iloc[i] = current_hidden_bullish and hidden_bullish_persistence.iloc[i] >= persistence_bars
        hidden_bearish_div.iloc[i] = current_hidden_bearish and hidden_bearish_persistence.iloc[i] >= persistence_bars
    
    return bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div


def adx_divergence(close: pd.Series, adx: pd.Series, lookback: int = 20, min_swings: int = 2, 
                  min_change: float = 0.02, persistence_bars: int = 3) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Detect ADX Divergence - when price makes new extremes but ADX (trend strength) doesn't confirm.
    
    ADX Divergence Types:
    - Regular Bullish: Price makes lower low, ADX makes higher low (increasing trend strength at lower prices)
    - Regular Bearish: Price makes higher high, ADX makes lower high (decreasing trend strength at higher prices)
    - Hidden Bullish: Price makes higher low, ADX makes lower low (decreasing trend strength at higher lows)
    - Hidden Bearish: Price makes lower high, ADX makes higher high (increasing trend strength at lower highs)
    
    Args:
        close: Series of closing prices
        adx: Series of ADX values (0-100 scale)
        lookback: Number of bars to look back for swing analysis
        min_swings: Minimum number of swings required for divergence
        min_change: Minimum price change for significant swing (0.01-0.1)
        persistence_bars: Number of bars to maintain signal after detection
    
    Returns:
        Tuple of (bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div)
    """
    if len(close) < lookback or len(adx) < lookback:
        return pd.Series(False, index=close.index), pd.Series(False, index=close.index), pd.Series(False, index=close.index), pd.Series(False, index=close.index)
    
    # ADX is already on 0-100 scale, no normalization needed
    adx_normalized = adx.fillna(50)  # Fill NaN with neutral ADX value
    
    # Initialize output series
    bullish_div = pd.Series(False, index=close.index)
    bearish_div = pd.Series(False, index=close.index)
    hidden_bullish_div = pd.Series(False, index=close.index)
    hidden_bearish_div = pd.Series(False, index=close.index)
    
    # Persistence tracking
    bullish_persistence = pd.Series(0, index=close.index)
    bearish_persistence = pd.Series(0, index=close.index)
    hidden_bullish_persistence = pd.Series(0, index=close.index)
    hidden_bearish_persistence = pd.Series(0, index=close.index)
    
    for i in range(lookback, len(close)):
        # Get recent data for swing analysis
        recent_close = close.iloc[i-lookback:i+1]
        recent_adx = adx_normalized.iloc[i-lookback:i+1]
        
        # Find peaks and troughs in price
        price_peaks = []
        price_troughs = []
        adx_peaks = []
        adx_troughs = []
        
        for j in range(1, len(recent_close) - 1):
            # Price peaks (local maxima)
            if (recent_close.iloc[j] > recent_close.iloc[j-1] and 
                recent_close.iloc[j] > recent_close.iloc[j+1]):
                price_peaks.append((j, recent_close.iloc[j]))
            
            # Price troughs (local minima)
            if (recent_close.iloc[j] < recent_close.iloc[j-1] and 
                recent_close.iloc[j] < recent_close.iloc[j+1]):
                price_troughs.append((j, recent_close.iloc[j]))
            
            # ADX peaks (local maxima)
            if (recent_adx.iloc[j] > recent_adx.iloc[j-1] and 
                recent_adx.iloc[j] > recent_adx.iloc[j+1]):
                adx_peaks.append((j, recent_adx.iloc[j]))
            
            # ADX troughs (local minima)
            if (recent_adx.iloc[j] < recent_adx.iloc[j-1] and 
                recent_adx.iloc[j] < recent_adx.iloc[j+1]):
                adx_troughs.append((j, recent_adx.iloc[j]))
        
        # Need at least min_swings for divergence analysis
        if len(price_peaks) < min_swings or len(price_troughs) < min_swings:
            continue
        
        # Regular Bullish Divergence: Price lower low, ADX higher low
        if len(price_troughs) >= 2 and len(adx_troughs) >= 2:
            recent_troughs = price_troughs[-2:]
            recent_adx_troughs = adx_troughs[-2:]
            
            if (recent_troughs[1][1] < recent_troughs[0][1] and  # Price lower low
                recent_adx_troughs[1][1] > recent_adx_troughs[0][1] and  # ADX higher low
                abs(recent_troughs[1][1] - recent_troughs[0][1]) / recent_troughs[0][1] >= min_change):  # Significant change
                bullish_persistence.iloc[i] = bullish_persistence.iloc[i-1] + 1
            else:
                bullish_persistence.iloc[i] = 0
        
        # Regular Bearish Divergence: Price higher high, ADX lower high
        if len(price_peaks) >= 2 and len(adx_peaks) >= 2:
            recent_peaks = price_peaks[-2:]
            recent_adx_peaks = adx_peaks[-2:]
            
            if (recent_peaks[1][1] > recent_peaks[0][1] and  # Price higher high
                recent_adx_peaks[1][1] < recent_adx_peaks[0][1] and  # ADX lower high
                abs(recent_peaks[1][1] - recent_peaks[0][1]) / recent_peaks[0][1] >= min_change):  # Significant change
                bearish_persistence.iloc[i] = bearish_persistence.iloc[i-1] + 1
            else:
                bearish_persistence.iloc[i] = 0
        
        # Hidden Bullish Divergence: Price higher low, ADX lower low
        if len(price_troughs) >= 2 and len(adx_troughs) >= 2:
            recent_troughs = price_troughs[-2:]
            recent_adx_troughs = adx_troughs[-2:]
            
            if (recent_troughs[1][1] > recent_troughs[0][1] and  # Price higher low
                recent_adx_troughs[1][1] < recent_adx_troughs[0][1] and  # ADX lower low
                abs(recent_troughs[1][1] - recent_troughs[0][1]) / recent_troughs[0][1] >= min_change):  # Significant change
                hidden_bullish_persistence.iloc[i] = hidden_bullish_persistence.iloc[i-1] + 1
            else:
                hidden_bullish_persistence.iloc[i] = 0
        
        # Hidden Bearish Divergence: Price lower high, ADX higher high
        if len(price_peaks) >= 2 and len(adx_peaks) >= 2:
            recent_peaks = price_peaks[-2:]
            recent_adx_peaks = adx_peaks[-2:]
            
            if (recent_peaks[1][1] < recent_peaks[0][1] and  # Price lower high
                recent_adx_peaks[1][1] > recent_adx_peaks[0][1] and  # ADX higher high
                abs(recent_peaks[1][1] - recent_peaks[0][1]) / recent_peaks[0][1] >= min_change):  # Significant change
                hidden_bearish_persistence.iloc[i] = hidden_bearish_persistence.iloc[i-1] + 1
            else:
                hidden_bearish_persistence.iloc[i] = 0
        
        # Check current divergence conditions
        current_bullish = bullish_persistence.iloc[i] > 0
        current_bearish = bearish_persistence.iloc[i] > 0
        current_hidden_bullish = hidden_bullish_persistence.iloc[i] > 0
        current_hidden_bearish = hidden_bearish_persistence.iloc[i] > 0
        
        # Apply persistence logic - signals only persist as long as conditions are met
        # This ensures divergence is only true when conditions are actually met
        bullish_div.iloc[i] = current_bullish and bullish_persistence.iloc[i] >= persistence_bars
        bearish_div.iloc[i] = current_bearish and bearish_persistence.iloc[i] >= persistence_bars
        hidden_bullish_div.iloc[i] = current_hidden_bullish and hidden_bullish_persistence.iloc[i] >= persistence_bars
        hidden_bearish_div.iloc[i] = current_hidden_bearish and hidden_bearish_persistence.iloc[i] >= persistence_bars
    
    return bullish_div, bearish_div, hidden_bullish_div, hidden_bearish_div


def atr_channels(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20, multiplier: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate ATR Channels.
    
    ATR Channels are volatility-based indicators that use ATR with EMA for dynamic
    support/resistance levels. They consist of three lines: upper channel, middle 
    channel (EMA), and lower channel.
    
    Upper Channel = EMA + (ATR × multiplier)
    Middle Channel = EMA
    Lower Channel = EMA - (ATR × multiplier)
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: EMA and ATR period (default 20)
        multiplier: ATR multiplier (default 2.0)
    
    Returns:
        Tuple of (upper_channel, middle_channel, lower_channel)
    """
    # Calculate EMA (middle channel)
    middle_channel = ema(close, period)
    
    # Calculate ATR
    tr = true_range(high, low, close)
    atr = tr.rolling(period).mean()
    
    # Calculate upper and lower channels
    upper_channel = middle_channel + (atr * multiplier)
    lower_channel = middle_channel - (atr * multiplier)
    
    return upper_channel, middle_channel, lower_channel


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tr = true_range(df["High"], df["Low"], df["Close"]) 
    return tr.rolling(period).mean()


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    plus_dm = (high.diff()).clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)
    plus_dm[plus_dm < minus_dm] = 0
    minus_dm[minus_dm < plus_dm] = 0

    tr = true_range(high, low, close)
    atr_smooth = tr.rolling(period).mean()
    plus_di = (plus_dm.rolling(period).mean() / atr_smooth) * 100
    minus_di = (minus_dm.rolling(period).mean() / atr_smooth) * 100
    dx = (plus_di.subtract(minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    adx_val = dx.rolling(period).mean()
    return adx_val.fillna(0)


def donchian(df: pd.DataFrame, period: int = 20) -> Tuple[pd.Series, pd.Series]:
    upper = df["High"].rolling(period).max()
    lower = df["Low"].rolling(period).min()
    return upper, lower


def zscore(series: pd.Series, period: int = 20) -> pd.Series:
    mean = series.rolling(period).mean()
    std = series.rolling(period).std()
    return (series - mean) / std.replace(0, np.nan)


def volume_sma_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
    vsma = volume.rolling(period).mean()
    return volume / vsma.replace(0, np.nan)


def session_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Session VWAP (resets each trading day). Uses typical price.
    Works for intraday intervals by grouping on calendar date.
    """
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
    volume = df["Volume"].fillna(0)
    # Ensure index is DatetimeIndex and normalize to date
    if isinstance(df.index, pd.DatetimeIndex):
        # If timezone-aware, convert to naive or extract date properly
        if df.index.tz is not None:
            df_index = df.index.tz_localize(None) if df.index.tz is not None else df.index
        else:
            df_index = df.index
        by_day = pd.Series(df_index.date, index=df.index)
    else:
        # Fallback: try to convert to datetime
        df_index = pd.to_datetime(df.index, utc=True).tz_localize(None)
        by_day = pd.Series(df_index.date, index=df.index)
    cum_pv = (typical_price * volume).groupby(by_day).cumsum()
    cum_v = volume.groupby(by_day).cumsum().replace(0, np.nan)
    vwap = cum_pv / cum_v
    return vwap


def bullish_engulfing(df: pd.DataFrame) -> pd.Series:
    o, c = df["Open"], df["Close"]
    prev_o, prev_c = o.shift(1), c.shift(1)
    return (prev_c < prev_o) & (c > o) & (c >= prev_o) & (o <= prev_c)


def bearish_engulfing(df: pd.DataFrame) -> pd.Series:
    o, c = df["Open"], df["Close"]
    prev_o, prev_c = o.shift(1), c.shift(1)
    return (prev_c > prev_o) & (c < o) & (c <= prev_o) & (o >= prev_c)


# ----------------------------
# Strategy logic
# ----------------------------
def build_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Trend
    out["ema_fast"] = ema(out["Close"], 12)
    out["ema_slow"] = ema(out["Close"], 26)
    
    # Kalman Moving Average (adaptive moving average using Kalman filter)
    out["kalman_ma"] = kalman_ma(
        out["Close"],
        out["High"],
        out["Low"],
        base_q=0.0001,
        base_r=0.01,
        use_adapt=True,
        atr_len=14,
        std_len=20,
        vol_blend=0.5,
        q_scale=2.0,
        r_scale=2.0,
        vol_floor=0.0005,
    )
    
    # Parabolic SAR (trend-following stop and reverse)
    out["psar"] = parabolic_sar(out["High"], out["Low"], out["Close"], acceleration=0.02, maximum=0.2)
    
    # Ichimoku Cloud (comprehensive trend analysis system)
    tenkan, kijun, senkou_a, senkou_b, chikou, cloud_upper, cloud_lower = ichimoku_cloud(out["High"], out["Low"], out["Close"], tenkan_period=9, kijun_period=26, senkou_b_period=52, displacement=26)
    out["tenkan"] = tenkan
    out["kijun"] = kijun
    out["senkou_a"] = senkou_a
    out["senkou_b"] = senkou_b
    out["chikou"] = chikou
    out["cloud_upper"] = cloud_upper
    out["cloud_lower"] = cloud_lower
    out["cloud_thickness"] = (cloud_upper - cloud_lower) / out["Close"]  # Normalized cloud thickness

    # Momentum
    out["rsi"] = rsi(out["Close"], 14)
    # RSI Divergence (price vs RSI divergence analysis)
    rsi_bullish_div, rsi_bearish_div, rsi_hidden_bullish_div, rsi_hidden_bearish_div = rsi_divergence(out["Close"], out["rsi"], lookback=20, min_swings=2, min_change=0.02, persistence_bars=3)
    out["rsi_bullish_div"] = rsi_bullish_div
    out["rsi_bearish_div"] = rsi_bearish_div
    out["rsi_hidden_bullish_div"] = rsi_hidden_bullish_div
    out["rsi_hidden_bearish_div"] = rsi_hidden_bearish_div
    out["stoch_rsi"] = stochastic_rsi(out["Close"], rsi_period=14, stoch_period=14, k_period=3)
    # Stochastic RSI Divergence (price vs Stochastic RSI divergence analysis)
    stoch_rsi_bullish_div, stoch_rsi_bearish_div, stoch_rsi_hidden_bullish_div, stoch_rsi_hidden_bearish_div = stoch_rsi_divergence(out["Close"], out["stoch_rsi"], lookback=20, min_swings=2, min_change=0.02, persistence_bars=3)
    out["stoch_rsi_bullish_div"] = stoch_rsi_bullish_div
    out["stoch_rsi_bearish_div"] = stoch_rsi_bearish_div
    out["stoch_rsi_hidden_bullish_div"] = stoch_rsi_hidden_bullish_div
    out["stoch_rsi_hidden_bearish_div"] = stoch_rsi_hidden_bearish_div
    
    # MACD (trend momentum)
    macd_line, macd_signal, macd_histogram = macd(out["Close"], fast_period=12, slow_period=26, signal_period=9)
    out["macd_line"] = macd_line
    out["macd_signal"] = macd_signal
    out["macd_histogram"] = macd_histogram
    # MACD Divergence (price vs MACD divergence analysis)
    macd_bullish_div, macd_bearish_div, macd_hidden_bullish_div, macd_hidden_bearish_div = macd_divergence(out["Close"], out["macd_line"], out["macd_histogram"], lookback=20, min_swings=2, min_change=0.02, persistence_bars=3)
    out["macd_bullish_div"] = macd_bullish_div
    out["macd_bearish_div"] = macd_bearish_div
    out["macd_hidden_bullish_div"] = macd_hidden_bullish_div
    out["macd_hidden_bearish_div"] = macd_hidden_bearish_div
    
    # Williams %R (momentum oscillator)
    out["williams_r"] = williams_r(out["High"], out["Low"], out["Close"], period=14)
    # Williams %R Divergence (price vs Williams %R divergence analysis)
    # Normalize W%R (-100..0) to Stoch-like (0..100): stoch_like = 100 + williams_r
    wpr_stoch_like = 100 + out["williams_r"].clip(-100, 0)
    wpr_bullish_div, wpr_bearish_div, wpr_hidden_bullish_div, wpr_hidden_bearish_div = stoch_rsi_divergence(
        out["Close"], wpr_stoch_like, lookback=20, min_swings=2, min_change=0.02, persistence_bars=3
    )
    out["wpr_bullish_div"] = wpr_bullish_div
    out["wpr_bearish_div"] = wpr_bearish_div
    out["wpr_hidden_bullish_div"] = wpr_hidden_bullish_div
    out["wpr_hidden_bearish_div"] = wpr_hidden_bearish_div
    
    # CCI (Commodity Channel Index - momentum oscillator)
    out["cci"] = cci(out["High"], out["Low"], out["Close"], period=20)
    # CCI Divergence (price vs CCI divergence analysis)
    cci_bullish_div, cci_bearish_div, cci_hidden_bullish_div, cci_hidden_bearish_div = cci_divergence(out["Close"], out["cci"], lookback=20, min_swings=2, min_change=0.02, persistence_bars=3)
    out["cci_bullish_div"] = cci_bullish_div
    out["cci_bearish_div"] = cci_bearish_div
    out["cci_hidden_bullish_div"] = cci_hidden_bullish_div
    out["cci_hidden_bearish_div"] = cci_hidden_bearish_div
    
    # MFI (Money Flow Index - volume-weighted momentum oscillator)
    out["mfi"] = mfi(out["High"], out["Low"], out["Close"], out["Volume"], period=14)
    # MFI Divergence (price vs MFI divergence analysis)
    mfi_bullish_div, mfi_bearish_div, mfi_hidden_bullish_div, mfi_hidden_bearish_div = mfi_divergence(out["Close"], out["mfi"], lookback=20, min_swings=2, min_change=0.02, persistence_bars=3)
    out["mfi_bullish_div"] = mfi_bullish_div
    out["mfi_bearish_div"] = mfi_bearish_div
    out["mfi_hidden_bullish_div"] = mfi_hidden_bullish_div
    out["mfi_hidden_bearish_div"] = mfi_hidden_bearish_div
    
    # ROC (Rate of Change - momentum oscillator)
    out["roc"] = roc(out["Close"], period=12)
    # ROC Divergence (price vs ROC divergence analysis)
    # ROC can be positive or negative; normalize to 0..100 for divergence detection
    # Map ROC range (-50 to +50) to (0 to 100): normalized = (roc + 50) * 100 / 100
    roc_normalized = ((out["roc"].clip(-50, 50) + 50) * 100 / 100).clip(0, 100)
    roc_bullish_div, roc_bearish_div, roc_hidden_bullish_div, roc_hidden_bearish_div = stoch_rsi_divergence(
        out["Close"], roc_normalized, lookback=20, min_swings=2, min_change=0.02, persistence_bars=3
    )
    out["roc_bullish_div"] = roc_bullish_div
    out["roc_bearish_div"] = roc_bearish_div
    out["roc_hidden_bullish_div"] = roc_hidden_bullish_div
    out["roc_hidden_bearish_div"] = roc_hidden_bearish_div

    # Volatility
    out["atr"] = atr(out, 14)
    out["atr_sma20"] = out["atr"].rolling(20).mean()
    
    # Bollinger Bands (volatility-based support/resistance)
    bb_middle, bb_upper, bb_lower = bollinger_bands(out["Close"], window=20, k=2.0)
    out["bb_middle"] = bb_middle
    out["bb_upper"] = bb_upper
    out["bb_lower"] = bb_lower
    out["bb_width"] = (bb_upper - bb_lower) / bb_middle  # Normalized width
    out["bb_percent"] = (out["Close"] - bb_lower) / (bb_upper - bb_lower)  # %B indicator
    # Bollinger Band Width Divergence (price vs BB width divergence analysis)
    # Smooth BB width to reduce noise for better divergence detection
    bb_width_smooth = out["bb_width"].rolling(window=3, min_periods=1).mean()
    # Normalize BB width to 0-100 scale for divergence detection
    bb_width_min = bb_width_smooth.rolling(window=50, min_periods=20).min()
    bb_width_max = bb_width_smooth.rolling(window=50, min_periods=20).max()
    bb_width_normalized = ((bb_width_smooth - bb_width_min) / (bb_width_max - bb_width_min + 1e-8) * 100).clip(0, 100)
    bb_bullish_div, bb_bearish_div, bb_hidden_bullish_div, bb_hidden_bearish_div = stoch_rsi_divergence(
        out["Close"], bb_width_normalized, lookback=20, min_swings=2, min_change=0.02, persistence_bars=3
    )
    out["bb_bullish_div"] = bb_bullish_div
    out["bb_bearish_div"] = bb_bearish_div
    out["bb_hidden_bullish_div"] = bb_hidden_bullish_div
    out["bb_hidden_bearish_div"] = bb_hidden_bearish_div
    
    # Keltner Channels (volatility-based support/resistance using ATR)
    kc_upper, kc_middle, kc_lower = keltner_channels(out["High"], out["Low"], out["Close"], period=20, multiplier=2.0)
    out["kc_upper"] = kc_upper
    out["kc_middle"] = kc_middle
    out["kc_lower"] = kc_lower
    out["kc_width"] = (kc_upper - kc_lower) / kc_middle  # Normalized width
    out["kc_percent"] = (out["Close"] - kc_lower) / (kc_upper - kc_lower)  # %K indicator
    
    # ATR Channels (volatility-based support/resistance using ATR with EMA)
    atr_upper, atr_middle, atr_lower = atr_channels(out["High"], out["Low"], out["Close"], period=20, multiplier=2.0)
    out["atr_upper"] = atr_upper
    out["atr_middle"] = atr_middle
    out["atr_lower"] = atr_lower
    out["atr_width"] = (atr_upper - atr_lower) / atr_middle  # Normalized width
    out["atr_percent"] = (out["Close"] - atr_lower) / (atr_upper - atr_lower)  # %A indicator

    # Volume
    out["vol_ratio"] = volume_sma_ratio(out["Volume"], 20)
    # VWAP (daily session)
    out["vwap"] = session_vwap(out)
    # OBV (On-Balance Volume - cumulative volume flow)
    out["obv"] = on_balance_volume(out["Close"], out["Volume"], period=14)
    # OBV Divergence (price vs OBV divergence analysis)
    # OBV is cumulative and can have large absolute values; normalize using rolling min/max for divergence detection
    obv_rolling_min = out["obv"].rolling(window=50, min_periods=20).min()
    obv_rolling_max = out["obv"].rolling(window=50, min_periods=20).max()
    obv_normalized = ((out["obv"] - obv_rolling_min) / (obv_rolling_max - obv_rolling_min + 1e-8) * 100).clip(0, 100)
    obv_bullish_div, obv_bearish_div, obv_hidden_bullish_div, obv_hidden_bearish_div = stoch_rsi_divergence(
        out["Close"], obv_normalized, lookback=20, min_swings=2, min_change=0.02, persistence_bars=3
    )
    out["obv_bullish_div"] = obv_bullish_div
    out["obv_bearish_div"] = obv_bearish_div
    out["obv_hidden_bullish_div"] = obv_hidden_bullish_div
    out["obv_hidden_bearish_div"] = obv_hidden_bearish_div
    # Volume Profile (HVN/LVN analysis)
    hvn_strength, lvn_strength, vwap_deviation, volume_trend = volume_profile(out, lookback=20, volume_threshold=1.5)
    out["hvn_strength"] = hvn_strength
    out["lvn_strength"] = lvn_strength
    out["vwap_deviation"] = vwap_deviation
    out["volume_trend"] = volume_trend
    # VROC (Volume Rate of Change - volume momentum)
    vroc, vroc_sma, vroc_momentum = volume_rate_of_change(out["Volume"], period=10)
    out["vroc"] = vroc
    out["vroc_sma"] = vroc_sma
    out["vroc_momentum"] = vroc_momentum
    # VROC Divergence (price vs VROC divergence analysis)
    # VROC can be positive or negative; normalize to 0..100 for divergence detection
    # Map VROC range (-50 to +50) to (0 to 100): normalized = (vroc + 50) * 100 / 100
    vroc_normalized = ((out["vroc"].clip(-50, 50) + 50) * 100 / 100).clip(0, 100)
    vroc_bullish_div, vroc_bearish_div, vroc_hidden_bullish_div, vroc_hidden_bearish_div = stoch_rsi_divergence(
        out["Close"], vroc_normalized, lookback=20, min_swings=2, min_change=0.02, persistence_bars=3
    )
    out["vroc_bullish_div"] = vroc_bullish_div
    out["vroc_bearish_div"] = vroc_bearish_div
    out["vroc_hidden_bullish_div"] = vroc_hidden_bullish_div
    out["vroc_hidden_bearish_div"] = vroc_hidden_bearish_div

    # ATR Divergence (price vs ATR volatility divergence analysis)
    # ATR divergence detects when price makes new extremes but volatility doesn't confirm
    atr_bullish_div, atr_bearish_div, atr_hidden_bullish_div, atr_hidden_bearish_div = atr_divergence(
        out["Close"], out["atr"], lookback=20, min_swings=2, min_change=0.02, persistence_bars=3
    )
    out["atr_bullish_div"] = atr_bullish_div
    out["atr_bearish_div"] = atr_bearish_div
    out["atr_hidden_bullish_div"] = atr_hidden_bullish_div
    out["atr_hidden_bearish_div"] = atr_hidden_bearish_div

    # Multi-dimensional (trend strength)
    out["adx"] = adx(out, 14)

    # ADX Divergence (price vs ADX trend strength divergence analysis)
    # ADX divergence detects when price makes new extremes but trend strength doesn't confirm
    adx_bullish_div, adx_bearish_div, adx_hidden_bullish_div, adx_hidden_bearish_div = adx_divergence(
        out["Close"], out["adx"], lookback=20, min_swings=2, min_change=0.02, persistence_bars=3
    )
    out["adx_bullish_div"] = adx_bullish_div
    out["adx_bearish_div"] = adx_bearish_div
    out["adx_hidden_bullish_div"] = adx_hidden_bullish_div
    out["adx_hidden_bearish_div"] = adx_hidden_bearish_div

    # Parabola Detection (mathematical curve fitting for parabolic patterns)
    parabola_bullish_end, parabola_bearish_end, parabola_confidence, parabola_active = parabola_detector(
        out["Close"], lookback=50, confidence_threshold=0.70, deviation_threshold=0.02,
        use_atr_filter=True, use_adx_filter=True, atr_period=14, adx_period=14,
        adx_threshold=15, atr_threshold=0.3, persistence_bars=3
    )
    out["parabola_bullish_end"] = parabola_bullish_end  # SHORT signal (end of bullish parabola)
    out["parabola_bearish_end"] = parabola_bearish_end  # LONG signal (end of bearish parabola)
    out["parabola_confidence"] = parabola_confidence
    out["parabola_active"] = parabola_active

    # SuperTrend (ATR-based trend/stop indicator)
    st_line, st_dir = supertrend(out, atr_period=10, multiplier=3.0)
    out["supertrend_line"] = st_line
    out["supertrend_dir"] = st_dir  # +1 bullish, -1 bearish
    # SuperTrend Slope Divergence (price vs SuperTrend slope divergence analysis)
    # Calculate SuperTrend slope using rolling regression for smooth trend detection
    st_slope = out["supertrend_line"].rolling(window=5, min_periods=3).apply(
        lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0, raw=False
    )
    # Normalize slope to 0-100 scale for divergence detection
    st_slope_min = st_slope.rolling(window=50, min_periods=20).min()
    st_slope_max = st_slope.rolling(window=50, min_periods=20).max()
    st_slope_normalized = ((st_slope - st_slope_min) / (st_slope_max - st_slope_min + 1e-8) * 100).clip(0, 100)
    st_bullish_div, st_bearish_div, st_hidden_bullish_div, st_hidden_bearish_div = stoch_rsi_divergence(
        out["Close"], st_slope_normalized, lookback=20, min_swings=2, min_change=0.02, persistence_bars=3
    )
    out["st_bullish_div"] = st_bullish_div
    out["st_bearish_div"] = st_bearish_div
    out["st_hidden_bullish_div"] = st_hidden_bullish_div
    out["st_hidden_bearish_div"] = st_hidden_bearish_div

    # VIX Rate of Change (market fear/volatility indicator)
    # Rising VIX = fear/uncertainty (bearish), Falling VIX = complacency/confidence (bullish)
    try:
        # Get date range from dataframe index
        start_date = out.index.min().strftime("%Y-%m-%d") if not out.empty else None
        end_date = out.index.max().strftime("%Y-%m-%d") if not out.empty else None
        
        if start_date and end_date:
            # Determine interval for VIX fetch (match main dataframe interval)
            vix_interval = "1d"  # VIX is typically daily, but we'll try to match
            if hasattr(out.index, 'freq') or len(out) > 0:
                # Estimate interval from data frequency
                if len(out) > 1:
                    time_diff = (out.index[1] - out.index[0]).total_seconds() / 3600
                    if time_diff < 2:
                        vix_interval = "1h"
                    else:
                        vix_interval = "1d"
            
            # Fetch VIX data
            vix_series = fetch_vix_data(start_date, end_date, interval=vix_interval)
            
            if not vix_series.empty:
                # Align VIX data with main dataframe index
                # Convert both indices to timezone-naive for alignment
                vix_index = vix_series.index
                if hasattr(vix_index, 'tz') and vix_index.tz is not None:
                    vix_index = vix_index.tz_localize(None)
                
                main_index = out.index
                if hasattr(main_index, 'tz') and main_index.tz is not None:
                    main_index = main_index.tz_localize(None)
                
                # Create aligned series with forward fill for missing dates
                vix_df = pd.DataFrame({'vix': vix_series.values}, index=vix_index)
                vix_aligned = vix_df.reindex(main_index).ffill()['vix']
                
                # Calculate VIX Rate of Change (percentage change over period)
                vix_roc_period = 5  # 5-period ROC for VIX
                vix_roc = roc(vix_aligned, period=vix_roc_period)
                out["vix"] = vix_aligned
                out["vix_roc"] = vix_roc
            else:
                # If VIX fetch fails, create empty series
                out["vix"] = pd.Series(dtype=float, index=out.index)
                out["vix_roc"] = pd.Series(dtype=float, index=out.index)
        else:
            out["vix"] = pd.Series(dtype=float, index=out.index)
            out["vix_roc"] = pd.Series(dtype=float, index=out.index)
    except Exception as e:
        if ARGS_DEBUG:
            print(f"[VIX] Error calculating VIX ROC: {e}")
        out["vix"] = pd.Series(dtype=float, index=out.index)
        out["vix_roc"] = pd.Series(dtype=float, index=out.index)

    # Support/Resistance proxy
    out["don_upper"], out["don_lower"] = donchian(out, 20)

    # Candlestick
    out["bull_engulf"] = bullish_engulfing(out)
    out["bear_engulf"] = bearish_engulfing(out)

    # ML/Statistical
    out["z"] = zscore(out["Close"], 20)

    # Timing (day-of-week and hour in EST/New York timezone)
    # Convert to EST/EDT (America/New_York) for accurate market time
    try:
        import pytz
        ny_tz = pytz.timezone('America/New_York')
    except ImportError:
        try:
            from zoneinfo import ZoneInfo
            ny_tz = ZoneInfo('America/New_York')
        except ImportError:
            # Fallback: assume data is already in EST/EDT (typical for stock data)
            ny_tz = None
    
    if isinstance(out.index, pd.DatetimeIndex):
        # Convert to EST/New York timezone for accurate market hours
        if ny_tz is not None:
            if out.index.tz is None:
                # Timezone-naive: assume it's already in market time (EST/EDT) - common for stock data
                # But to be safe, we'll treat as UTC and convert to EST
                try:
                    est_index = out.index.tz_localize('UTC').tz_convert(ny_tz)
                except:
                    # If localization fails, assume already in EST
                    est_index = out.index
            else:
                # Timezone-aware: convert to EST
                try:
                    est_index = out.index.tz_convert(ny_tz)
                except:
                    est_index = out.index
        else:
            # No timezone library: assume data is already in EST/EDT
            est_index = out.index
        
        out["dow"] = est_index.dayofweek
        out["hour"] = est_index.hour
    else:
        # Convert to datetime if needed
        try:
            dt_index = pd.to_datetime(out.index)
            if ny_tz is not None and hasattr(dt_index, 'tz'):
                if dt_index.tz is None:
                    try:
                        est_index = dt_index.tz_localize('UTC').tz_convert(ny_tz)
                    except:
                        est_index = dt_index
                else:
                    try:
                        est_index = dt_index.tz_convert(ny_tz)
                    except:
                        est_index = dt_index
            else:
                est_index = dt_index
            out["dow"] = est_index.dayofweek if hasattr(est_index, 'dayofweek') else pd.Series([0] * len(out), index=out.index)
            out["hour"] = est_index.hour if hasattr(est_index, 'hour') else pd.Series([0] * len(out), index=out.index)
        except Exception:
            # Fallback: set to default values if conversion fails
            out["dow"] = pd.Series([0] * len(out), index=out.index)
            out["hour"] = pd.Series([0] * len(out), index=out.index)

    return out


def resample_to_higher_timeframe(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """
    Resample daily OHLCV data to higher timeframe (weekly/monthly).
    
    Args:
        df: DataFrame with OHLCV data (daily)
        freq: Pandas frequency string ('W-FRI' for weekly, 'ME' for monthly)
    
    Returns:
        Resampled DataFrame with same OHLCV structure
    """
    # Normalize 'M' to 'ME' to avoid deprecation warning
    if freq == 'M':
        freq = 'ME'
    resampled = df.resample(freq).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    return resampled


def generate_signals(
    df: pd.DataFrame,
    use_timing_filter: bool = True,
    adx_thresh: float = 22.0,  # Optimized 2026-01-21: SPY validation showed 22.0 > 20.0 (0.33% vs 0.31% avg return)
    vol_ratio_min: float = 1.1,
    z_abs_max: float = 2.0,
    rsi_buy_max: float = 65.0,
    rsi_sell_min: float = 35.0,
    atr_presence_ratio: float = 0.8,
    min_components_buy: int | None = None,
    min_components_sell: int | None = None,
    min_fraction: float = 0.6,
    vwap_buy_above: float = 1.0,
    vwap_sell_below: float = 1.0,
    bb_squeeze_thresh: float = 0.1,
    bb_bounce_thresh: float = 0.2,
    stoch_rsi_oversold: float = 20.0,
    stoch_rsi_overbought: float = 80.0,
    macd_above_zero: bool = True,
    macd_histogram_positive: bool = True,
    williams_r_oversold: float = -80.0,
    williams_r_overbought: float = -20.0,
    cci_oversold: float = -100.0,
    cci_overbought: float = 100.0,
    mfi_oversold: float = 20.0,
    mfi_overbought: float = 80.0,
    psar_above_price: bool = True,
    roc_positive: float = 0.0,
    roc_negative: float = 0.0,
    kc_squeeze_thresh: float = 0.1,
    kc_bounce_thresh: float = 0.2,
    obv_trend_thresh: float = 0.0,
    obv_divergence_thresh: float = 0.1,
    ichimoku_bullish_cloud: bool = True,
    ichimoku_bearish_cloud: bool = True,
    ichimoku_tenkan_kijun: bool = True,
    ichimoku_chikou: bool = True,
    supertrend_use: bool = True,
    supertrend_dir_required: int = 1,
    atr_channels_use: bool = True,
    atr_channels_squeeze_thresh: float = 0.1,
    atr_channels_bounce_thresh: float = 0.2,
    volume_profile_use: bool = True,
    hvn_strength_thresh: float = 0.3,
    lvn_strength_thresh: float = 0.2,
    vwap_deviation_thresh: float = 0.02,
    volume_trend_thresh: float = 0.1,
    vroc_use: bool = True,
    vroc_positive_thresh: float = 10.0,
    vroc_negative_thresh: float = -10.0,
    vroc_momentum_thresh: float = 5.0,
    rsi_divergence_use: bool = True,
    rsi_divergence_lookback: int = 20,
    rsi_divergence_min_swings: int = 2,
    rsi_divergence_min_change: float = 0.02,
    rsi_divergence_persistence_bars: int = 3,
    macd_divergence_use: bool = True,
    macd_divergence_lookback: int = 20,
    macd_divergence_min_swings: int = 2,
    macd_divergence_min_change: float = 0.02,
    macd_divergence_persistence_bars: int = 3,
    stoch_rsi_divergence_use: bool = True,
    stoch_rsi_divergence_lookback: int = 20,
    stoch_rsi_divergence_min_swings: int = 2,
    stoch_rsi_divergence_min_change: float = 0.02,
    stoch_rsi_divergence_persistence_bars: int = 3,
    cci_divergence_use: bool = True,
    cci_divergence_lookback: int = 20,
    cci_divergence_min_swings: int = 2,
    cci_divergence_min_change: float = 0.02,
    cci_divergence_persistence_bars: int = 3,
    mfi_divergence_use: bool = True,
    mfi_divergence_lookback: int = 20,
    mfi_divergence_min_swings: int = 2,
    mfi_divergence_min_change: float = 0.02,
    mfi_divergence_persistence_bars: int = 3,
    wpr_divergence_use: bool = True,
    wpr_divergence_lookback: int = 20,
    wpr_divergence_min_swings: int = 2,
    wpr_divergence_min_change: float = 0.02,
    wpr_divergence_persistence_bars: int = 3,
    roc_divergence_use: bool = True,
    roc_divergence_lookback: int = 20,
    roc_divergence_min_swings: int = 2,
    roc_divergence_min_change: float = 0.02,
    roc_divergence_persistence_bars: int = 3,
    obv_divergence_use: bool = True,
    obv_divergence_lookback: int = 20,
    obv_divergence_min_swings: int = 2,
    obv_divergence_min_change: float = 0.02,
    obv_divergence_persistence_bars: int = 3,
    st_divergence_use: bool = True,
    st_divergence_lookback: int = 20,
    st_divergence_min_swings: int = 2,
    st_divergence_min_change: float = 0.02,
    st_divergence_persistence_bars: int = 3,
    bb_divergence_use: bool = True,
    bb_divergence_lookback: int = 20,
    bb_divergence_min_swings: int = 2,
    bb_divergence_min_change: float = 0.02,
    bb_divergence_persistence_bars: int = 3,
    vroc_divergence_use: bool = True,
    vroc_divergence_lookback: int = 20,
    vroc_divergence_min_swings: int = 2,
    vroc_divergence_min_change: float = 0.02,
    vroc_divergence_persistence_bars: int = 3,
    atr_divergence_use: bool = True,
    atr_divergence_lookback: int = 20,
    atr_divergence_min_swings: int = 2,
    atr_divergence_min_change: float = 0.02,
    atr_divergence_persistence_bars: int = 3,
    adx_divergence_use: bool = True,
    adx_divergence_lookback: int = 20,
    adx_divergence_min_swings: int = 2,
    adx_divergence_min_change: float = 0.02,
    adx_divergence_persistence_bars: int = 3,
    parabola_use: bool = True,
    parabola_lookback: int = 50,
    parabola_confidence_threshold: float = 0.70,
    parabola_deviation_threshold: float = 0.02,
    parabola_use_atr_filter: bool = True,
    parabola_use_adx_filter: bool = True,
    parabola_atr_period: int = 14,
    parabola_adx_period: int = 14,
    parabola_adx_threshold: int = 15,
    parabola_atr_threshold: float = 0.3,
    parabola_persistence_bars: int = 3,
    use_mtf_confirmation: bool = True,
    mtf_weekly: bool = True,
    mtf_monthly: bool = True,
    # v11 ENHANCEMENT: Automatic threshold adjustment (non-destructive)
    auto_adjust_thresholds: bool = False,
    auto_adjust_lookback: int = 100,
    # v11 ENHANCEMENT: Improved exit logic (non-destructive)
    use_improved_exits: bool = True,  # Default enabled with ATR trailing stops
    exit_trailing_stop_pct: float = 0.08,  # Fallback: Exit if price drops 8% from peak (used if ATR not available)
    exit_trailing_stop_atr_mult: float = 2.0,  # ATR multiplier for trailing stop (e.g., 2.0 = trail by 2x ATR)
    exit_trailing_stop_market_cap: str = "large",  # Market cap category: "small", "mid", "large" (adjusts ATR multiplier)
    exit_confirmation_bars: int = 2,  # Require 2 consecutive sell signals to exit
    exit_min_hold_bars: int = 5,  # Don't exit positions held less than 5 bars
    exit_early_on_parabola_break: bool = True,  # Exit early when parabola breaks
    exit_early_on_adx_drop: bool = True,  # Exit early when ADX drops below threshold
    exit_adx_drop_threshold: float = 15.0,  # ADX threshold for early exit
    # Hard stop loss (3% from entry, only after 3 days to avoid premature exits)
    use_hard_stop_loss: bool = True,  # Enable hard stop loss
    hard_stop_loss_pct: float = 0.03,  # Hard stop at 3% loss from entry
    hard_stop_min_days: int = 3,  # Only trigger hard stop after 3 days (bars)
    # Conservative take profit + "let it ride" scaling out
    use_conservative_take_profit: bool = True,  # Enable conservative partial exit
    conservative_tp_profit_pct: float = 0.025,  # Exit portion when up 2.5% (conservative profit lock-in)
    conservative_tp_exit_pct: float = 0.50,  # Exit 50% of position at conservative TP (rest "lets it ride")
    # After conservative exit, remaining position continues with trailing stops until full exit
    # Overextension guard: Triple (or more) RSI bearish divergences → block buys for N days (daily candles)
    rsi_bear_div_block_use: bool = True,
    rsi_bear_div_block_days: int = 14,
    rsi_bear_div_event_lookback: int = 120,
    rsi_bear_div_event_threshold: int = 3,
    rsi_bear_div_include_hidden: bool = True,
    # VIX Rate of Change (market fear/volatility indicator)
    vix_roc_use: bool = True,  # Enable VIX ROC filter
    vix_roc_rising_threshold: float = 5.0,  # VIX ROC threshold for aggressive rise (bearish/sell condition) - default 5%
    vix_roc_falling_threshold: float = -5.0,  # VIX ROC threshold for aggressive fall (bullish/buy condition) - default -5%
    # Kalman Moving Average (adaptive moving average)
    kalman_ma_use: bool = True,  # Enable Kalman MA signals
) -> pd.DataFrame:
    d = df.copy()

    # Component booleans
    trend_up = d["ema_fast"] > d["ema_slow"]
    trend_down = d["ema_fast"] < d["ema_slow"]

    strong_trend = d["adx"] > adx_thresh

    # RSI guardrails (avoid extremes for entries)
    rsi_buy_ok = d["rsi"] < rsi_buy_max
    rsi_sell_ok = d["rsi"] > rsi_sell_min

    # Volatility presence
    has_vol = d["atr"] > (d["atr_sma20"] * atr_presence_ratio)

    # Volume confirmation
    vol_ok = d["vol_ratio"] > vol_ratio_min
    
    # Volume Profile signals
    if volume_profile_use:
        # High Volume Nodes (HVN) - strong support/resistance levels
        hvn_support = d["hvn_strength"] > hvn_strength_thresh
        
        # Low Volume Nodes (LVN) - breakout zones
        lvn_breakout = d["lvn_strength"] > lvn_strength_thresh
        
        # VWAP deviation - price relative to volume-weighted average
        vwap_above = d["vwap_deviation"] > vwap_deviation_thresh
        vwap_below = d["vwap_deviation"] < -vwap_deviation_thresh
        
        # Volume trend - increasing volume momentum
        volume_increasing = d["volume_trend"] > volume_trend_thresh
        volume_decreasing = d["volume_trend"] < -volume_trend_thresh
    else:
        hvn_support = pd.Series(True, index=d.index)
        lvn_breakout = pd.Series(True, index=d.index)
        vwap_above = pd.Series(True, index=d.index)
        vwap_below = pd.Series(True, index=d.index)
        volume_increasing = pd.Series(True, index=d.index)
        volume_decreasing = pd.Series(True, index=d.index)

    # VROC signals
    if vroc_use:
        # VROC positive - volume increasing
        vroc_positive = d["vroc"] > vroc_positive_thresh
        
        # VROC negative - volume decreasing
        vroc_negative = d["vroc"] < vroc_negative_thresh
        
        # VROC momentum - volume acceleration
        vroc_momentum_up = d["vroc_momentum"] > vroc_momentum_thresh
        vroc_momentum_down = d["vroc_momentum"] < -vroc_momentum_thresh
        
        # VROC SMA confirmation - smoothed volume trend
        vroc_sma_positive = d["vroc_sma"] > 0
        vroc_sma_negative = d["vroc_sma"] < 0
    else:
        vroc_positive = pd.Series(True, index=d.index)
        vroc_negative = pd.Series(True, index=d.index)
        vroc_momentum_up = pd.Series(True, index=d.index)
        vroc_momentum_down = pd.Series(True, index=d.index)
        vroc_sma_positive = pd.Series(True, index=d.index)
        vroc_sma_negative = pd.Series(True, index=d.index)

    # RSI Divergence signals
    if rsi_divergence_use:
        # RSI Divergence signals (already calculated in build_indicators)
        rsi_bullish_divergence = d["rsi_bullish_div"]
        rsi_bearish_divergence = d["rsi_bearish_div"]
        rsi_hidden_bullish_divergence = d["rsi_hidden_bullish_div"]
        rsi_hidden_bearish_divergence = d["rsi_hidden_bearish_div"]
    else:
        rsi_bullish_divergence = pd.Series(False, index=d.index)
        rsi_bearish_divergence = pd.Series(False, index=d.index)
        rsi_hidden_bullish_divergence = pd.Series(False, index=d.index)
        rsi_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # MACD Divergence signals
    if macd_divergence_use:
        # MACD Divergence signals (already calculated in build_indicators)
        macd_bullish_divergence = d["macd_bullish_div"]
        macd_bearish_divergence = d["macd_bearish_div"]
        macd_hidden_bullish_divergence = d["macd_hidden_bullish_div"]
        macd_hidden_bearish_divergence = d["macd_hidden_bearish_div"]
    else:
        macd_bullish_divergence = pd.Series(False, index=d.index)
        macd_bearish_divergence = pd.Series(False, index=d.index)
        macd_hidden_bullish_divergence = pd.Series(False, index=d.index)
        macd_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # Stochastic RSI Divergence signals
    if stoch_rsi_divergence_use:
        # Stochastic RSI Divergence signals (already calculated in build_indicators)
        stoch_rsi_bullish_divergence = d["stoch_rsi_bullish_div"]
        stoch_rsi_bearish_divergence = d["stoch_rsi_bearish_div"]
        stoch_rsi_hidden_bullish_divergence = d["stoch_rsi_hidden_bullish_div"]
        stoch_rsi_hidden_bearish_divergence = d["stoch_rsi_hidden_bearish_div"]
    else:
        stoch_rsi_bullish_divergence = pd.Series(False, index=d.index)
        stoch_rsi_bearish_divergence = pd.Series(False, index=d.index)
        stoch_rsi_hidden_bullish_divergence = pd.Series(False, index=d.index)
        stoch_rsi_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # CCI Divergence signals
    if cci_divergence_use:
        # CCI Divergence signals (already calculated in build_indicators)
        cci_bullish_divergence = d["cci_bullish_div"]
        cci_bearish_divergence = d["cci_bearish_div"]
        cci_hidden_bullish_divergence = d["cci_hidden_bullish_div"]
        cci_hidden_bearish_divergence = d["cci_hidden_bearish_div"]
    else:
        cci_bullish_divergence = pd.Series(False, index=d.index)
        cci_bearish_divergence = pd.Series(False, index=d.index)
        cci_hidden_bullish_divergence = pd.Series(False, index=d.index)
        cci_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # MFI Divergence signals
    if mfi_divergence_use:
        # MFI Divergence signals (already calculated in build_indicators)
        mfi_bullish_divergence = d["mfi_bullish_div"]
        mfi_bearish_divergence = d["mfi_bearish_div"]
        mfi_hidden_bullish_divergence = d["mfi_hidden_bullish_div"]
        mfi_hidden_bearish_divergence = d["mfi_hidden_bearish_div"]
    else:
        mfi_bullish_divergence = pd.Series(False, index=d.index)
        mfi_bearish_divergence = pd.Series(False, index=d.index)
        mfi_hidden_bullish_divergence = pd.Series(False, index=d.index)
        mfi_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # ROC Divergence signals
    if roc_divergence_use:
        # ROC Divergence signals (already calculated in build_indicators)
        roc_bullish_divergence = d["roc_bullish_div"]
        roc_bearish_divergence = d["roc_bearish_div"]
        roc_hidden_bullish_divergence = d["roc_hidden_bullish_div"]
        roc_hidden_bearish_divergence = d["roc_hidden_bearish_div"]
    else:
        roc_bullish_divergence = pd.Series(False, index=d.index)
        roc_bearish_divergence = pd.Series(False, index=d.index)
        roc_hidden_bullish_divergence = pd.Series(False, index=d.index)
        roc_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # OBV Divergence signals
    if obv_divergence_use:
        # OBV Divergence signals (already calculated in build_indicators)
        obv_bullish_divergence = d["obv_bullish_div"]
        obv_bearish_divergence = d["obv_bearish_div"]
        obv_hidden_bullish_divergence = d["obv_hidden_bullish_div"]
        obv_hidden_bearish_divergence = d["obv_hidden_bearish_div"]
    else:
        obv_bullish_divergence = pd.Series(False, index=d.index)
        obv_bearish_divergence = pd.Series(False, index=d.index)
        obv_hidden_bullish_divergence = pd.Series(False, index=d.index)
        obv_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # SuperTrend Slope Divergence signals
    if st_divergence_use:
        # SuperTrend Slope Divergence signals (already calculated in build_indicators)
        st_bullish_divergence = d["st_bullish_div"]
        st_bearish_divergence = d["st_bearish_div"]
        st_hidden_bullish_divergence = d["st_hidden_bullish_div"]
        st_hidden_bearish_divergence = d["st_hidden_bearish_div"]
    else:
        st_bullish_divergence = pd.Series(False, index=d.index)
        st_bearish_divergence = pd.Series(False, index=d.index)
        st_hidden_bullish_divergence = pd.Series(False, index=d.index)
        st_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # Bollinger Band Width Divergence signals
    if bb_divergence_use:
        # Bollinger Band Width Divergence signals (already calculated in build_indicators)
        bb_bullish_divergence = d["bb_bullish_div"]
        bb_bearish_divergence = d["bb_bearish_div"]
        bb_hidden_bullish_divergence = d["bb_hidden_bullish_div"]
        bb_hidden_bearish_divergence = d["bb_hidden_bearish_div"]
    else:
        bb_bullish_divergence = pd.Series(False, index=d.index)
        bb_bearish_divergence = pd.Series(False, index=d.index)
        bb_hidden_bullish_divergence = pd.Series(False, index=d.index)
        bb_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # VROC Divergence signals
    if vroc_divergence_use:
        # VROC Divergence signals (already calculated in build_indicators)
        vroc_bullish_divergence = d["vroc_bullish_div"]
        vroc_bearish_divergence = d["vroc_bearish_div"]
        vroc_hidden_bullish_divergence = d["vroc_hidden_bullish_div"]
        vroc_hidden_bearish_divergence = d["vroc_hidden_bearish_div"]
    else:
        vroc_bullish_divergence = pd.Series(False, index=d.index)
        vroc_bearish_divergence = pd.Series(False, index=d.index)
        vroc_hidden_bullish_divergence = pd.Series(False, index=d.index)
        vroc_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # ATR Divergence signals
    if atr_divergence_use:
        # ATR Divergence signals (already calculated in build_indicators)
        atr_bullish_divergence = d["atr_bullish_div"]
        atr_bearish_divergence = d["atr_bearish_div"]
        atr_hidden_bullish_divergence = d["atr_hidden_bullish_div"]
        atr_hidden_bearish_divergence = d["atr_hidden_bearish_div"]
    else:
        atr_bullish_divergence = pd.Series(False, index=d.index)
        atr_bearish_divergence = pd.Series(False, index=d.index)
        atr_hidden_bullish_divergence = pd.Series(False, index=d.index)
        atr_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # ADX Divergence signals
    if adx_divergence_use:
        # ADX Divergence signals (already calculated in build_indicators)
        adx_bullish_divergence = d["adx_bullish_div"]
        adx_bearish_divergence = d["adx_bearish_div"]
        adx_hidden_bullish_divergence = d["adx_hidden_bullish_div"]
        adx_hidden_bearish_divergence = d["adx_hidden_bearish_div"]
    else:
        adx_bullish_divergence = pd.Series(False, index=d.index)
        adx_bearish_divergence = pd.Series(False, index=d.index)
        adx_hidden_bullish_divergence = pd.Series(False, index=d.index)
        adx_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # Parabola signals (corrected logic: end of parabolas as signals)
    if parabola_use:
        # Parabola signals (already calculated in build_indicators)
        # End of bullish parabola = SHORT signal (bubble popping)
        parabola_bearish = d["parabola_bullish_end"]  # Note: bullish_end = bearish signal
        # End of bearish parabola = LONG signal (crash bottoming)  
        parabola_bullish = d["parabola_bearish_end"]  # Note: bearish_end = bullish signal
        parabola_active = d["parabola_active"]
    else:
        parabola_bullish = pd.Series(False, index=d.index)
        parabola_bearish = pd.Series(False, index=d.index)
        parabola_active = pd.Series(False, index=d.index)

    # Williams %R Divergence signals
    if wpr_divergence_use:
        wpr_bullish_divergence = d["wpr_bullish_div"]
        wpr_bearish_divergence = d["wpr_bearish_div"]
        wpr_hidden_bullish_divergence = d["wpr_hidden_bullish_div"]
        wpr_hidden_bearish_divergence = d["wpr_hidden_bearish_div"]
    else:
        wpr_bullish_divergence = pd.Series(False, index=d.index)
        wpr_bearish_divergence = pd.Series(False, index=d.index)
        wpr_hidden_bullish_divergence = pd.Series(False, index=d.index)
        wpr_hidden_bearish_divergence = pd.Series(False, index=d.index)

    # Donchian breakouts
    don_break_up = d["Close"] > d["don_upper"]
    don_break_down = d["Close"] < d["don_lower"]

    # Z-Score not overextended in opposite direction
    z_ok_buy = d["z"].abs() <= z_abs_max
    z_ok_sell = d["z"].abs() <= z_abs_max

    # Candles
    bull_candle = d["bull_engulf"]
    bear_candle = d["bear_engulf"]

    # Timing filter
    if use_timing_filter:
        not_friday = d["dow"] != 4
        # Friday 3:00-8:00 PM EST bearish indicator (risk management: avoid low liquidity before weekend)
        # Adds +1 to sell components during this time window (15:00-20:00 EST = 3 PM - 8 PM EST)
        if "hour" in d.columns:
            friday_late_afternoon = (d["dow"] == 4) & (d["hour"] >= 15) & (d["hour"] < 20)
        else:
            # For daily data without hour info, default to False (time-based filter not applicable)
            friday_late_afternoon = pd.Series(False, index=d.index)
        
        # Monday 4:00-10:00 AM EST bullish indicator (early market momentum, high liquidity)
        # Adds +1 to buy components during this time window (4:00-10:00 EST = 4 AM - 10 AM EST)
        if "hour" in d.columns:
            monday_early_morning = (d["dow"] == 0) & (d["hour"] >= 4) & (d["hour"] < 10)
        else:
            # For daily data without hour info, default to False (time-based filter not applicable)
            monday_early_morning = pd.Series(False, index=d.index)
    else:
        not_friday = pd.Series(True, index=d.index)
        friday_late_afternoon = pd.Series(False, index=d.index)
        monday_early_morning = pd.Series(False, index=d.index)
    
    d["friday_late_afternoon"] = friday_late_afternoon
    d["monday_early_morning"] = monday_early_morning

    # VWAP conditions with customizable thresholds
    if "vwap" in d.columns:
        vwap_buy_threshold = d["vwap"] * vwap_buy_above
        vwap_sell_threshold = d["vwap"] * vwap_sell_below
        above_vwap = d["Close"] > vwap_buy_threshold
        below_vwap = d["Close"] < vwap_sell_threshold
    else:
        above_vwap = pd.Series(False, index=d.index)
        below_vwap = pd.Series(False, index=d.index)

    # Bollinger Bands conditions
    if "bb_upper" in d.columns and "bb_lower" in d.columns and "bb_width" in d.columns and "bb_percent" in d.columns:
        # BB Squeeze: low volatility (narrow bands) often precedes breakouts
        bb_squeeze = d["bb_width"] < bb_squeeze_thresh
        
        # BB Bounce: price near lower band (oversold) or upper band (overbought)
        bb_bounce_lower = d["bb_percent"] < bb_bounce_thresh  # Near lower band (buy signal)
        bb_bounce_upper = d["bb_percent"] > (1.0 - bb_bounce_thresh)  # Near upper band (sell signal)
        
        # BB Breakout: price breaks above upper or below lower band
        bb_break_up = d["Close"] > d["bb_upper"]
        bb_break_down = d["Close"] < d["bb_lower"]
    else:
        bb_squeeze = pd.Series(False, index=d.index)
        bb_bounce_lower = pd.Series(False, index=d.index)
        bb_bounce_upper = pd.Series(False, index=d.index)
        bb_break_up = pd.Series(False, index=d.index)
        bb_break_down = pd.Series(False, index=d.index)

    # Stochastic RSI conditions
    if "stoch_rsi" in d.columns:
        # StochRSI oversold (buy signal) and overbought (sell signal)
        stoch_rsi_oversold_signal = d["stoch_rsi"] < stoch_rsi_oversold
        stoch_rsi_overbought_signal = d["stoch_rsi"] > stoch_rsi_overbought
    else:
        stoch_rsi_oversold_signal = pd.Series(False, index=d.index)
        stoch_rsi_overbought_signal = pd.Series(False, index=d.index)

    # MACD conditions
    if "macd_line" in d.columns and "macd_signal" in d.columns and "macd_histogram" in d.columns:
        # MACD above zero (bullish momentum)
        macd_above_zero_signal = d["macd_line"] > 0 if macd_above_zero else pd.Series(True, index=d.index)
        
        # MACD histogram positive (increasing momentum)
        macd_histogram_positive_signal = d["macd_histogram"] > 0 if macd_histogram_positive else pd.Series(True, index=d.index)
        
        # MACD crossover signals
        macd_cross_above = (d["macd_line"] > d["macd_signal"]) & (d["macd_line"].shift(1) <= d["macd_signal"].shift(1))
        macd_cross_below = (d["macd_line"] < d["macd_signal"]) & (d["macd_line"].shift(1) >= d["macd_signal"].shift(1))
    else:
        macd_above_zero_signal = pd.Series(False, index=d.index)
        macd_histogram_positive_signal = pd.Series(False, index=d.index)
        macd_cross_above = pd.Series(False, index=d.index)
        macd_cross_below = pd.Series(False, index=d.index)

    # Williams %R conditions
    if "williams_r" in d.columns:
        # Williams %R oversold (buy signal) and overbought (sell signal)
        williams_r_oversold_signal = d["williams_r"] < williams_r_oversold
        williams_r_overbought_signal = d["williams_r"] > williams_r_overbought
    else:
        williams_r_oversold_signal = pd.Series(False, index=d.index)
        williams_r_overbought_signal = pd.Series(False, index=d.index)

    # CCI conditions
    if "cci" in d.columns:
        # CCI oversold (buy signal) and overbought (sell signal)
        cci_oversold_signal = d["cci"] < cci_oversold
        cci_overbought_signal = d["cci"] > cci_overbought
    else:
        cci_oversold_signal = pd.Series(False, index=d.index)
        cci_overbought_signal = pd.Series(False, index=d.index)

    # MFI conditions
    if "mfi" in d.columns:
        # MFI oversold (buy signal) and overbought (sell signal)
        mfi_oversold_signal = d["mfi"] < mfi_oversold
        mfi_overbought_signal = d["mfi"] > mfi_overbought
    else:
        mfi_oversold_signal = pd.Series(False, index=d.index)
        mfi_overbought_signal = pd.Series(False, index=d.index)

    # PSAR conditions
    if "psar" in d.columns:
        # PSAR below price = uptrend (buy signal), PSAR above price = downtrend (sell signal)
        psar_bullish_signal = d["Close"] > d["psar"]  # Price above PSAR = uptrend
        psar_bearish_signal = d["Close"] < d["psar"]  # Price below PSAR = downtrend
    else:
        psar_bullish_signal = pd.Series(False, index=d.index)
        psar_bearish_signal = pd.Series(False, index=d.index)

    # ROC conditions
    if "roc" in d.columns:
        # ROC positive = upward momentum (buy signal), ROC negative = downward momentum (sell signal)
        roc_positive_signal = d["roc"] > roc_positive  # ROC above threshold = upward momentum
        roc_negative_signal = d["roc"] < roc_negative  # ROC below threshold = downward momentum
    else:
        roc_positive_signal = pd.Series(False, index=d.index)
        roc_negative_signal = pd.Series(False, index=d.index)

    # Keltner Channels conditions
    if "kc_upper" in d.columns and "kc_lower" in d.columns and "kc_width" in d.columns and "kc_percent" in d.columns:
        kc_squeeze = d["kc_width"] < kc_squeeze_thresh
        kc_bounce_lower = d["kc_percent"] < kc_bounce_thresh
        kc_bounce_upper = d["kc_percent"] > (1.0 - kc_bounce_thresh)
        kc_break_up = d["Close"] > d["kc_upper"]
        kc_break_down = d["Close"] < d["kc_lower"]
    else:
        kc_squeeze = pd.Series(False, index=d.index)
        kc_bounce_lower = pd.Series(False, index=d.index)
        kc_bounce_upper = pd.Series(False, index=d.index)
        kc_break_up = pd.Series(False, index=d.index)
        kc_break_down = pd.Series(False, index=d.index)

    # OBV conditions
    if "obv" in d.columns:
        # OBV trend: positive slope indicates buying pressure, negative slope indicates selling pressure
        obv_trend = d["obv"].diff() > obv_trend_thresh
        obv_trend_negative = d["obv"].diff() < -obv_trend_thresh
        
        # OBV divergence: price vs OBV direction mismatch
        price_trend = d["Close"].diff() > 0
        obv_trend_positive = d["obv"].diff() > 0
        
        # Bullish divergence: price down, OBV up (buying pressure despite falling price)
        obv_bullish_divergence = (~price_trend) & obv_trend_positive
        # Bearish divergence: price up, OBV down (selling pressure despite rising price)
        obv_bearish_divergence = price_trend & (~obv_trend_positive)
        
        # OBV trend signals
        obv_bullish_trend = obv_trend
        obv_bearish_trend = obv_trend_negative
    else:
        obv_trend = pd.Series(False, index=d.index)
        obv_trend_negative = pd.Series(False, index=d.index)
        obv_bullish_divergence = pd.Series(False, index=d.index)
        obv_bearish_divergence = pd.Series(False, index=d.index)
        obv_bullish_trend = pd.Series(False, index=d.index)
        obv_bearish_trend = pd.Series(False, index=d.index)

    # Ichimoku Cloud conditions
    if "tenkan" in d.columns and "kijun" in d.columns and "cloud_upper" in d.columns and "cloud_lower" in d.columns and "chikou" in d.columns:
        # Cloud position signals
        price_above_cloud = d["Close"] > d["cloud_upper"]
        price_below_cloud = d["Close"] < d["cloud_lower"]
        price_in_cloud = (d["Close"] >= d["cloud_lower"]) & (d["Close"] <= d["cloud_upper"])
        
        # Tenkan/Kijun relationship
        tenkan_above_kijun = d["tenkan"] > d["kijun"]
        tenkan_below_kijun = d["tenkan"] < d["kijun"]
        
        # Chikou span position (compared to price 26 periods ago)
        chikou_above_price = d["chikou"] > d["Close"].shift(26)
        chikou_below_price = d["chikou"] < d["Close"].shift(26)
        
        # Ichimoku signals
        ichimoku_bullish_signal = (
            (price_above_cloud if ichimoku_bullish_cloud else True) &
            (tenkan_above_kijun if ichimoku_tenkan_kijun else True) &
            (chikou_above_price if ichimoku_chikou else True)
        )
        
        ichimoku_bearish_signal = (
            (price_below_cloud if ichimoku_bearish_cloud else True) &
            (tenkan_below_kijun if ichimoku_tenkan_kijun else True) &
            (chikou_below_price if ichimoku_chikou else True)
        )
        
        # Cloud thickness (for additional context)
        cloud_thick = d["cloud_thickness"] > 0.02  # 2% of price
    else:
        ichimoku_bullish_signal = pd.Series(False, index=d.index)
        ichimoku_bearish_signal = pd.Series(False, index=d.index)
        cloud_thick = pd.Series(False, index=d.index)

    # SuperTrend conditions
    if supertrend_use and "supertrend_dir" in d.columns and "supertrend_line" in d.columns:
        st_bullish = d["supertrend_dir"] > 0
        st_bearish = d["supertrend_dir"] < 0
        st_price_above = d["Close"] > d["supertrend_line"]
        st_price_below = d["Close"] < d["supertrend_line"]
    else:
        st_bullish = pd.Series(False, index=d.index)
        st_bearish = pd.Series(False, index=d.index)
        st_price_above = pd.Series(False, index=d.index)
        st_price_below = pd.Series(False, index=d.index)

    # ATR Channels conditions
    if atr_channels_use and "atr_upper" in d.columns and "atr_lower" in d.columns and "atr_width" in d.columns and "atr_percent" in d.columns:
        # ATR Channels squeeze: low volatility (narrow channels) often precedes breakouts
        atr_squeeze = d["atr_width"] < atr_channels_squeeze_thresh
        
        # ATR Channels bounce: price near lower channel (oversold) or upper channel (overbought)
        atr_bounce_lower = d["atr_percent"] < atr_channels_bounce_thresh  # Near lower channel (buy signal)
        atr_bounce_upper = d["atr_percent"] > (1.0 - atr_channels_bounce_thresh)  # Near upper channel (sell signal)
        
        # ATR Channels breakout: price breaks above upper or below lower channel
        atr_break_up = d["Close"] > d["atr_upper"]
        atr_break_down = d["Close"] < d["atr_lower"]
    else:
        atr_squeeze = pd.Series(False, index=d.index)
        atr_bounce_lower = pd.Series(False, index=d.index)
        atr_bounce_upper = pd.Series(False, index=d.index)
        atr_break_up = pd.Series(False, index=d.index)
        atr_break_down = pd.Series(False, index=d.index)

    # Expose component columns for explanation/debug
    d["trend_up"] = trend_up
    d["trend_down"] = trend_down
    d["strong_trend"] = strong_trend
    d["rsi_buy_ok"] = rsi_buy_ok
    d["rsi_sell_ok"] = rsi_sell_ok
    d["has_vol"] = has_vol
    d["vol_ok"] = vol_ok
    d["don_break_up"] = don_break_up
    d["don_break_down"] = don_break_down
    d["z_ok_buy"] = z_ok_buy
    d["z_ok_sell"] = z_ok_sell
    d["bull_candle"] = bull_candle
    d["bear_candle"] = bear_candle
    d["not_friday"] = not_friday
    d["above_vwap"] = above_vwap
    d["below_vwap"] = below_vwap
    d["bb_squeeze"] = bb_squeeze
    d["bb_bounce_lower"] = bb_bounce_lower
    d["bb_bounce_upper"] = bb_bounce_upper
    d["bb_break_up"] = bb_break_up
    d["bb_break_down"] = bb_break_down
    d["stoch_rsi_oversold"] = stoch_rsi_oversold_signal
    d["stoch_rsi_overbought"] = stoch_rsi_overbought_signal
    d["macd_above_zero"] = macd_above_zero_signal
    d["macd_histogram_positive"] = macd_histogram_positive_signal
    d["macd_cross_above"] = macd_cross_above
    d["macd_cross_below"] = macd_cross_below
    d["williams_r_oversold"] = williams_r_oversold_signal
    d["williams_r_overbought"] = williams_r_overbought_signal
    d["cci_oversold"] = cci_oversold_signal
    d["cci_overbought"] = cci_overbought_signal
    d["mfi_oversold"] = mfi_oversold_signal
    d["mfi_overbought"] = mfi_overbought_signal
    d["psar_bullish"] = psar_bullish_signal
    d["psar_bearish"] = psar_bearish_signal
    d["roc_positive"] = roc_positive_signal
    d["roc_negative"] = roc_negative_signal
    d["kc_squeeze"] = kc_squeeze
    d["kc_bounce_lower"] = kc_bounce_lower
    d["kc_bounce_upper"] = kc_bounce_upper
    d["kc_break_up"] = kc_break_up
    d["kc_break_down"] = kc_break_down
    d["obv_bullish_trend"] = obv_bullish_trend
    d["obv_bearish_trend"] = obv_bearish_trend
    d["obv_bullish_divergence"] = obv_bullish_divergence
    d["obv_bearish_divergence"] = obv_bearish_divergence
    d["ichimoku_bullish"] = ichimoku_bullish_signal
    d["ichimoku_bearish"] = ichimoku_bearish_signal
    d["cloud_thick"] = cloud_thick
    d["st_bullish"] = st_bullish
    d["st_bearish"] = st_bearish
    d["st_price_above"] = st_price_above
    d["st_price_below"] = st_price_below
    d["atr_squeeze"] = atr_squeeze
    d["atr_bounce_lower"] = atr_bounce_lower
    d["atr_bounce_upper"] = atr_bounce_upper
    d["atr_break_up"] = atr_break_up
    d["atr_break_down"] = atr_break_down

    # VIX Rate of Change conditions (market fear/volatility indicator)
    # Rising VIX aggressively = bearish (avoid longs, favor sells)
    # Falling VIX aggressively = bullish (favor buys)
    if vix_roc_use and "vix_roc" in d.columns:
        # VIX ROC rising aggressively (bearish condition - avoid longs)
        vix_roc_rising = d["vix_roc"] >= vix_roc_rising_threshold
        # VIX ROC falling aggressively (bullish condition - favor buys)
        vix_roc_falling = d["vix_roc"] <= vix_roc_falling_threshold
    else:
        vix_roc_rising = pd.Series(False, index=d.index)
        vix_roc_falling = pd.Series(False, index=d.index)
    
    d["vix_roc_rising"] = vix_roc_rising
    d["vix_roc_falling"] = vix_roc_falling

    # Kalman Moving Average conditions (adaptive moving average)
    # Close above Kalman MA = bullish, Close below Kalman MA = bearish
    if kalman_ma_use and "kalman_ma" in d.columns:
        kalman_ma_bullish = d["Close"] > d["kalman_ma"]  # Close above Kalman MA = bullish
        kalman_ma_bearish = d["Close"] < d["kalman_ma"]  # Close below Kalman MA = bearish
    else:
        kalman_ma_bullish = pd.Series(False, index=d.index)
        kalman_ma_bearish = pd.Series(False, index=d.index)
    
    d["kalman_ma_bullish"] = kalman_ma_bullish
    d["kalman_ma_bearish"] = kalman_ma_bearish

    # Score-based voting to avoid over-restricting
    # Timing filter applies to BUYS only (Fridays blocked for buys; sells still allowed)
    # Friday 3:00-8:00 PM EST: Automatic +1 bearish indicator (risk management: avoid low liquidity before weekend)
    # Monday 4:00-10:00 AM EST: Automatic +1 bullish indicator (early market momentum, high liquidity)
    # Bollinger Bands: squeeze + bounce/breakout for additional volatility-based signals
    # Keltner Channels: ATR-based volatility channels (complementary to Bollinger Bands)
    # OBV: On-Balance Volume for cumulative volume flow and divergence detection
    # Ichimoku Cloud: comprehensive trend analysis system with dynamic support/resistance
    # Stochastic RSI: oversold/overbought momentum signals
    # MACD: trend momentum confirmation and crossover signals
    # Williams %R: additional momentum oscillator with different scale
    # VIX ROC: Market fear/volatility indicator - rising VIX = bearish, falling VIX = bullish
    # Kalman MA: Adaptive moving average - close above = bullish, close below = bearish
    #
    # NOTE: Consider implementing divergences (price vs indicator) rather than hard-coded thresholds
    # for more adaptive signal generation across different market conditions. This would make
    # the strategy more robust to varying volatility and trend characteristics.
    buy_components = [trend_up, strong_trend, rsi_buy_ok, has_vol, vol_ok, don_break_up | bull_candle, z_ok_buy, not_friday, monday_early_morning, bb_squeeze | bb_bounce_lower | bb_break_up, kc_squeeze | kc_bounce_lower | kc_break_up, atr_squeeze | atr_bounce_lower | atr_break_up, obv_bullish_trend | obv_bullish_divergence, ichimoku_bullish_signal, st_bullish | st_price_above, stoch_rsi_oversold_signal, macd_above_zero_signal | macd_cross_above, williams_r_oversold_signal, cci_oversold_signal, mfi_oversold_signal, psar_bullish_signal, roc_positive_signal, hvn_support | lvn_breakout, vwap_above | volume_increasing, vroc_positive | vroc_momentum_up | vroc_sma_positive, rsi_bullish_divergence | rsi_hidden_bullish_divergence, macd_bullish_divergence | macd_hidden_bullish_divergence, stoch_rsi_bullish_divergence | stoch_rsi_hidden_bullish_divergence, cci_bullish_divergence | cci_hidden_bullish_divergence, mfi_bullish_divergence | mfi_hidden_bullish_divergence, wpr_bullish_divergence | wpr_hidden_bullish_divergence, roc_bullish_divergence | roc_hidden_bullish_divergence, obv_bullish_divergence | obv_hidden_bullish_divergence, st_bullish_divergence | st_hidden_bullish_divergence, bb_bullish_divergence | bb_hidden_bullish_divergence, vroc_bullish_divergence | vroc_hidden_bullish_divergence, atr_bullish_divergence | atr_hidden_bullish_divergence, adx_bullish_divergence | adx_hidden_bullish_divergence, parabola_bullish, vix_roc_falling, kalman_ma_bullish]
    sell_components = [trend_down, strong_trend, rsi_sell_ok, has_vol, vol_ok, don_break_down | bear_candle, z_ok_sell, bb_squeeze | bb_bounce_upper | bb_break_down, kc_squeeze | kc_bounce_upper | kc_break_down, atr_squeeze | atr_bounce_upper | atr_break_down, obv_bearish_trend | obv_bearish_divergence, ichimoku_bearish_signal, st_bearish | st_price_below, stoch_rsi_overbought_signal, macd_histogram_positive_signal | macd_cross_below, williams_r_overbought_signal, cci_overbought_signal, mfi_overbought_signal, psar_bearish_signal, roc_negative_signal, hvn_support | lvn_breakout, vwap_below | volume_decreasing, vroc_negative | vroc_momentum_down | vroc_sma_negative, rsi_bearish_divergence | rsi_hidden_bearish_divergence, macd_bearish_divergence | macd_hidden_bearish_divergence, stoch_rsi_bearish_divergence | stoch_rsi_hidden_bearish_divergence, cci_bearish_divergence | cci_hidden_bearish_divergence, mfi_bearish_divergence | mfi_hidden_bearish_divergence, wpr_bearish_divergence | wpr_hidden_bearish_divergence, roc_bearish_divergence | roc_hidden_bearish_divergence, obv_bearish_divergence | obv_hidden_bearish_divergence, st_bearish_divergence | st_hidden_bearish_divergence, bb_bearish_divergence | bb_hidden_bearish_divergence, vroc_bearish_divergence | vroc_hidden_bearish_divergence, atr_bearish_divergence | atr_hidden_bearish_divergence, adx_bearish_divergence | adx_hidden_bearish_divergence, parabola_bearish, vix_roc_rising, kalman_ma_bearish, friday_late_afternoon]

    buy_score = sum(comp.astype(int) for comp in buy_components)
    sell_score = sum(comp.astype(int) for comp in sell_components)

    # Expose scores
    d["buy_score"] = buy_score
    d["sell_score"] = sell_score

    # Dynamic thresholds: absolute if provided, else fraction of total components
    total_buy_components = len(buy_components)
    total_sell_components = len(sell_components)
    
    # v6 ENHANCEMENT (UPDATED): Fixed thresholds for high-quality but not ultra-rare signals
    # Total components: ~38 indicators
    # Strategy: Use thresholds near the 75th percentile of historical scores
    #           (based on recent analysis runs), trading off selectivity vs. silence.
    
    AGGRESSIVE_BUY_THRESHOLD = 16   # ≈42% of buy components must agree (16/38)
    AGGRESSIVE_SELL_THRESHOLD = 13  # ≈35% of sell components must agree (13/37)
    
    # v11 ENHANCEMENT: Automatic threshold adjustment (non-destructive)
    # If enabled, use analyze_signal_strength() recommendations instead of fixed thresholds
    if auto_adjust_thresholds and len(d) >= auto_adjust_lookback:
        try:
            # Analyze recent signal strength to get recommended thresholds
            analysis = analyze_signal_strength(d, lookback=auto_adjust_lookback)
            recommended_buy = analysis.get("recommended_buy_threshold", AGGRESSIVE_BUY_THRESHOLD)
            recommended_sell = analysis.get("recommended_sell_threshold", AGGRESSIVE_SELL_THRESHOLD)
            
            # Use recommended thresholds (but allow manual override to take precedence)
            if min_components_buy is None:
                buy_threshold = int(recommended_buy)
            else:
                buy_threshold = int(min_components_buy)
            
            if min_components_sell is None:
                sell_threshold = int(recommended_sell)
            else:
                sell_threshold = int(min_components_sell)
            
            if ARGS_DEBUG:
                print(f"[AUTO-THRESHOLD] Recommended: Buy={recommended_buy}, Sell={recommended_sell} | Using: Buy={buy_threshold}, Sell={sell_threshold}")
        except Exception as e:
            if ARGS_DEBUG:
                print(f"[AUTO-THRESHOLD] Error in auto-adjustment: {e}, falling back to fixed thresholds")
            # Fall back to fixed thresholds on error
            buy_threshold = (
                int(min_components_buy)
                if (min_components_buy is not None)
                else AGGRESSIVE_BUY_THRESHOLD
            )
            sell_threshold = (
                int(min_components_sell)
                if (min_components_sell is not None)
                else AGGRESSIVE_SELL_THRESHOLD
            )
    else:
        # Calculate thresholds (with override support via CLI args)
        buy_threshold = (
            int(min_components_buy)
            if (min_components_buy is not None)
            else AGGRESSIVE_BUY_THRESHOLD
        )
        sell_threshold = (
            int(min_components_sell)
            if (min_components_sell is not None)
            else AGGRESSIVE_SELL_THRESHOLD
        )
    
    # Add threshold info to dataframe for analysis
    d["buy_threshold"] = buy_threshold
    d["sell_threshold"] = sell_threshold
    d["buy_threshold_pct"] = buy_threshold / total_buy_components
    d["sell_threshold_pct"] = sell_threshold / total_sell_components

    # Generate base signals
    d["buy_signal"] = buy_score >= buy_threshold
    d["sell_signal"] = sell_score >= sell_threshold

    # Preserve raw threshold-met signals for display/diagnostics (even if later blocked).
    d["buy_signal_raw"] = d["buy_signal"].copy()
    d["sell_signal_raw"] = d["sell_signal"].copy()

    # ----------------------------
    # BUY BLOCK: Triple RSI bearish divergence persistence
    # ----------------------------
    # Goal: avoid trend-following buys when RSI shows repeated bearish divergence (overextension).
    try:
        if rsi_bear_div_block_use:
            rsi_bear = d.get("rsi_bearish_div", pd.Series(False, index=d.index)).fillna(False)
            if rsi_bear_div_include_hidden:
                rsi_bear = rsi_bear | d.get("rsi_hidden_bearish_div", pd.Series(False, index=d.index)).fillna(False)

            # Event = rising edge (count distinct divergences, not persistence bars)
            rsi_bear_event = rsi_bear & (~rsi_bear.shift(1).fillna(False))

            lookback = max(1, int(rsi_bear_div_event_lookback))
            threshold = max(1, int(rsi_bear_div_event_threshold))
            block_days = max(1, int(rsi_bear_div_block_days))

            rsi_bear_event_count = rsi_bear_event.rolling(window=lookback, min_periods=1).sum()

            # Trigger only on a NEW bearish divergence event once count has reached threshold
            rsi_bear_block_trigger = rsi_bear_event & (rsi_bear_event_count >= float(threshold))

            # Countdown timer that resets on trigger; active blocks buys
            rsi_bear_block_timer = pd.Series([0] * len(d), index=d.index, dtype=int)
            for i in range(len(d)):
                if i == 0:
                    rsi_bear_block_timer.iloc[i] = block_days if bool(rsi_bear_block_trigger.iloc[i]) else 0
                else:
                    prev = int(rsi_bear_block_timer.iloc[i - 1])
                    if bool(rsi_bear_block_trigger.iloc[i]):
                        rsi_bear_block_timer.iloc[i] = block_days
                    else:
                        rsi_bear_block_timer.iloc[i] = max(prev - 1, 0)

            rsi_bear_block_active = rsi_bear_block_timer > 0

            # Expose for debugging/website warnings
            d["rsi_bear_div_event"] = rsi_bear_event
            d["rsi_bear_div_event_count"] = rsi_bear_event_count
            d["rsi_bear_div_block_trigger"] = rsi_bear_block_trigger
            d["rsi_bear_div_block_timer"] = rsi_bear_block_timer
            d["rsi_bear_div_block_active"] = rsi_bear_block_active
            d["buy_blocked_rsi_bear_div"] = rsi_bear_block_active

            # Block BUYs (do not block SELLs)
            d["buy_signal"] = d["buy_signal"] & (~rsi_bear_block_active)
        else:
            d["buy_blocked_rsi_bear_div"] = False
    except Exception:
        d["buy_blocked_rsi_bear_div"] = False
    
    # v12 ENHANCEMENT: Signal persistence and conviction tracking
    # Track how many consecutive bars each signal has been true (adds conviction)
    buy_persistence = pd.Series([0] * len(d), index=d.index, dtype=int)
    sell_persistence = pd.Series([0] * len(d), index=d.index, dtype=int)
    
    for i in range(len(d)):
        if i == 0:
            buy_persistence.iloc[i] = 1 if d["buy_signal"].iloc[i] else 0
            sell_persistence.iloc[i] = 1 if d["sell_signal"].iloc[i] else 0
        else:
            # Buy persistence: increment if signal is true, reset to 0 if false
            if d["buy_signal"].iloc[i]:
                buy_persistence.iloc[i] = buy_persistence.iloc[i-1] + 1 if d["buy_signal"].iloc[i-1] else 1
            else:
                buy_persistence.iloc[i] = 0
            
            # Sell persistence: increment if signal is true, reset to 0 if false
            if d["sell_signal"].iloc[i]:
                sell_persistence.iloc[i] = sell_persistence.iloc[i-1] + 1 if d["sell_signal"].iloc[i-1] else 1
            else:
                sell_persistence.iloc[i] = 0
    
    d["buy_persistence"] = buy_persistence
    d["sell_persistence"] = sell_persistence
    
    # Calculate conviction scores (0.0 to 1.0)
    # Combines component percentage and persistence
    # Component %: how many indicators agree (16/38 = 42% = 0.42)
    # Persistence: how many consecutive bars (capped at 10 bars for diminishing returns)
    buy_component_pct = buy_score / total_buy_components  # 0.0 to 1.0
    sell_component_pct = sell_score / total_sell_components  # 0.0 to 1.0
    
    # Persistence bonus: 0.0 to 0.3 (capped at 10 bars = max bonus)
    # Formula: min(persistence, 10) / 10 * 0.3
    buy_persistence_bonus = (buy_persistence.clip(upper=10) / 10.0) * 0.3
    sell_persistence_bonus = (sell_persistence.clip(upper=10) / 10.0) * 0.3
    
    # Conviction = component % (0.0-1.0) + persistence bonus (0.0-0.3)
    # Clamped to 0.0-1.0 range
    buy_conviction = (buy_component_pct + buy_persistence_bonus).clip(0.0, 1.0)
    sell_conviction = (sell_component_pct + sell_persistence_bonus).clip(0.0, 1.0)
    
    d["buy_conviction"] = buy_conviction
    d["sell_conviction"] = sell_conviction
    
    # Position sizing multiplier based on conviction (for use in trading bots)
    # Low conviction (0.0-0.4): 0.5x (half size)
    # Medium conviction (0.4-0.7): 1.0x (normal size)
    # High conviction (0.7-1.0): 1.5x (larger size)
    def conviction_to_size_mult(conviction: pd.Series) -> pd.Series:
        """Convert conviction score to position size multiplier."""
        return pd.Series(
            [
                0.5 if c < 0.4 else (1.5 if c >= 0.7 else 1.0)
                for c in conviction
            ],
            index=conviction.index
        )
    
    d["buy_position_multiplier"] = conviction_to_size_mult(buy_conviction)
    d["sell_position_multiplier"] = conviction_to_size_mult(sell_conviction)
    
    # TODO: Perfect Stop Loss System (for future enhancement)
    # Current: Basic hard stop (3% after 3 days) + ATR trailing stops
    # Future improvements:
    # - ATR-based hard stops: Use ATR multiplier instead of fixed 3% (e.g., 2x ATR from entry)
    # - Regime-based stops: Tighter stops in bear markets, looser in bull markets
    #   * Use HMM regime detection or VIX levels to adjust stop distance
    #   * Bear market: 2% stop, Bull market: 4% stop
    # - DXY-based stops: Tighter stops when DXY is rising (risk-off environment)
    #   * Use DXY trend/rate of change to adjust stop sensitivity
    # - Volatility-adjusted stops: Wider stops in high volatility, tighter in low volatility
    #   * Use ATR percentile or VIX levels to dynamically adjust
    # - Time-decay stops: Gradually tighten stops as position ages
    #   * Start with 4% stop, tighten to 2% after 10 days
    # - Support/resistance stops: Place stops below key support levels
    #   * Use volume profile HVN/LVN or Fibonacci levels
    #
    # Example implementation:
    # if regime == "bear":
    #     stop_pct = 0.02  # Tighter in bear markets
    # elif regime == "bull":
    #     stop_pct = 0.04  # Looser in bull markets
    # 
    # if dxy_rising and dxy_roc > 5.0:
    #     stop_pct *= 0.75  # 25% tighter when DXY rising aggressively
    # 
    # if current_atr_percentile > 80:
    #     stop_pct *= 1.5  # 50% wider in high volatility
    
    # TODO: Risk-Based Position Sizing (for automation with Interactive Brokers)
    # Currently manual trading, but when automating, calculate actual position sizes:
    # 
    # def calculate_risk_based_position_size(
    #     equity: float,
    #     entry_price: float,
    #     stop_distance_pct: float,
    #     risk_per_trade_pct: float = 0.02,  # Risk 2% of capital per trade
    #     conviction_multiplier: float = 1.0  # From buy_position_multiplier
    # ) -> float:
    #     """
    #     Calculate position size in dollars based on risk.
    #     Formula: position_size = (equity × risk_pct) / stop_distance_pct
    #     Then multiply by conviction multiplier for signal strength adjustment.
    #     """
    #     base_position = (equity * risk_per_trade_pct) / stop_distance_pct
    #     adjusted_position = base_position * conviction_multiplier
    #     return adjusted_position
    # 
    # # Calculate stop distance from ATR or use fixed %
    # if has_atr and atr_col:
    #     atr_value = d[atr_col].iloc[-1]
    #     stop_distance_pct = (atr_value * exit_trailing_stop_atr_mult) / d["Close"].iloc[-1]
    # else:
    #     stop_distance_pct = 0.03  # Fixed 3% stop
    # 
    # # Calculate position size for each buy signal
    # equity = 10000  # Get from broker API or config
    # risk_pct = 0.02  # Risk 2% per trade
    # 
    # position_sizes = []
    # for i in range(len(d)):
    #     if d["buy_signal"].iloc[i]:
    #         entry_price = d["Close"].iloc[i]
    #         conviction_mult = d["buy_position_multiplier"].iloc[i]
    #         position_size = calculate_risk_based_position_size(
    #             equity, entry_price, stop_distance_pct, risk_pct, conviction_mult
    #         )
    #         position_sizes.append(position_size)
    #     else:
    #         position_sizes.append(0.0)
    # 
    # d["position_size_dollars"] = pd.Series(position_sizes, index=d.index)
    # d["stop_distance_pct"] = stop_distance_pct
    
    # v11 ENHANCEMENT: Improved exit logic (non-destructive)
    # This makes the strategy hold longer but allows early exits when needed
    if use_improved_exits:
        # Initialize exit logic columns
        exit_signal = pd.Series([False] * len(d), index=d.index)
        exit_reason = pd.Series([""] * len(d), index=d.index, dtype=object)
        trailing_peak = d["High"].copy()  # Track highest price since entry
        bars_since_entry = pd.Series([0] * len(d), index=d.index)
        consecutive_sell_signals = pd.Series([0] * len(d), index=d.index)
        
        # Initialize partial exit tracking (conservative take profit)
        partial_exit_signal = pd.Series([False] * len(d), index=d.index)
        partial_exit_price = pd.Series([0.0] * len(d), index=d.index)
        partial_exit_pct = pd.Series([0.0] * len(d), index=d.index)  # Track what % was exited
        
        # ATR-based trailing stop setup
        has_atr = "atr" in d.columns and d["atr"].notna().any()
        atr_col = "atr" if has_atr else None
        
        # Market cap adjustment for ATR multiplier
        # Small caps: tighter stops (0.7x), Large caps: looser stops (1.3x)
        cap_multipliers = {
            "small": 0.7,   # Tighter - 30% reduction
            "mid": 1.0,     # Baseline
            "large": 1.3,   # Looser - 30% increase
        }
        cap_adjustment = cap_multipliers.get(exit_trailing_stop_market_cap.lower(), 1.0)
        effective_atr_mult = exit_trailing_stop_atr_mult * cap_adjustment
        
        # Track position state (simplified: assume we enter on first buy signal)
        in_position = False
        entry_bar_index = -1
        trailing_peak_value = 0.0
        trailing_stop_price = 0.0  # ATR-based trailing stop price
        partial_exit_triggered = False  # Track if we've already taken partial profit
        entry_price = 0.0  # Track entry price for take profit calculation
        
        for i in range(len(d)):
            idx = d.index[i]
            current_price = d["Close"].iloc[i]
            current_high = d["High"].iloc[i]
            is_buy = d["buy_signal"].iloc[i]
            is_sell = d["sell_signal"].iloc[i]
            
            # Entry logic: enter on buy signal if not in position
            if not in_position and is_buy:
                in_position = True
                entry_bar_index = i
                entry_price = current_price
                trailing_peak_value = current_high
                trailing_stop_price = 0.0  # Initialize trailing stop
                partial_exit_triggered = False  # Reset partial exit flag
                bars_since_entry.iloc[i] = 0
                consecutive_sell_signals.iloc[i] = 0
                continue
            
            if in_position:
                bars_held = i - entry_bar_index
                bars_since_entry.iloc[i] = bars_held
                
                # Conservative take profit check (exits portion to lock in profits, rest "lets it ride")
                # Only triggers once per trade - after this, remaining position continues with trailing stops
                if use_conservative_take_profit and not partial_exit_triggered and entry_price > 0:
                    # Calculate conservative take profit price (e.g., entry + 2.5%)
                    conservative_tp_price = entry_price * (1 + conservative_tp_profit_pct)
                    
                    # Check if price has reached conservative take profit (using high to catch intraday moves)
                    if current_high >= conservative_tp_price:
                        partial_exit_triggered = True
                        partial_exit_signal.iloc[i] = True
                        partial_exit_price.iloc[i] = conservative_tp_price
                        partial_exit_pct.iloc[i] = conservative_tp_exit_pct
                        # Note: Position continues with remaining portion (1 - conservative_tp_exit_pct)
                        # Trailing stops and other exit conditions still apply to the "let it ride" portion
                
                # Update trailing peak (highest high since entry)
                if current_high > trailing_peak_value:
                    trailing_peak_value = current_high
                trailing_peak.iloc[i] = trailing_peak_value
                
                # Update ATR-based trailing stop (moves up with price, never down)
                if has_atr and atr_col and trailing_peak_value > 0:
                    current_atr = d[atr_col].iloc[i] if pd.notna(d[atr_col].iloc[i]) else 0.0
                    if current_atr > 0:
                        # Calculate new trailing stop: peak - (ATR × multiplier)
                        new_trailing_stop = trailing_peak_value - (current_atr * effective_atr_mult)
                        # Trailing stop only moves up, never down
                        if new_trailing_stop > trailing_stop_price or trailing_stop_price == 0.0:
                            trailing_stop_price = new_trailing_stop
                
                # Track consecutive sell signals
                if is_sell:
                    prev_consecutive = consecutive_sell_signals.iloc[i-1] if i > 0 else 0
                    consecutive_sell_signals.iloc[i] = prev_consecutive + 1
                else:
                    consecutive_sell_signals.iloc[i] = 0
                
                consecutive_sells = consecutive_sell_signals.iloc[i]
                should_exit = False
                reason = ""
                
                # Early exit triggers (can exit even if minimum hold not met)
                early_exit = False
                
                # 1. Parabola break (trend exhaustion)
                if exit_early_on_parabola_break and "parabola_active" in d.columns:
                    parabola_active = d["parabola_active"].iloc[i] if i < len(d) else False
                    parabola_breaks_col = d.get("parabola_breaks", pd.Series([False] * len(d), index=d.index))
                    parabola_breaks = parabola_breaks_col.iloc[i] if "parabola_breaks" in d.columns else False
                    if parabola_active and parabola_breaks:
                        early_exit = True
                        reason = "Parabola break (trend exhaustion)"
                
                # 2. ADX drop (trend weakening)
                if exit_early_on_adx_drop and "adx" in d.columns:
                    current_adx = d["adx"].iloc[i] if i < len(d) else 0.0
                    if current_adx < exit_adx_drop_threshold:
                        early_exit = True
                        if not reason:
                            reason = f"ADX drop ({current_adx:.1f} < {exit_adx_drop_threshold})"
                
                # 3. Hard stop loss (3% from entry, only after minimum days)
                if use_hard_stop_loss and bars_held >= hard_stop_min_days and entry_price > 0:
                    current_low = d["Low"].iloc[i]
                    loss_from_entry_pct = (current_low / entry_price) - 1.0
                    if loss_from_entry_pct <= -hard_stop_loss_pct:
                        early_exit = True
                        if not reason:
                            reason = f"Hard stop loss ({loss_from_entry_pct:.1%} from entry, after {bars_held} days)"
                
                # 4. ATR-based trailing stop (preferred) or percentage-based fallback
                if has_atr and atr_col and trailing_stop_price > 0:
                    # ATR-based trailing stop: exit if price drops below trailing stop
                    current_low = d["Low"].iloc[i]
                    if current_low <= trailing_stop_price:
                        early_exit = True
                        if not reason:
                            drawdown_pct = (current_price / trailing_peak_value) - 1.0
                            reason = f"ATR trailing stop ({effective_atr_mult:.1f}x ATR, {drawdown_pct:.1%} from peak)"
                elif trailing_peak_value > 0:
                    # Fallback to percentage-based trailing stop if ATR not available
                    drawdown_pct = (current_price / trailing_peak_value) - 1.0
                    if drawdown_pct <= -exit_trailing_stop_pct:
                        early_exit = True
                        if not reason:
                            reason = f"Trailing stop ({drawdown_pct:.1%} from peak)"
                
                # Regular exit conditions (require minimum hold period)
                if not early_exit and bars_held >= exit_min_hold_bars:
                    # Exit on confirmation (multiple consecutive sell signals)
                    if consecutive_sells >= exit_confirmation_bars:
                        should_exit = True
                        reason = f"Confirmed exit ({consecutive_sells} consecutive sell signals)"
                
                # Apply exit signal
                if early_exit or should_exit:
                    exit_signal.iloc[i] = True
                    exit_reason.iloc[i] = reason
                    # Reset position state
                    in_position = False
                    entry_bar_index = -1
                    entry_price = 0.0
                    trailing_peak_value = 0.0
                    trailing_stop_price = 0.0
                    partial_exit_triggered = False
                    bars_since_entry.iloc[i] = 0
                    consecutive_sell_signals.iloc[i] = 0
            else:
                # Not in position
                bars_since_entry.iloc[i] = 0
                consecutive_sell_signals.iloc[i] = 0
                trailing_peak.iloc[i] = current_high
        
        # Add exit logic columns to dataframe
        d["exit_signal"] = exit_signal
        d["exit_reason"] = exit_reason
        d["trailing_peak"] = trailing_peak
        d["bars_since_entry"] = bars_since_entry
        d["consecutive_sell_signals"] = consecutive_sell_signals
        
        # Add partial exit columns (conservative take profit)
        d["partial_exit_signal"] = partial_exit_signal
        d["partial_exit_price"] = partial_exit_price
        d["partial_exit_pct"] = partial_exit_pct  # What % of position was exited
        
        # Override sell_signal with improved exit logic
        # Use exit_signal instead of raw sell_signal for actual exits
        d["sell_signal_original"] = d["sell_signal"].copy()  # Keep original for analysis
        d["sell_signal"] = exit_signal  # Use improved exit logic
    else:
        # Original behavior: use sell_signal as-is
        pass

    # Persist component counts to enable downstream strength/confidence calculations
    d["total_buy_components"] = int(total_buy_components)
    d["total_sell_components"] = int(total_sell_components)
    
    # Multi-Timeframe Confirmation (default ON)
    # Initialize MTF columns (will be filled if confirmation is enabled)
    d["mtf_weekly_buy"] = False
    d["mtf_weekly_sell"] = False
    d["mtf_monthly_buy"] = False
    d["mtf_monthly_sell"] = False
    d["mtf_strength_boost"] = 0.0  # Multiplier for signal strength (0.0 to 1.0)
    
    if use_mtf_confirmation:
        # Note: MTF only works with daily data as source
        # Check if we have sufficient data and daily frequency
        try:
            # Try to detect if data is daily by checking index frequency
            # Stock data has gaps (weekends/holidays), so infer_freq often returns None
            # Instead, check the median time delta between bars
            inferred_freq = pd.infer_freq(d.index)
            
            # More robust daily detection: check median delta between bars
            if len(d) >= 2:
                time_deltas = d.index.to_series().diff().dropna()
                median_delta = time_deltas.median()
                # Daily data typically has 1-day median (accounting for weekends)
                is_daily = median_delta <= pd.Timedelta(days=3)  # Allow for weekends
            else:
                is_daily = False
            
            # Need at least 60 days for meaningful weekly/monthly analysis
            has_enough_data = len(d) >= 60
            
            if ARGS_DEBUG:
                print(f"[MTF] Freq={inferred_freq}, is_daily={is_daily}, len={len(d)}, has_enough={has_enough_data}")
            
            if is_daily and has_enough_data:
                if ARGS_DEBUG:
                    print(f"[MTF] Daily data detected ({len(d)} bars), analyzing weekly/monthly...")
                
                # Resample to weekly if enabled
                if mtf_weekly:
                    try:
                        weekly_df = resample_to_higher_timeframe(df[['Open', 'High', 'Low', 'Close', 'Volume']], 'W-FRI')
                        if len(weekly_df) >= 12:  # Need at least ~3 months of weekly data
                            if ARGS_DEBUG:
                                print(f"[MTF] Weekly resampling: {len(weekly_df)} bars, running indicators...")
                            weekly_ind = build_indicators(weekly_df)
                            weekly_sig = generate_signals(
                                weekly_ind,
                                use_timing_filter=False,  # No timing filter for weekly
                                adx_thresh=adx_thresh,
                                vol_ratio_min=vol_ratio_min,
                                z_abs_max=z_abs_max,
                                rsi_buy_max=rsi_buy_max,
                                rsi_sell_min=rsi_sell_min,
                                atr_presence_ratio=atr_presence_ratio,
                                min_components_buy=min_components_buy,
                                min_components_sell=min_components_sell,
                                min_fraction=min_fraction,
                                use_mtf_confirmation=False  # Prevent recursion
                            )
                            # Get the latest weekly signal
                            if len(weekly_sig) > 0:
                                latest_weekly = weekly_sig.iloc[-1]
                                d["mtf_weekly_buy"] = bool(latest_weekly["buy_signal"])
                                d["mtf_weekly_sell"] = bool(latest_weekly["sell_signal"])
                                if ARGS_DEBUG:
                                    print(f"[MTF] Weekly signals: BUY={bool(latest_weekly['buy_signal'])}, SELL={bool(latest_weekly['sell_signal'])}")
                    except Exception:
                        pass  # Silently skip if weekly resampling fails
                
                # Resample to monthly if enabled
                if mtf_monthly:
                    try:
                        monthly_df = resample_to_higher_timeframe(df[['Open', 'High', 'Low', 'Close', 'Volume']], 'ME')
                        if len(monthly_df) >= 4:  # Need at least ~4 months of monthly data
                            monthly_ind = build_indicators(monthly_df)
                            monthly_sig = generate_signals(
                                monthly_ind,
                                use_timing_filter=False,  # No timing filter for monthly
                                adx_thresh=adx_thresh,
                                vol_ratio_min=vol_ratio_min,
                                z_abs_max=z_abs_max,
                                rsi_buy_max=rsi_buy_max,
                                rsi_sell_min=rsi_sell_min,
                                atr_presence_ratio=atr_presence_ratio,
                                min_components_buy=min_components_buy,
                                min_components_sell=min_components_sell,
                                min_fraction=min_fraction,
                                use_mtf_confirmation=False  # Prevent recursion
                            )
                            # Get the latest monthly signal
                            if len(monthly_sig) > 0:
                                latest_monthly = monthly_sig.iloc[-1]
                                d["mtf_monthly_buy"] = bool(latest_monthly["buy_signal"])
                                d["mtf_monthly_sell"] = bool(latest_monthly["sell_signal"])
                                if ARGS_DEBUG:
                                    print(f"[MTF] Monthly signals: BUY={bool(latest_monthly['buy_signal'])}, SELL={bool(latest_monthly['sell_signal'])}")
                    except Exception:
                        pass  # Silently skip if monthly resampling fails
                
                # Calculate MTF strength boost based on timeframe alignment
                # This will be used to enhance the signal strength rating
                for idx in d.index:
                    boost = 0.0
                    is_buy = d.loc[idx, "buy_signal"]
                    is_sell = d.loc[idx, "sell_signal"]
                    
                    if is_buy:
                        if mtf_weekly and d.loc[idx, "mtf_weekly_buy"]:
                            boost += 0.5  # +50% strength for weekly alignment
                        if mtf_monthly and d.loc[idx, "mtf_monthly_buy"]:
                            boost += 0.5  # +50% strength for monthly alignment
                    elif is_sell:
                        if mtf_weekly and d.loc[idx, "mtf_weekly_sell"]:
                            boost += 0.5
                        if mtf_monthly and d.loc[idx, "mtf_monthly_sell"]:
                            boost += 0.5
                    
                    d.loc[idx, "mtf_strength_boost"] = min(1.0, boost)  # Cap at 100% boost
        except Exception:
            pass  # Silently skip MTF if any errors occur

    return d


# ----------------------------
# VWAP backtest utilities
# ----------------------------
def compute_forward_returns(close: pd.Series, horizon: int = 5) -> pd.Series:
    return close.shift(-horizon) / close - 1.0


def boolean_sample_stats(mask: pd.Series, fwd_ret: pd.Series) -> dict:
    sel = fwd_ret[mask.fillna(False)]
    n = int(sel.count())
    if n == 0:
        return {"n": 0, "win_rate": np.nan, "avg_ret": np.nan, "median_ret": np.nan}
    win_rate = float((sel > 0).mean())
    return {
        "n": n,
        "win_rate": win_rate,
        "avg_ret": float(sel.mean()),
        "median_ret": float(sel.median()),
    }


def analyze_signal_strength(df: pd.DataFrame, lookback: int = 100) -> dict:
    """
    Analyze signal strength and provide recommendations for optimal thresholds.
    
    Returns:
        dict: Analysis results including recommended thresholds and performance metrics
    """
    if len(df) < lookback:
        lookback = len(df)
    
    recent_data = df.tail(lookback)
    
    # Analyze score distributions
    buy_scores = recent_data["buy_score"]
    sell_scores = recent_data["sell_score"]
    
    # Calculate score statistics
    buy_stats = {
        "mean": float(buy_scores.mean()),
        "median": float(buy_scores.median()),
        "std": float(buy_scores.std()),
        "min": int(buy_scores.min()),
        "max": int(buy_scores.max()),
        "p25": float(buy_scores.quantile(0.25)),
        "p75": float(buy_scores.quantile(0.75)),
        "p90": float(buy_scores.quantile(0.90)),
    }
    
    sell_stats = {
        "mean": float(sell_scores.mean()),
        "median": float(sell_scores.median()),
        "std": float(sell_scores.std()),
        "min": int(sell_scores.min()),
        "max": int(sell_scores.max()),
        "p25": float(sell_scores.quantile(0.25)),
        "p75": float(sell_scores.quantile(0.75)),
        "p90": float(sell_scores.quantile(0.90)),
    }
    
    # Calculate signal frequency at different thresholds
    total_buy_components = len([col for col in df.columns if col.startswith("buy_") and col not in ["buy_score", "buy_signal", "buy_threshold", "buy_threshold_pct"]])
    total_sell_components = len([col for col in df.columns if col.startswith("sell_") and col not in ["sell_score", "sell_signal", "sell_threshold", "sell_threshold_pct"]])
    
    # Test different threshold levels
    threshold_analysis = {}
    for threshold_pct in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        buy_thresh = max(1, int(threshold_pct * total_buy_components))
        sell_thresh = max(1, int(threshold_pct * total_sell_components))
        
        buy_signals = (buy_scores >= buy_thresh).sum()
        sell_signals = (sell_scores >= sell_thresh).sum()
        
        threshold_analysis[f"{threshold_pct:.0%}"] = {
            "buy_threshold": buy_thresh,
            "sell_threshold": sell_thresh,
            "buy_signals": int(buy_signals),
            "sell_signals": int(sell_signals),
            "buy_frequency": float(buy_signals / len(recent_data)),
            "sell_frequency": float(sell_signals / len(recent_data)),
        }
    
    # Recommend optimal threshold based on signal quality vs quantity trade-off
    # Look for threshold that gives reasonable signal frequency (5-20%) with good performance
    recommended_buy_thresh = max(1, int(buy_stats["p75"]))  # Top 25% of signals
    recommended_sell_thresh = max(1, int(sell_stats["p75"]))  # Top 25% of signals
    
    return {
        "buy_score_stats": buy_stats,
        "sell_score_stats": sell_stats,
        "threshold_analysis": threshold_analysis,
        "recommended_buy_threshold": recommended_buy_thresh,
        "recommended_sell_threshold": recommended_sell_thresh,
        "total_buy_components": total_buy_components,
        "total_sell_components": total_sell_components,
        "analysis_period": lookback,
    }


def vwap_backtest(df: pd.DataFrame, horizon: int = 5) -> dict:
    """
    Simple VWAP conditions:
      - above_vwap: Close > VWAP
      - below_vwap: Close < VWAP
      - cross_up: Close crosses above VWAP
      - cross_down: Close crosses below VWAP
    Evaluate forward returns over 'horizon' bars for each condition.
    """
    if "vwap" not in df.columns:
        raise ValueError("VWAP column missing. Build indicators first.")
    close = df["Close"]
    vwap = df["vwap"]
    fwd = compute_forward_returns(close, horizon=horizon)

    above = close > vwap
    below = close < vwap
    cross_up = above & (~above.shift(1).fillna(False))
    cross_down = below & (~below.shift(1).fillna(False))

    return {
        "horizon": horizon,
        "above_vwap": boolean_sample_stats(above, fwd),
        "below_vwap": boolean_sample_stats(below, fwd),
        "cross_up": boolean_sample_stats(cross_up, fwd),
        "cross_down": boolean_sample_stats(cross_down, fwd),
    }


# ----------------------------
# Component backtest utilities (apples-to-apples)
# ----------------------------
def components_backtest(df: pd.DataFrame, horizon: int = 5) -> dict:
    """
    Evaluate forward returns for each binary component condition used in generate_signals,
    using the same horizon as VWAP backtest.
    Components tested:
      - trend_up (ema_fast > ema_slow)
      - trend_down
      - strong_trend (adx > 20)
      - rsi_buy_ok (rsi < 65)
      - rsi_sell_ok (rsi > 35)
      - has_vol (atr > 0.8 * atr_sma20)
      - vol_ok (vol_ratio > 1.1)
      - don_break_up
      - don_break_down
      - bull_candle
      - bear_candle
      - above_vwap (if present)
      - below_vwap (if present)
    """
    required = [
        "ema_fast","ema_slow","adx","rsi","atr","atr_sma20","vol_ratio",
        "don_upper","don_lower","bull_engulf","bear_engulf","Close"
    ]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing indicator column: {col}")

    fwd = compute_forward_returns(df["Close"], horizon=horizon)

    trend_up = df["ema_fast"] > df["ema_slow"]
    trend_down = df["ema_fast"] < df["ema_slow"]
    strong_trend = df["adx"] > 20.0
    rsi_buy_ok = df["rsi"] < 65
    rsi_sell_ok = df["rsi"] > 35
    has_vol = df["atr"] > (df["atr_sma20"] * 0.8)
    vol_ok = df["vol_ratio"] > 1.1
    don_break_up = df["Close"] > df["don_upper"]
    don_break_down = df["Close"] < df["don_lower"]
    bull_candle = df["bull_engulf"]
    bear_candle = df["bear_engulf"]

    stats = {
        "horizon": horizon,
        "trend_up": boolean_sample_stats(trend_up, fwd),
        "trend_down": boolean_sample_stats(trend_down, fwd),
        "strong_trend": boolean_sample_stats(strong_trend, fwd),
        "rsi_buy_ok": boolean_sample_stats(rsi_buy_ok, fwd),
        "rsi_sell_ok": boolean_sample_stats(rsi_sell_ok, fwd),
        "has_vol": boolean_sample_stats(has_vol, fwd),
        "vol_ok": boolean_sample_stats(vol_ok, fwd),
        "don_break_up": boolean_sample_stats(don_break_up, fwd),
        "don_break_down": boolean_sample_stats(don_break_down, fwd),
        "bull_candle": boolean_sample_stats(bull_candle, fwd),
        "bear_candle": boolean_sample_stats(bear_candle, fwd),
    }

    if "vwap" in df.columns:
        above = df["Close"] > df["vwap"]
        below = df["Close"] < df["vwap"]
        stats["above_vwap"] = boolean_sample_stats(above, fwd)
        stats["below_vwap"] = boolean_sample_stats(below, fwd)

    return stats

# ----------------------------
# Webhook integration
# ----------------------------
def ensure_usd_symbol(symbol: str) -> str:
    return symbol if "/" in symbol else f"{symbol}/USD"


def send_webhook(
    symbol: str,
    action: str,
    url: str = "http://127.0.0.1:5000/",
    mode: str = "text",
    message_text: str | None = None,
) -> Tuple[bool, str]:
    """
    Sends either the original JSON trade payload (for MegaBot compatibility) or a plain text message
    for manual/discretionary workflows. Default remains JSON.

    mode: "json" | "text"
    message_text: used only when mode == "text"; if None, a minimal line will be sent
    """
    try:
        if mode == "text":
            data = message_text or f"{ensure_usd_symbol(symbol)} {action.upper()}"
            resp = requests.post(url, data=data, headers={"Content-Type": "text/plain"}, timeout=5)
        else:
            payload = {"action": action, "symbol": ensure_usd_symbol(symbol)}
            resp = requests.post(url, json=payload, timeout=5)
        return resp.ok, f"{resp.status_code} {resp.text[:200]}"
    except Exception as e:
        return False, str(e)


def send_website_signal(
    symbol: str,
    action: str,
    price: float | None = None,
    quantity: float | None = None,
    source: str = "MAIN_stock_strat11",
    note: str | None = None,
    url: str | None = None,
) -> bool:
    """
    Sends a signal to the website signals receiver for display on the website.
    This is separate from the trading bot webhook.
    """
    try:
        # Get webhook URL from environment variable or use provided/default
        if url is None:
            url = os.getenv("WEBSITE_WEBHOOK_URL", "http://127.0.0.1:5005/webhook")
        
        payload = {
            "action": action,
            "symbol": symbol,  # Keep original format (e.g., "SPY" not "SPY/USD")
            "price": price,
            "quantity": quantity,
            "source": source,
            "note": note,
        }
        resp = requests.post(url, json=payload, timeout=3)
        if resp.ok:
            return True
        else:
            print(f"⚠️  Website signal failed: {resp.status_code}")
            return False
    except Exception as e:
        # Silently fail - don't interrupt main strategy execution
        return False


def append_signal_to_json_file(
    path: Path,
    payload: dict,
    max_entries: int = 1000,
) -> None:
    """
    Append or update a signal in a JSON array file (no exceptions raised).
    For stock signals: Updates existing signal for same symbol+action, or appends if new.
    This ensures signals persist until the next analysis run, even if conditions change.
    Keeps the file trimmed to max_entries.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = []
        else:
            data = []

        # For stock signals: Check if we already have a signal for this symbol+action
        # If so, update it instead of appending (ensures persistence until next analysis)
        symbol = payload.get("symbol", "")
        action = payload.get("action", "")
        source = payload.get("source", "")
        
        # Only deduplicate stock signals (from MAIN_stock_strat)
        is_stock_signal = source and ("stock_strat" in source.lower() or "MAIN_stock" in source)
        
        if is_stock_signal and symbol and action:
            # Find and update existing signal for this symbol+action
            updated = False
            for i, entry in enumerate(data):
                entry_symbol = entry.get("symbol", "")
                entry_action = entry.get("action", "")
                entry_source = entry.get("source", "")
                
                # Match if same symbol and action, and both are stock signals
                if (entry_symbol == symbol and 
                    entry_action == action and 
                    entry_source and 
                    ("stock_strat" in entry_source.lower() or "MAIN_stock" in entry_source)):
                    # Update existing entry with new data (newer timestamp, updated scores, etc.)
                    data[i] = payload
                    updated = True
                    break
            
            if not updated:
                # New signal for this symbol+action, append it
                data.append(payload)
        else:
            # Non-stock signal or missing info, just append
            data.append(payload)
        
        # Trim oldest if oversized (keep most recent)
        # But preserve all stock signals (from MAIN_stock_strat) to ensure they persist through weekends
        stock_signals = [entry for entry in data if entry.get("source", "") and ("stock_strat" in entry.get("source", "").lower() or "MAIN_stock" in entry.get("source", ""))]
        non_stock_signals = [entry for entry in data if entry not in stock_signals]
        
        # Trim non-stock signals first if needed
        if len(non_stock_signals) > max_entries // 2:
            non_stock_signals = non_stock_signals[:max_entries // 2]
        
        # Combine back: stock signals first (to preserve them), then trimmed non-stock signals
        # This ensures stock signals persist even when file gets large
        data = stock_signals + non_stock_signals
        
        # Final trim if still too large (but stock signals take priority)
        if len(data) > max_entries:
            # Keep all stock signals, trim non-stock signals
            if len(stock_signals) < max_entries:
                data = stock_signals + non_stock_signals[:max_entries - len(stock_signals)]
            else:
                # Too many stock signals - keep most recent stock signals only
                data = stock_signals[-max_entries:]

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        # Do not let logging errors interrupt strategy
        pass


# ----------------------------
# CLI / Runner
# ----------------------------

# Default multi-symbol watchlist (used when you pass --symbols explicitly)
# NOTE: The per-symbol parameter overrides live in asset_params.json (if present),
# but that JSON does NOT define the watchlist; it only overrides thresholds/params
# for symbols you choose to scan.
DEFAULT_WATCHLIST_SYMBOLS = [
    # US Sector ETFs
    "XLK", "XLY", "XLP", "XLI", "XLB", "XLRE", "XLU", "XLC", "XLF", "XLV", "XLE",
    # Specialized Sectors
    "SOXX",  # Semiconductors
    # Individual Stocks
    "NVDA",
    # Benchmarks
    "SPY",
    # Precious Metals
    "GLD", "SLV", "PPLT", "PALL",
    # Energy
    "USO",
    # International / Credit
    "EEM", "PCEF", "HYG",
    # Country/Region ETFs
    "MCHI", "INDA", "EWJ", "EWG", "EWT",
    # --- New tickers added (2026-01-21) ---
    "TAN", "GLTR", "IBB", "REMX",
    "AMZN", "AAPL", "CRCL", "ICVT", "ORCL", "INGM", "MSTR",
    "XYLD", "RYLD", "NFTY",
    "EWC",
]

# Rollback note (kept as a comment on purpose):
# If you ever want to revert to the previous watchlist, remove the block labeled
# "New tickers added (2026-01-21)" above. Those new tickers were:
# TAN, GLTR, IBB, REMX, AMZN, AAPL, CRCL, ICVT, XYLD, RYLD, NFTY, ORCL, INGM, MSTR, EWC

def main():
    parser = argparse.ArgumentParser(description="Minimal combined stock strategy → optional webhook")
    parser.add_argument("--symbol", type=str, default="AAPL", help="Ticker symbol (e.g., AAPL)")
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help=(
            "Comma-separated list of symbols to scan. "
            "Tip: Use DEFAULT_WATCHLIST_SYMBOLS for a broad universe "
            "(e.g., XLK,XLY,...,SPY,... + TAN,GLTR,IBB,REMX,AMZN,AAPL,CRCL,ICVT,XYLD,RYLD,NFTY,ORCL,INGM,MSTR,EWC)"
        ),
    )
    parser.add_argument("--start", type=str, default="2015-01-01", help="Start date (default: 2015-01-01 for 10-year dataset to avoid overfitting)")
    parser.add_argument("--end", type=str, default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--interval", type=str, default="1h", choices=["1h", "1d"])
    parser.add_argument("--send-webhook", action="store_true", help="Send last-bar signal")
    parser.add_argument("--webhook-url", type=str, default="http://127.0.0.1:5000/", help="Webhook URL")
    parser.add_argument("--webhook-mode", type=str, choices=["json","text"], default="text", help="Payload type: json (MegaBot-compatible) or text (plain message)")
    # Debug/verbosity toggle
    parser.add_argument("--debug", action="store_true", default=False, help="Enable verbose debug output")
    parser.add_argument("--no-debug", dest="debug", action="store_false", help="Disable verbose debug output")
    # Market breadth summary toggle
    parser.add_argument("--print-breadth", action="store_true", default=True, help="Print market breadth summary across scanned symbols")
    parser.add_argument("--no-print-breadth", dest="print_breadth", action="store_false", help="Do not print market breadth summary")
    # Signal strength/confidence toggle
    parser.add_argument("--print-strength", action="store_true", default=True, help="Include signal strength (1-10) and confidence in outputs")
    parser.add_argument("--no-print-strength", dest="print_strength", action="store_false", help="Do not include strength/confidence")
    # Dynamic voting thresholds
    parser.add_argument("--min-components-buy", type=int, default=None, help="Absolute min components required for BUY (overrides fraction)")
    parser.add_argument("--min-components-sell", type=int, default=None, help="Absolute min components required for SELL (overrides fraction)")
    parser.add_argument("--min-fraction", type=float, default=0.6, help="Fraction of components required if absolute not provided (e.g., 0.6)")
    # Per-asset parameterization
    parser.add_argument("--config", type=str, default=None, help="Path to per-asset JSON config")
    parser.add_argument("--print-effective-params", action="store_true", help="Print effective parameters per asset before signals")
    parser.add_argument("--adx-thresh", type=float, default=None, help="Override ADX threshold")
    parser.add_argument("--vol-ratio-min", type=float, default=None, help="Override volume ratio minimum")
    parser.add_argument("--z-abs-max", type=float, default=None, help="Override |zscore| maximum")
    parser.add_argument("--rsi-buy-max", type=float, default=None, help="Override RSI max for buys")
    parser.add_argument("--rsi-sell-min", type=float, default=None, help="Override RSI min for sells")
    parser.add_argument("--atr-presence-ratio", type=float, default=None, help="Override ATR presence ratio vs ATR-SMA20")
    # VWAP customization
    parser.add_argument("--vwap-buy-above", type=float, default=None, help="Buy when price is X% above VWAP (1.0 = exactly above, 1.02 = 2% above)")
    parser.add_argument("--vwap-sell-below", type=float, default=None, help="Sell when price is X% below VWAP (1.0 = exactly below, 0.98 = 2% below)")
    # Bollinger Bands customization
    parser.add_argument("--bb-squeeze-thresh", type=float, default=None, help="BB squeeze threshold (lower = more sensitive to low volatility)")
    parser.add_argument("--bb-bounce-thresh", type=float, default=None, help="BB bounce threshold (lower = more sensitive to band touches)")
    # Stochastic RSI customization
    parser.add_argument("--stoch-rsi-oversold", type=float, default=None, help="StochRSI oversold threshold (lower = more sensitive)")
    parser.add_argument("--stoch-rsi-overbought", type=float, default=None, help="StochRSI overbought threshold (higher = more sensitive)")
    # MACD customization
    parser.add_argument("--macd-above-zero", action="store_true", default=None, help="Require MACD above zero for buy signals")
    parser.add_argument("--no-macd-above-zero", dest="macd_above_zero", action="store_false", help="Don't require MACD above zero")
    parser.add_argument("--macd-histogram-positive", action="store_true", default=None, help="Require MACD histogram positive for sell signals")
    parser.add_argument("--no-macd-histogram-positive", dest="macd_histogram_positive", action="store_false", help="Don't require MACD histogram positive")
    # Williams %R customization
    parser.add_argument("--williams-r-oversold", type=float, default=None, help="Williams %R oversold threshold (lower = more sensitive, default -80)")
    parser.add_argument("--williams-r-overbought", type=float, default=None, help="Williams %R overbought threshold (higher = more sensitive, default -20)")
    parser.add_argument("--cci-oversold", type=float, default=None, help="CCI oversold threshold (lower = more sensitive, default -100)")
    parser.add_argument("--cci-overbought", type=float, default=None, help="CCI overbought threshold (higher = more sensitive, default 100)")
    parser.add_argument("--mfi-oversold", type=float, default=None, help="MFI oversold threshold (lower = more sensitive, default 20)")
    parser.add_argument("--mfi-overbought", type=float, default=None, help="MFI overbought threshold (higher = more sensitive, default 80)")
    parser.add_argument("--psar-above-price", action="store_true", default=None, help="Require PSAR above price for sell signals")
    parser.add_argument("--no-psar-above-price", dest="psar_above_price", action="store_false", help="Don't require PSAR above price")
    parser.add_argument("--roc-positive", type=float, default=None, help="ROC positive threshold (higher = more sensitive, default 0)")
    parser.add_argument("--roc-negative", type=float, default=None, help="ROC negative threshold (lower = more sensitive, default 0)")
    parser.add_argument("--kc-squeeze-thresh", type=float, default=None, help="Keltner Channels squeeze threshold (lower = more sensitive, default 0.1)")
    parser.add_argument("--kc-bounce-thresh", type=float, default=None, help="Keltner Channels bounce threshold (lower = more sensitive, default 0.2)")
    parser.add_argument("--obv-trend-thresh", type=float, default=None, help="OBV trend threshold (higher = more sensitive, default 0.0)")
    parser.add_argument("--obv-divergence-thresh", type=float, default=None, help="OBV divergence threshold (higher = more sensitive, default 0.1)")
    parser.add_argument("--ichimoku-bullish-cloud", action="store_true", default=None, help="Require price above cloud for bullish signals")
    parser.add_argument("--no-ichimoku-bullish-cloud", dest="ichimoku_bullish_cloud", action="store_false", help="Don't require price above cloud for bullish signals")
    parser.add_argument("--ichimoku-bearish-cloud", action="store_true", default=None, help="Require price below cloud for bearish signals")
    parser.add_argument("--no-ichimoku-bearish-cloud", dest="ichimoku_bearish_cloud", action="store_false", help="Don't require price below cloud for bearish signals")
    parser.add_argument("--ichimoku-tenkan-kijun", action="store_true", default=None, help="Require Tenkan/Kijun relationship for signals")
    parser.add_argument("--no-ichimoku-tenkan-kijun", dest="ichimoku_tenkan_kijun", action="store_false", help="Don't require Tenkan/Kijun relationship for signals")
    parser.add_argument("--ichimoku-chikou", action="store_true", default=None, help="Require Chikou span position for signals")
    parser.add_argument("--no-ichimoku-chikou", dest="ichimoku_chikou", action="store_false", help="Don't require Chikou span position for signals")
    # SuperTrend customization
    parser.add_argument("--supertrend-use", action="store_true", default=None, help="Enable SuperTrend conditions in voting")
    parser.add_argument("--no-supertrend-use", dest="supertrend_use", action="store_false", help="Disable SuperTrend conditions in voting")
    parser.add_argument("--supertrend-dir-required", type=int, default=None, help="SuperTrend direction required (+1 bullish, -1 bearish, 0 ignore)")
    parser.add_argument("--atr-channels-use", action="store_true", default=None, help="Enable ATR Channels conditions in voting")
    parser.add_argument("--no-atr-channels-use", dest="atr_channels_use", action="store_false", help="Disable ATR Channels conditions in voting")
    parser.add_argument("--atr-channels-squeeze-thresh", type=float, default=None, help="ATR Channels squeeze threshold (lower = more sensitive, default 0.1)")
    parser.add_argument("--atr-channels-bounce-thresh", type=float, default=None, help="ATR Channels bounce threshold (lower = more sensitive, default 0.2)")
    parser.add_argument("--volume-profile-use", action="store_true", default=None, help="Enable Volume Profile conditions in voting")
    parser.add_argument("--no-volume-profile-use", dest="volume_profile_use", action="store_false", help="Disable Volume Profile conditions in voting")
    parser.add_argument("--hvn-strength-thresh", type=float, default=None, help="HVN strength threshold (higher = more selective, default 0.3)")
    parser.add_argument("--lvn-strength-thresh", type=float, default=None, help="LVN strength threshold (higher = more selective, default 0.2)")
    parser.add_argument("--vwap-deviation-thresh", type=float, default=None, help="VWAP deviation threshold (higher = more selective, default 0.02)")
    parser.add_argument("--volume-trend-thresh", type=float, default=None, help="Volume trend threshold (higher = more selective, default 0.1)")
    parser.add_argument("--vroc-use", action="store_true", default=None, help="Enable VROC conditions in voting")
    parser.add_argument("--no-vroc-use", dest="vroc_use", action="store_false", help="Disable VROC conditions in voting")
    parser.add_argument("--vroc-positive-thresh", type=float, default=None, help="VROC positive threshold (higher = more selective, default 10.0)")
    parser.add_argument("--vroc-negative-thresh", type=float, default=None, help="VROC negative threshold (lower = more selective, default -10.0)")
    parser.add_argument("--vroc-momentum-thresh", type=float, default=None, help="VROC momentum threshold (higher = more selective, default 5.0)")
    parser.add_argument("--rsi-divergence-use", action="store_true", default=None, help="Enable RSI Divergence conditions in voting")
    parser.add_argument("--no-rsi-divergence-use", dest="rsi_divergence_use", action="store_false", help="Disable RSI Divergence conditions in voting")
    parser.add_argument("--rsi-divergence-lookback", type=int, default=None, help="RSI Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--rsi-divergence-min-swings", type=int, default=None, help="RSI Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--rsi-divergence-min-change", type=float, default=None, help="RSI Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--rsi-divergence-persistence-bars", type=int, default=None, help="RSI Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--macd-divergence-use", action="store_true", default=None, help="Enable MACD Divergence conditions in voting")
    parser.add_argument("--no-macd-divergence-use", dest="macd_divergence_use", action="store_false", help="Disable MACD Divergence conditions in voting")
    parser.add_argument("--macd-divergence-lookback", type=int, default=None, help="MACD Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--macd-divergence-min-swings", type=int, default=None, help="MACD Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--macd-divergence-min-change", type=float, default=None, help="MACD Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--macd-divergence-persistence-bars", type=int, default=None, help="MACD Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--stoch-rsi-divergence-use", action="store_true", default=None, help="Enable Stochastic RSI Divergence conditions in voting")
    parser.add_argument("--no-stoch-rsi-divergence-use", dest="stoch_rsi_divergence_use", action="store_false", help="Disable Stochastic RSI Divergence conditions in voting")
    parser.add_argument("--stoch-rsi-divergence-lookback", type=int, default=None, help="Stochastic RSI Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--stoch-rsi-divergence-min-swings", type=int, default=None, help="Stochastic RSI Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--stoch-rsi-divergence-min-change", type=float, default=None, help="Stochastic RSI Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--stoch-rsi-divergence-persistence-bars", type=int, default=None, help="Stochastic RSI Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--cci-divergence-use", action="store_true", default=None, help="Enable CCI Divergence conditions in voting")
    parser.add_argument("--no-cci-divergence-use", dest="cci_divergence_use", action="store_false", help="Disable CCI Divergence conditions in voting")
    parser.add_argument("--cci-divergence-lookback", type=int, default=None, help="CCI Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--cci-divergence-min-swings", type=int, default=None, help="CCI Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--cci-divergence-min-change", type=float, default=None, help="CCI Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--cci-divergence-persistence-bars", type=int, default=None, help="CCI Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--mfi-divergence-use", action="store_true", default=None, help="Enable MFI Divergence conditions in voting")
    parser.add_argument("--no-mfi-divergence-use", dest="mfi_divergence_use", action="store_false", help="Disable MFI Divergence conditions in voting")
    parser.add_argument("--mfi-divergence-lookback", type=int, default=None, help="MFI Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--mfi-divergence-min-swings", type=int, default=None, help="MFI Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--mfi-divergence-min-change", type=float, default=None, help="MFI Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--mfi-divergence-persistence-bars", type=int, default=None, help="MFI Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--wpr-divergence-use", action="store_true", default=None, help="Enable Williams %R Divergence conditions in voting")
    parser.add_argument("--no-wpr-divergence-use", dest="wpr_divergence_use", action="store_false", help="Disable Williams %R Divergence conditions in voting")
    parser.add_argument("--wpr-divergence-lookback", type=int, default=None, help="Williams %R Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--wpr-divergence-min-swings", type=int, default=None, help="Williams %R Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--wpr-divergence-min-change", type=float, default=None, help="Williams %R Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--wpr-divergence-persistence-bars", type=int, default=None, help="Williams %R Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--roc-divergence-use", action="store_true", default=None, help="Enable ROC Divergence conditions in voting")
    parser.add_argument("--no-roc-divergence-use", dest="roc_divergence_use", action="store_false", help="Disable ROC Divergence conditions in voting")
    parser.add_argument("--roc-divergence-lookback", type=int, default=None, help="ROC Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--roc-divergence-min-swings", type=int, default=None, help="ROC Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--roc-divergence-min-change", type=float, default=None, help="ROC Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--roc-divergence-persistence-bars", type=int, default=None, help="ROC Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--obv-divergence-use", action="store_true", default=None, help="Enable OBV Divergence conditions in voting")
    parser.add_argument("--no-obv-divergence-use", dest="obv_divergence_use", action="store_false", help="Disable OBV Divergence conditions in voting")
    parser.add_argument("--obv-divergence-lookback", type=int, default=None, help="OBV Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--obv-divergence-min-swings", type=int, default=None, help="OBV Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--obv-divergence-min-change", type=float, default=None, help="OBV Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--obv-divergence-persistence-bars", type=int, default=None, help="OBV Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--st-divergence-use", action="store_true", default=None, help="Enable SuperTrend Slope Divergence conditions in voting")
    parser.add_argument("--no-st-divergence-use", dest="st_divergence_use", action="store_false", help="Disable SuperTrend Slope Divergence conditions in voting")
    parser.add_argument("--st-divergence-lookback", type=int, default=None, help="SuperTrend Slope Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--st-divergence-min-swings", type=int, default=None, help="SuperTrend Slope Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--st-divergence-min-change", type=float, default=None, help="SuperTrend Slope Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--st-divergence-persistence-bars", type=int, default=None, help="SuperTrend Slope Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--bb-divergence-use", action="store_true", default=None, help="Enable Bollinger Band Width Divergence conditions in voting")
    parser.add_argument("--no-bb-divergence-use", dest="bb_divergence_use", action="store_false", help="Disable Bollinger Band Width Divergence conditions in voting")
    parser.add_argument("--bb-divergence-lookback", type=int, default=None, help="Bollinger Band Width Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--bb-divergence-min-swings", type=int, default=None, help="Bollinger Band Width Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--bb-divergence-min-change", type=float, default=None, help="Bollinger Band Width Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--bb-divergence-persistence-bars", type=int, default=None, help="Bollinger Band Width Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--vroc-divergence-use", action="store_true", default=None, help="Enable VROC Divergence conditions in voting")
    parser.add_argument("--no-vroc-divergence-use", dest="vroc_divergence_use", action="store_false", help="Disable VROC Divergence conditions in voting")
    parser.add_argument("--vroc-divergence-lookback", type=int, default=None, help="VROC Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--vroc-divergence-min-swings", type=int, default=None, help="VROC Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--vroc-divergence-min-change", type=float, default=None, help="VROC Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--vroc-divergence-persistence-bars", type=int, default=None, help="VROC Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--atr-divergence-use", action="store_true", default=None, help="Enable ATR Divergence conditions in voting")
    parser.add_argument("--no-atr-divergence-use", dest="atr_divergence_use", action="store_false", help="Disable ATR Divergence conditions in voting")
    parser.add_argument("--atr-divergence-lookback", type=int, default=None, help="ATR Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--atr-divergence-min-swings", type=int, default=None, help="ATR Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--atr-divergence-min-change", type=float, default=None, help="ATR Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--atr-divergence-persistence-bars", type=int, default=None, help="ATR Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--adx-divergence-use", action="store_true", default=None, help="Enable ADX Divergence conditions in voting")
    parser.add_argument("--no-adx-divergence-use", dest="adx_divergence_use", action="store_false", help="Disable ADX Divergence conditions in voting")
    parser.add_argument("--adx-divergence-lookback", type=int, default=None, help="ADX Divergence lookback period (higher = more historical analysis, default 20)")
    parser.add_argument("--adx-divergence-min-swings", type=int, default=None, help="ADX Divergence minimum swings required (higher = more selective, default 2)")
    parser.add_argument("--adx-divergence-min-change", type=float, default=None, help="ADX Divergence minimum price change for significant swing (higher = more selective, default 0.02)")
    parser.add_argument("--adx-divergence-persistence-bars", type=int, default=None, help="ADX Divergence persistence bars required (higher = more stable signals, default 3)")
    parser.add_argument("--parabola-use", action="store_true", default=None, help="Enable Parabola Detection conditions in voting")
    parser.add_argument("--no-parabola-use", dest="parabola_use", action="store_false", help="Disable Parabola Detection conditions in voting")
    parser.add_argument("--parabola-lookback", type=int, default=None, help="Parabola lookback period (higher = more historical analysis, default 50)")
    parser.add_argument("--parabola-confidence-threshold", type=float, default=None, help="Parabola minimum R² confidence (higher = more selective, default 0.70)")
    parser.add_argument("--parabola-deviation-threshold", type=float, default=None, help="Parabola price deviation threshold for break detection (higher = more tolerant, default 0.02)")
    parser.add_argument("--parabola-use-atr-filter", action="store_true", default=None, help="Enable ATR volatility filter for parabola detection")
    parser.add_argument("--no-parabola-use-atr-filter", dest="parabola_use_atr_filter", action="store_false", help="Disable ATR volatility filter for parabola detection")
    parser.add_argument("--parabola-use-adx-filter", action="store_true", default=None, help="Enable ADX trend strength filter for parabola detection")
    parser.add_argument("--no-parabola-use-adx-filter", dest="parabola_use_adx_filter", action="store_false", help="Disable ADX trend strength filter for parabola detection")
    parser.add_argument("--parabola-atr-period", type=int, default=None, help="Parabola ATR calculation period (default 14)")
    parser.add_argument("--parabola-adx-period", type=int, default=None, help="Parabola ADX calculation period (default 14)")
    parser.add_argument("--parabola-adx-threshold", type=int, default=None, help="Parabola minimum ADX for trend strength (default 15)")
    parser.add_argument("--parabola-atr-threshold", type=float, default=None, help="Parabola ATR multiplier for volatility filter (default 0.3)")
    parser.add_argument("--parabola-persistence-bars", type=int, default=None, help="Parabola persistence bars after break (default 3)")
    # Multi-Timeframe Confirmation
    parser.add_argument("--use-mtf-confirmation", action="store_true", default=None, help="Enable multi-timeframe confirmation (weekly + monthly)")
    parser.add_argument("--no-use-mtf-confirmation", dest="use_mtf_confirmation", action="store_false", help="Disable multi-timeframe confirmation")
    parser.add_argument("--mtf-weekly", action="store_true", default=None, help="Include weekly timeframe in MTF confirmation")
    parser.add_argument("--no-mtf-weekly", dest="mtf_weekly", action="store_false", help="Exclude weekly timeframe from MTF confirmation")
    # v11 ENHANCEMENT: Automatic threshold adjustment (non-destructive)
    parser.add_argument("--auto-adjust-thresholds", action="store_true", default=False, help="Automatically adjust buy/sell thresholds based on analyze_signal_strength() recommendations")
    parser.add_argument("--auto-adjust-lookback", type=int, default=100, help="Lookback period for automatic threshold adjustment (default: 100 bars)")
    # v11 ENHANCEMENT: Improved exit logic (non-destructive)
    parser.add_argument("--use-improved-exits", action="store_true", default=True, help="Enable improved exit logic: hold longer but allow early exits (ATR trailing stops, confirmation, etc.) - DEFAULT: ENABLED")
    parser.add_argument("--no-improved-exits", dest="use_improved_exits", action="store_false", help="Disable improved exit logic (use original sell signals only)")
    parser.add_argument("--exit-trailing-stop-pct", type=float, default=0.08, help="Fallback trailing stop percentage: exit if price drops X%% from peak (used if ATR not available, default: 0.08 = 8%%)")
    parser.add_argument("--exit-trailing-stop-atr-mult", type=float, default=2.0, help="ATR multiplier for trailing stop (e.g., 2.0 = trail by 2x ATR, default: 2.0)")
    parser.add_argument("--exit-trailing-stop-market-cap", type=str, default="large", choices=["small", "mid", "large"], help="Market cap category for ATR adjustment: small=tighter (0.7x), mid=baseline (1.0x), large=looser (1.3x), default: large")
    parser.add_argument("--exit-confirmation-bars", type=int, default=2, help="Require N consecutive sell signals before exiting (default: 2)")
    parser.add_argument("--exit-min-hold-bars", type=int, default=5, help="Minimum bars to hold position before allowing exit (default: 5)")
    parser.add_argument("--exit-early-on-parabola-break", action="store_true", default=True, help="Exit early when parabola breaks (trend exhaustion detection)")
    parser.add_argument("--no-exit-early-on-parabola-break", dest="exit_early_on_parabola_break", action="store_false", help="Disable early exit on parabola break")
    parser.add_argument("--exit-early-on-adx-drop", action="store_true", default=True, help="Exit early when ADX drops below threshold (trend weakening)")
    parser.add_argument("--no-exit-early-on-adx-drop", dest="exit_early_on_adx_drop", action="store_false", help="Disable early exit on ADX drop")
    parser.add_argument("--exit-adx-drop-threshold", type=float, default=15.0, help="ADX threshold for early exit (default: 15.0)")
    # Hard stop loss (used inside improved exits)
    # Default None so per-asset JSON / built-in defaults can apply without argparse overriding them.
    parser.add_argument("--use-hard-stop-loss", dest="use_hard_stop_loss", action="store_true", default=None, help="Enable hard stop loss (default: use per-asset config or built-in default)")
    parser.add_argument("--no-hard-stop-loss", dest="use_hard_stop_loss", action="store_false", default=None, help="Disable hard stop loss (overrides per-asset config)")
    parser.add_argument("--hard-stop-loss-pct", type=float, default=None, help="Hard stop loss percent from entry (e.g., 0.03 = 3%)")
    parser.add_argument("--hard-stop-min-days", type=int, default=None, help="Minimum holding days before hard stop can trigger (default: 3)")
    # Overextension guard: multiple RSI bearish divergences (block buys for N days)
    parser.add_argument("--rsi-bear-div-block-use", dest="rsi_bear_div_block_use", action="store_true", default=None, help="Enable RSI bearish divergence buy-block (default: enabled)")
    parser.add_argument("--no-rsi-bear-div-block-use", dest="rsi_bear_div_block_use", action="store_false", default=None, help="Disable RSI bearish divergence buy-block")
    parser.add_argument("--rsi-bear-div-block-days", type=int, default=None, help="Days/bars to block buys after trigger (default: 14)")
    parser.add_argument("--rsi-bear-div-event-lookback", type=int, default=None, help="Lookback bars for counting bearish divergence events (default: 120)")
    parser.add_argument("--rsi-bear-div-event-threshold", type=int, default=None, help="Event count threshold to trigger block (default: 3)")
    parser.add_argument("--rsi-bear-div-include-hidden", dest="rsi_bear_div_include_hidden", action="store_true", default=None, help="Include hidden bearish RSI divergence as events (default: true)")
    parser.add_argument("--no-rsi-bear-div-include-hidden", dest="rsi_bear_div_include_hidden", action="store_false", default=None, help="Exclude hidden bearish RSI divergence from events")
    # Conservative take profit + "let it ride" scaling out
    parser.add_argument("--use-conservative-tp", dest="use_conservative_take_profit", action="store_true", default=True, help="Enable conservative take profit (exits portion to lock profits, rest lets it ride, default: enabled)")
    parser.add_argument("--no-conservative-tp", dest="use_conservative_take_profit", action="store_false", help="Disable conservative take profit")
    parser.add_argument("--conservative-tp-profit-pct", type=float, default=0.025, help="Profit % to trigger conservative exit (default: 0.025 = 2.5%%)")
    parser.add_argument("--conservative-tp-exit-pct", type=float, default=0.50, help="Position % to exit at conservative TP (default: 0.50 = 50%%, rest lets it ride)")
    parser.add_argument("--mtf-monthly", action="store_true", default=None, help="Include monthly timeframe in MTF confirmation")
    parser.add_argument("--no-mtf-monthly", dest="mtf_monthly", action="store_false", help="Exclude monthly timeframe from MTF confirmation")
    # Analysis timestamp controls (prevents duplicate runs)
    parser.add_argument("--min-hours-between", type=float, default=MIN_HOURS_BETWEEN_ANALYSES, 
                       help=f"Minimum hours between analysis runs (default: {MIN_HOURS_BETWEEN_ANALYSES} hours, persistent between sessions)")
    parser.add_argument("--force-analysis", action="store_true", default=False,
                       help="Force analysis to run even if done recently (ignores timestamp check)")
    # Loop controls
    parser.add_argument("--loop", dest="loop", action="store_true", default=True, help="Run continuously")
    parser.add_argument("--no-loop", dest="loop", action="store_false", help="Run once and exit")
    parser.add_argument("--sleep-seconds", type=int, default=39600, help="Seconds to sleep between scans when --loop is enabled (default: 39600 = 11 hours)")
    # VWAP backtest options
    parser.add_argument("--vwap-backtest", action="store_true", help="Run VWAP backtest summary on the fetched data")
    parser.add_argument("--vwap-horizon", type=int, default=5, help="Forward return horizon (bars) for VWAP backtest")
    # Components backtest options
    parser.add_argument("--components-backtest", action="store_true", help="Run apples-to-apples component backtest on the fetched data")
    parser.add_argument("--components-horizon", type=int, default=5, help="Forward return horizon (bars) for component backtest")
    # Parameter sweep
    parser.add_argument("--sweep-param", type=str, default=None, help="Name of parameter to sweep (e.g., adx_thresh, rsi_buy_max)")
    parser.add_argument(
        "--sweep-values", type=str, default=None, help="Comma-separated values to test for the sweep parameter"
    )
    parser.add_argument("--sweep-horizon", type=int, default=5, help="Forward return horizon (bars) for sweep evaluation")
    parser.add_argument("--sweep-save-csv", type=str, default=None, help="Optional CSV path to save sweep results")
    # v11 ENHANCEMENT: File logging (always on by default)
    parser.add_argument("--log-file", type=str, default="logs/", help="Log file path or directory (default: 'logs/' creates dated log files). Use '--no-log-file' to disable.")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level (default: INFO)")
    parser.add_argument("--no-log-file", dest="log_file", action="store_const", const=None, help="Disable file logging")
    args = parser.parse_args()

    # When output is piped (nohup/tee), Python buffers prints by default.
    # This makes long backtests/optimizations look "stuck" even while working.
    # Force line-buffered output so logs update in real time.
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(line_buffering=True)
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass
    
    # v11 ENHANCEMENT: Setup file logging if enabled
    log_file_path = None
    if args.log_file:
        log_file_path = Path(args.log_file)
        
        # If log_file is a directory or ends with '/', create dated filename
        if log_file_path.is_dir() or str(log_file_path).endswith('/'):
            # Create logs directory if needed
            log_file_path.mkdir(parents=True, exist_ok=True)
            # Generate dated filename: stock_strat_YYYY-MM-DD.log
            today = datetime.now().strftime('%Y-%m-%d')
            log_file_path = log_file_path / f"stock_strat_{today}.log"
        elif log_file_path.suffix == '':
            # No extension provided, add .log and date
            today = datetime.now().strftime('%Y-%m-%d')
            log_file_path = log_file_path.parent / f"{log_file_path.name}_{today}.log"
        
        # Create log directory if it doesn't exist
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging to write to both console and file
        log_level = getattr(logging, args.log_level.upper(), logging.INFO)
        
        # Create formatter with full date-time timestamp (YYYY-MM-DD HH:MM:SS)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler (append mode to preserve history)
        file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Console handler (only if debug is off, to avoid duplicate output)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Only warnings/errors to console to avoid duplicate
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Write startup header with current date/time to verify freshness
        startup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        header_separator = "=" * 80
        logging.info(header_separator)
        logging.info(f"[MAIN_stock_strat12] SESSION STARTED at {startup_time}")
        logging.info(f"[MAIN_stock_strat12] Log file: {log_file_path}")
        logging.info(f"[MAIN_stock_strat12] Log level: {args.log_level}")
        logging.info(f"[MAIN_stock_strat12] Script version: v12 (with weekend skip)")
        logging.info(header_separator)
    else:
        # No file logging - use print() as before
        logging.basicConfig(level=logging.WARNING, format='%(message)s')
    
    # Set global debug flag so data fetching layer can use it
    global ARGS_DEBUG
    ARGS_DEBUG = args.debug
    
    # Suppress noisy performance warnings (always - they're not critical)
    import warnings
    try:
        import pandas as pd  # already imported above; safe re-import
        warnings.simplefilter("ignore", category=pd.errors.PerformanceWarning)
    except Exception:
        pass

    # Determine symbol list
    symbols: list[str]
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols = [args.symbol]

    # Convenience: if user passes --symbols default_watchlist, expand it.
    # This is intentionally "low tech" and avoids changing defaults.
    if len(symbols) == 1 and symbols[0].strip().lower() in ("default_watchlist", "watchlist", "default"):
        symbols = list(DEFAULT_WATCHLIST_SYMBOLS)

    # Load per-asset config if provided
    # Default config path fallback
    default_cfg_path = os.path.join(os.path.dirname(__file__), "asset_params.json")
    cfg_path = args.config or default_cfg_path
    cfg = {}
    if cfg_path and os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r") as f:
                cfg = json.load(f) or {}
        except Exception:
            cfg = {}

    last_heartbeat = datetime.now()
    heartbeat_interval = timedelta(hours=12)

    def is_in_weekend_halting_period():
        """
        Check if current time is within the weekend halting period.
        Halts processing from Friday 8 PM (20:00) to Sunday 8 PM (20:00).
        This allows Sunday night trading (futures, some stocks) to be processed.
        """
        now = datetime.now()
        current_day = now.weekday()  # 0=Monday, 5=Saturday, 6=Sunday
        current_hour = now.hour
        
        # Saturday: always halt (all day)
        if current_day == 5:  # Saturday
            return True
        
        # Friday after 8 PM: halt
        if current_day == 4 and current_hour >= 20:  # Friday, 8 PM or later
            return True
        
        # Sunday before 8 PM: halt
        if current_day == 6 and current_hour < 20:  # Sunday, before 8 PM
            return True
        
        # All other times: process normally
        return False

    while True:
        # Halt processing during weekend period (Friday 8 PM to Sunday 8 PM)
        # Saturday is completely halted, Sunday night (8 PM+) resumes for futures/Sunday trading
        # Skip weekend check for parameter sweeps (optimization runs)
        if is_in_weekend_halting_period() and not args.sweep_param:
            now = datetime.now()
            current_day = now.weekday()
            current_hour = now.hour
            
            # Calculate next scan time
            if current_day == 4 and current_hour >= 20:  # Friday 8 PM+
                # Next scan is Sunday 8 PM
                days_until_sunday = (6 - current_day) % 7  # 2 days
                hours_until_8pm = (20 - current_hour) + (days_until_sunday * 24)
                if hours_until_8pm <= 0:
                    hours_until_8pm = (20 - current_hour) + 2 * 24
            elif current_day == 5:  # Saturday
                # Next scan is Sunday 8 PM
                hours_until_8pm = (20 - current_hour) + 24  # Sunday 8 PM
            else:  # Sunday before 8 PM
                hours_until_8pm = 20 - current_hour
            
            skip_msg = f"[MAIN_stock_strat12] Halting scan - weekend period (Friday 8 PM - Sunday 8 PM). Current: {now.strftime('%A %H:%M')}, Resumes Sunday 8 PM ({hours_until_8pm:.1f} hours)."
            print(skip_msg)
            if log_file_path:
                logging.info(skip_msg)
            if not args.loop:
                break
            try:
                time.sleep(args.sleep_seconds)
            except KeyboardInterrupt:
                print("Stopping stock strategy...")
                break
            continue
        
        # Check if we should skip analysis due to recent run (unless forced)
        if not args.force_analysis:
            should_skip, skip_reason = should_skip_analysis(min_hours=args.min_hours_between)
            if should_skip:
                skip_msg = f"[MAIN_stock_strat12] ⏭️  Skipping analysis: {skip_reason}"
                print(skip_msg)
                if log_file_path:
                    logging.info(skip_msg)
                if not args.loop:
                    break
                try:
                    time.sleep(args.sleep_seconds)
                except KeyboardInterrupt:
                    print("Stopping stock strategy...")
                    break
                continue
        
        # Breadth tallies for this scan
        breadth_total = 0
        breadth_buy_count = 0
        breadth_sell_count = 0
        breadth_mixed_count = 0
        # Sentiment tallies for universe bias snapshot
        universe_sentiment_sum = 0.0
        universe_sentiment_count = 0
        # Collect symbol results for top signals summary
        # v11.1 ENHANCEMENT: Added sector information to logs - 2025-12-06
        # symbol_results now includes sector: (symbol, close, buy_score, total_buy, sell_score, total_sell, buy_signal, sell_signal, sector)
        symbol_results: list[Tuple[str, float, int, int, int, int, bool, bool, str, float, int, float, float, int, float]] = []  # (symbol, close, buy_score, total_buy, sell_score, total_sell, buy_signal, sell_signal, sector, buy_conviction, buy_persistence, buy_multiplier, sell_conviction, sell_persistence, sell_multiplier)
        
        # Minimal progress message (always prints, even without debug)
        scan_start_time = datetime.now()
        scan_msg = f"[MAIN_stock_strat12] Starting scan: {len(symbols)} symbols at {scan_start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        print(scan_msg)
        if log_file_path:
            logging.info(scan_msg)
        
        # Update the analysis timestamp at the START of analysis (persistent between sessions)
        update_analysis_timestamp()
        
        total_symbols = len(symbols)
        symbols_processed = 0
        symbol_timings: list[Tuple[str, float, bool]] = []

        def _print_progress(symbol: str, duration: float, success: bool, rating_text: Optional[str] = None) -> None:
            """Print minimal progress info with ETA based on recent timings."""
            if not symbol_timings:
                return

            recent_timings = symbol_timings[-5:]  # use last up to 5 symbols for rolling average
            avg_duration = sum(t[1] for t in recent_timings) / len(recent_timings)
            remaining = max(total_symbols - symbols_processed, 0)
            eta_minutes = (avg_duration * remaining) / 60.0 if avg_duration > 0 else 0
            status_icon = "✅" if success else "⚠️"
            rating_segment = f" | {rating_text}" if rating_text else ""
            progress_msg = (
                f"[MAIN_stock_strat12] {status_icon} Progress {symbols_processed}/{total_symbols} | "
                f"{symbol} {duration:.1f}s{rating_segment} | ETA {eta_minutes:.1f} min"
            )
            print(progress_msg)
            if log_file_path:
                logging.info(progress_msg)

        for sym in symbols:
            symbol_start_time = time.perf_counter()
            symbol_failed = False
            # Respect --end for *all* intervals so we can do proper train/validation splits.
            # (Previously, 1d always used "today", which made backtests/sweeps on fixed windows impossible.)
            dynamic_end = args.end

            if args.debug:
                print("")
                print(f"==== {sym} ====")
                print(f"Fetching {sym} {args.interval} data from {args.start} → {dynamic_end} ...")
            try:
                df = fetch_history(sym, args.start, dynamic_end, args.interval)
            except Exception as fe:
                symbol_failed = True
                if args.debug:
                    print(f"Skipping {sym}: {fe}")
                else:
                    # Always print errors even without debug (critical for troubleshooting)
                    error_msg = f"[MAIN_stock_strat12] ⚠️ Skipping {sym}: {fe}"
                    print(error_msg)
                    if log_file_path:
                        logging.warning(error_msg)
                symbol_duration = time.perf_counter() - symbol_start_time
                symbols_processed += 1
                symbol_timings.append((sym, symbol_duration, False))
                _print_progress(sym, symbol_duration, False)
                continue

            ind = build_indicators(df)
            # Resolve effective params
            eff = {
                "adx_thresh": (args.adx_thresh if args.adx_thresh is not None else cfg.get(sym, {}).get("adx_thresh", 22.0)),  # Default updated 2026-01-21 from SPY optimization
                "vol_ratio_min": (args.vol_ratio_min if args.vol_ratio_min is not None else cfg.get(sym, {}).get("vol_ratio_min", 1.1)),
                "z_abs_max": (args.z_abs_max if args.z_abs_max is not None else cfg.get(sym, {}).get("z_abs_max", 2.0)),
                "rsi_buy_max": (args.rsi_buy_max if args.rsi_buy_max is not None else cfg.get(sym, {}).get("rsi_buy_max", 65.0)),
                "rsi_sell_min": (args.rsi_sell_min if args.rsi_sell_min is not None else cfg.get(sym, {}).get("rsi_sell_min", 35.0)),
                "atr_presence_ratio": (args.atr_presence_ratio if args.atr_presence_ratio is not None else cfg.get(sym, {}).get("atr_presence_ratio", 0.8)),
                "min_components_buy": (args.min_components_buy if args.min_components_buy is not None else cfg.get(sym, {}).get("min_components_buy")),
                "min_components_sell": (args.min_components_sell if args.min_components_sell is not None else cfg.get(sym, {}).get("min_components_sell")),
                "min_fraction": (args.min_fraction if args.min_fraction is not None else cfg.get(sym, {}).get("min_fraction", 0.6)),
                "vwap_buy_above": (args.vwap_buy_above if args.vwap_buy_above is not None else cfg.get(sym, {}).get("vwap_buy_above", 1.0)),
                "vwap_sell_below": (args.vwap_sell_below if args.vwap_sell_below is not None else cfg.get(sym, {}).get("vwap_sell_below", 1.0)),
                "bb_squeeze_thresh": (args.bb_squeeze_thresh if args.bb_squeeze_thresh is not None else cfg.get(sym, {}).get("bb_squeeze_thresh", 0.1)),
                "bb_bounce_thresh": (args.bb_bounce_thresh if args.bb_bounce_thresh is not None else cfg.get(sym, {}).get("bb_bounce_thresh", 0.2)),
                "stoch_rsi_oversold": (args.stoch_rsi_oversold if args.stoch_rsi_oversold is not None else cfg.get(sym, {}).get("stoch_rsi_oversold", 20.0)),
                "stoch_rsi_overbought": (args.stoch_rsi_overbought if args.stoch_rsi_overbought is not None else cfg.get(sym, {}).get("stoch_rsi_overbought", 80.0)),
                "macd_above_zero": (args.macd_above_zero if args.macd_above_zero is not None else cfg.get(sym, {}).get("macd_above_zero", True)),
                "macd_histogram_positive": (args.macd_histogram_positive if args.macd_histogram_positive is not None else cfg.get(sym, {}).get("macd_histogram_positive", True)),
                "williams_r_oversold": (args.williams_r_oversold if args.williams_r_oversold is not None else cfg.get(sym, {}).get("williams_r_oversold", -80.0)),
                "williams_r_overbought": (args.williams_r_overbought if args.williams_r_overbought is not None else cfg.get(sym, {}).get("williams_r_overbought", -20.0)),
                "cci_oversold": (args.cci_oversold if args.cci_oversold is not None else cfg.get(sym, {}).get("cci_oversold", -100.0)),
                "cci_overbought": (args.cci_overbought if args.cci_overbought is not None else cfg.get(sym, {}).get("cci_overbought", 100.0)),
                "mfi_oversold": (args.mfi_oversold if args.mfi_oversold is not None else cfg.get(sym, {}).get("mfi_oversold", 20.0)),
                "mfi_overbought": (args.mfi_overbought if args.mfi_overbought is not None else cfg.get(sym, {}).get("mfi_overbought", 80.0)),
                "psar_above_price": (args.psar_above_price if args.psar_above_price is not None else cfg.get(sym, {}).get("psar_above_price", True)),
                "roc_positive": (args.roc_positive if args.roc_positive is not None else cfg.get(sym, {}).get("roc_positive", 0.0)),
                "roc_negative": (args.roc_negative if args.roc_negative is not None else cfg.get(sym, {}).get("roc_negative", 0.0)),
                "kc_squeeze_thresh": (args.kc_squeeze_thresh if args.kc_squeeze_thresh is not None else cfg.get(sym, {}).get("kc_squeeze_thresh", 0.1)),
                "kc_bounce_thresh": (args.kc_bounce_thresh if args.kc_bounce_thresh is not None else cfg.get(sym, {}).get("kc_bounce_thresh", 0.2)),
                "obv_trend_thresh": (args.obv_trend_thresh if args.obv_trend_thresh is not None else cfg.get(sym, {}).get("obv_trend_thresh", 0.0)),
                "obv_divergence_thresh": (args.obv_divergence_thresh if args.obv_divergence_thresh is not None else cfg.get(sym, {}).get("obv_divergence_thresh", 0.1)),
                "ichimoku_bullish_cloud": (args.ichimoku_bullish_cloud if args.ichimoku_bullish_cloud is not None else cfg.get(sym, {}).get("ichimoku_bullish_cloud", True)),
                "ichimoku_bearish_cloud": (args.ichimoku_bearish_cloud if args.ichimoku_bearish_cloud is not None else cfg.get(sym, {}).get("ichimoku_bearish_cloud", True)),
                "ichimoku_tenkan_kijun": (args.ichimoku_tenkan_kijun if args.ichimoku_tenkan_kijun is not None else cfg.get(sym, {}).get("ichimoku_tenkan_kijun", True)),
                "ichimoku_chikou": (args.ichimoku_chikou if args.ichimoku_chikou is not None else cfg.get(sym, {}).get("ichimoku_chikou", True)),
                "supertrend_use": (args.supertrend_use if args.supertrend_use is not None else cfg.get(sym, {}).get("supertrend_use", True)),
                "supertrend_dir_required": (args.supertrend_dir_required if args.supertrend_dir_required is not None else cfg.get(sym, {}).get("supertrend_dir_required", 0)),
                "atr_channels_use": (args.atr_channels_use if args.atr_channels_use is not None else cfg.get(sym, {}).get("atr_channels_use", True)),
                "atr_channels_squeeze_thresh": (args.atr_channels_squeeze_thresh if args.atr_channels_squeeze_thresh is not None else cfg.get(sym, {}).get("atr_channels_squeeze_thresh", 0.1)),
                "atr_channels_bounce_thresh": (args.atr_channels_bounce_thresh if args.atr_channels_bounce_thresh is not None else cfg.get(sym, {}).get("atr_channels_bounce_thresh", 0.2)),
                "volume_profile_use": (args.volume_profile_use if args.volume_profile_use is not None else cfg.get(sym, {}).get("volume_profile_use", True)),
                "hvn_strength_thresh": (args.hvn_strength_thresh if args.hvn_strength_thresh is not None else cfg.get(sym, {}).get("hvn_strength_thresh", 0.3)),
                "lvn_strength_thresh": (args.lvn_strength_thresh if args.lvn_strength_thresh is not None else cfg.get(sym, {}).get("lvn_strength_thresh", 0.2)),
                "vwap_deviation_thresh": (args.vwap_deviation_thresh if args.vwap_deviation_thresh is not None else cfg.get(sym, {}).get("vwap_deviation_thresh", 0.02)),
                "volume_trend_thresh": (args.volume_trend_thresh if args.volume_trend_thresh is not None else cfg.get(sym, {}).get("volume_trend_thresh", 0.1)),
                "vroc_use": (args.vroc_use if args.vroc_use is not None else cfg.get(sym, {}).get("vroc_use", True)),
                "vroc_positive_thresh": (args.vroc_positive_thresh if args.vroc_positive_thresh is not None else cfg.get(sym, {}).get("vroc_positive_thresh", 10.0)),
                "vroc_negative_thresh": (args.vroc_negative_thresh if args.vroc_negative_thresh is not None else cfg.get(sym, {}).get("vroc_negative_thresh", -10.0)),
                "vroc_momentum_thresh": (args.vroc_momentum_thresh if args.vroc_momentum_thresh is not None else cfg.get(sym, {}).get("vroc_momentum_thresh", 5.0)),
                "rsi_divergence_use": (args.rsi_divergence_use if args.rsi_divergence_use is not None else cfg.get(sym, {}).get("rsi_divergence_use", True)),
                "rsi_divergence_lookback": (args.rsi_divergence_lookback if args.rsi_divergence_lookback is not None else cfg.get(sym, {}).get("rsi_divergence_lookback", 20)),
                "rsi_divergence_min_swings": (args.rsi_divergence_min_swings if args.rsi_divergence_min_swings is not None else cfg.get(sym, {}).get("rsi_divergence_min_swings", 2)),
                "rsi_divergence_min_change": (args.rsi_divergence_min_change if args.rsi_divergence_min_change is not None else cfg.get(sym, {}).get("rsi_divergence_min_change", 0.02)),
                "rsi_divergence_persistence_bars": (args.rsi_divergence_persistence_bars if args.rsi_divergence_persistence_bars is not None else cfg.get(sym, {}).get("rsi_divergence_persistence_bars", 3)),
                "macd_divergence_use": (args.macd_divergence_use if args.macd_divergence_use is not None else cfg.get(sym, {}).get("macd_divergence_use", True)),
                "macd_divergence_lookback": (args.macd_divergence_lookback if args.macd_divergence_lookback is not None else cfg.get(sym, {}).get("macd_divergence_lookback", 20)),
                "macd_divergence_min_swings": (args.macd_divergence_min_swings if args.macd_divergence_min_swings is not None else cfg.get(sym, {}).get("macd_divergence_min_swings", 2)),
                "macd_divergence_min_change": (args.macd_divergence_min_change if args.macd_divergence_min_change is not None else cfg.get(sym, {}).get("macd_divergence_min_change", 0.02)),
                "macd_divergence_persistence_bars": (args.macd_divergence_persistence_bars if args.macd_divergence_persistence_bars is not None else cfg.get(sym, {}).get("macd_divergence_persistence_bars", 3)),
                "stoch_rsi_divergence_use": (args.stoch_rsi_divergence_use if args.stoch_rsi_divergence_use is not None else cfg.get(sym, {}).get("stoch_rsi_divergence_use", True)),
                "stoch_rsi_divergence_lookback": (args.stoch_rsi_divergence_lookback if args.stoch_rsi_divergence_lookback is not None else cfg.get(sym, {}).get("stoch_rsi_divergence_lookback", 20)),
                "stoch_rsi_divergence_min_swings": (args.stoch_rsi_divergence_min_swings if args.stoch_rsi_divergence_min_swings is not None else cfg.get(sym, {}).get("stoch_rsi_divergence_min_swings", 2)),
                "stoch_rsi_divergence_min_change": (args.stoch_rsi_divergence_min_change if args.stoch_rsi_divergence_min_change is not None else cfg.get(sym, {}).get("stoch_rsi_divergence_min_change", 0.02)),
                "stoch_rsi_divergence_persistence_bars": (args.stoch_rsi_divergence_persistence_bars if args.stoch_rsi_divergence_persistence_bars is not None else cfg.get(sym, {}).get("stoch_rsi_divergence_persistence_bars", 3)),
                "cci_divergence_use": (args.cci_divergence_use if args.cci_divergence_use is not None else cfg.get(sym, {}).get("cci_divergence_use", True)),
                "cci_divergence_lookback": (args.cci_divergence_lookback if args.cci_divergence_lookback is not None else cfg.get(sym, {}).get("cci_divergence_lookback", 20)),
                "cci_divergence_min_swings": (args.cci_divergence_min_swings if args.cci_divergence_min_swings is not None else cfg.get(sym, {}).get("cci_divergence_min_swings", 2)),
                "cci_divergence_min_change": (args.cci_divergence_min_change if args.cci_divergence_min_change is not None else cfg.get(sym, {}).get("cci_divergence_min_change", 0.02)),
                "cci_divergence_persistence_bars": (args.cci_divergence_persistence_bars if args.cci_divergence_persistence_bars is not None else cfg.get(sym, {}).get("cci_divergence_persistence_bars", 3)),
                "mfi_divergence_use": (args.mfi_divergence_use if args.mfi_divergence_use is not None else cfg.get(sym, {}).get("mfi_divergence_use", True)),
                "mfi_divergence_lookback": (args.mfi_divergence_lookback if args.mfi_divergence_lookback is not None else cfg.get(sym, {}).get("mfi_divergence_lookback", 20)),
                "mfi_divergence_min_swings": (args.mfi_divergence_min_swings if args.mfi_divergence_min_swings is not None else cfg.get(sym, {}).get("mfi_divergence_min_swings", 2)),
                "mfi_divergence_min_change": (args.mfi_divergence_min_change if args.mfi_divergence_min_change is not None else cfg.get(sym, {}).get("mfi_divergence_min_change", 0.02)),
                "mfi_divergence_persistence_bars": (args.mfi_divergence_persistence_bars if args.mfi_divergence_persistence_bars is not None else cfg.get(sym, {}).get("mfi_divergence_persistence_bars", 3)),
                "wpr_divergence_use": (args.wpr_divergence_use if args.wpr_divergence_use is not None else cfg.get(sym, {}).get("wpr_divergence_use", True)),
                "wpr_divergence_lookback": (args.wpr_divergence_lookback if args.wpr_divergence_lookback is not None else cfg.get(sym, {}).get("wpr_divergence_lookback", 20)),
                "wpr_divergence_min_swings": (args.wpr_divergence_min_swings if args.wpr_divergence_min_swings is not None else cfg.get(sym, {}).get("wpr_divergence_min_swings", 2)),
                "wpr_divergence_min_change": (args.wpr_divergence_min_change if args.wpr_divergence_min_change is not None else cfg.get(sym, {}).get("wpr_divergence_min_change", 0.02)),
                "wpr_divergence_persistence_bars": (args.wpr_divergence_persistence_bars if args.wpr_divergence_persistence_bars is not None else cfg.get(sym, {}).get("wpr_divergence_persistence_bars", 3)),
                "roc_divergence_use": (args.roc_divergence_use if args.roc_divergence_use is not None else cfg.get(sym, {}).get("roc_divergence_use", True)),
                "roc_divergence_lookback": (args.roc_divergence_lookback if args.roc_divergence_lookback is not None else cfg.get(sym, {}).get("roc_divergence_lookback", 20)),
                "roc_divergence_min_swings": (args.roc_divergence_min_swings if args.roc_divergence_min_swings is not None else cfg.get(sym, {}).get("roc_divergence_min_swings", 2)),
                "roc_divergence_min_change": (args.roc_divergence_min_change if args.roc_divergence_min_change is not None else cfg.get(sym, {}).get("roc_divergence_min_change", 0.02)),
                "roc_divergence_persistence_bars": (args.roc_divergence_persistence_bars if args.roc_divergence_persistence_bars is not None else cfg.get(sym, {}).get("roc_divergence_persistence_bars", 3)),
                "obv_divergence_use": (args.obv_divergence_use if args.obv_divergence_use is not None else cfg.get(sym, {}).get("obv_divergence_use", True)),
                "obv_divergence_lookback": (args.obv_divergence_lookback if args.obv_divergence_lookback is not None else cfg.get(sym, {}).get("obv_divergence_lookback", 20)),
                "obv_divergence_min_swings": (args.obv_divergence_min_swings if args.obv_divergence_min_swings is not None else cfg.get(sym, {}).get("obv_divergence_min_swings", 2)),
                "obv_divergence_min_change": (args.obv_divergence_min_change if args.obv_divergence_min_change is not None else cfg.get(sym, {}).get("obv_divergence_min_change", 0.02)),
                "obv_divergence_persistence_bars": (args.obv_divergence_persistence_bars if args.obv_divergence_persistence_bars is not None else cfg.get(sym, {}).get("obv_divergence_persistence_bars", 3)),
                "st_divergence_use": (args.st_divergence_use if args.st_divergence_use is not None else cfg.get(sym, {}).get("st_divergence_use", True)),
                "st_divergence_lookback": (args.st_divergence_lookback if args.st_divergence_lookback is not None else cfg.get(sym, {}).get("st_divergence_lookback", 20)),
                "st_divergence_min_swings": (args.st_divergence_min_swings if args.st_divergence_min_swings is not None else cfg.get(sym, {}).get("st_divergence_min_swings", 2)),
                "st_divergence_min_change": (args.st_divergence_min_change if args.st_divergence_min_change is not None else cfg.get(sym, {}).get("st_divergence_min_change", 0.02)),
                "st_divergence_persistence_bars": (args.st_divergence_persistence_bars if args.st_divergence_persistence_bars is not None else cfg.get(sym, {}).get("st_divergence_persistence_bars", 3)),
                "bb_divergence_use": (args.bb_divergence_use if args.bb_divergence_use is not None else cfg.get(sym, {}).get("bb_divergence_use", True)),
                "bb_divergence_lookback": (args.bb_divergence_lookback if args.bb_divergence_lookback is not None else cfg.get(sym, {}).get("bb_divergence_lookback", 20)),
                "bb_divergence_min_swings": (args.bb_divergence_min_swings if args.bb_divergence_min_swings is not None else cfg.get(sym, {}).get("bb_divergence_min_swings", 2)),
                "bb_divergence_min_change": (args.bb_divergence_min_change if args.bb_divergence_min_change is not None else cfg.get(sym, {}).get("bb_divergence_min_change", 0.02)),
                "bb_divergence_persistence_bars": (args.bb_divergence_persistence_bars if args.bb_divergence_persistence_bars is not None else cfg.get(sym, {}).get("bb_divergence_persistence_bars", 3)),
                "vroc_divergence_use": (args.vroc_divergence_use if args.vroc_divergence_use is not None else cfg.get(sym, {}).get("vroc_divergence_use", True)),
                "vroc_divergence_lookback": (args.vroc_divergence_lookback if args.vroc_divergence_lookback is not None else cfg.get(sym, {}).get("vroc_divergence_lookback", 20)),
                "vroc_divergence_min_swings": (args.vroc_divergence_min_swings if args.vroc_divergence_min_swings is not None else cfg.get(sym, {}).get("vroc_divergence_min_swings", 2)),
                "vroc_divergence_min_change": (args.vroc_divergence_min_change if args.vroc_divergence_min_change is not None else cfg.get(sym, {}).get("vroc_divergence_min_change", 0.02)),
                "vroc_divergence_persistence_bars": (args.vroc_divergence_persistence_bars if args.vroc_divergence_persistence_bars is not None else cfg.get(sym, {}).get("vroc_divergence_persistence_bars", 3)),
                "atr_divergence_use": (args.atr_divergence_use if args.atr_divergence_use is not None else cfg.get(sym, {}).get("atr_divergence_use", True)),
                "atr_divergence_lookback": (args.atr_divergence_lookback if args.atr_divergence_lookback is not None else cfg.get(sym, {}).get("atr_divergence_lookback", 20)),
                "atr_divergence_min_swings": (args.atr_divergence_min_swings if args.atr_divergence_min_swings is not None else cfg.get(sym, {}).get("atr_divergence_min_swings", 2)),
                "atr_divergence_min_change": (args.atr_divergence_min_change if args.atr_divergence_min_change is not None else cfg.get(sym, {}).get("atr_divergence_min_change", 0.02)),
                "atr_divergence_persistence_bars": (args.atr_divergence_persistence_bars if args.atr_divergence_persistence_bars is not None else cfg.get(sym, {}).get("atr_divergence_persistence_bars", 3)),
                "adx_divergence_use": (args.adx_divergence_use if args.adx_divergence_use is not None else cfg.get(sym, {}).get("adx_divergence_use", True)),
                "adx_divergence_lookback": (args.adx_divergence_lookback if args.adx_divergence_lookback is not None else cfg.get(sym, {}).get("adx_divergence_lookback", 20)),
                "adx_divergence_min_swings": (args.adx_divergence_min_swings if args.adx_divergence_min_swings is not None else cfg.get(sym, {}).get("adx_divergence_min_swings", 2)),
                "adx_divergence_min_change": (args.adx_divergence_min_change if args.adx_divergence_min_change is not None else cfg.get(sym, {}).get("adx_divergence_min_change", 0.02)),
                "adx_divergence_persistence_bars": (args.adx_divergence_persistence_bars if args.adx_divergence_persistence_bars is not None else cfg.get(sym, {}).get("adx_divergence_persistence_bars", 3)),
                "parabola_use": (args.parabola_use if args.parabola_use is not None else cfg.get(sym, {}).get("parabola_use", True)),
                "parabola_lookback": (args.parabola_lookback if args.parabola_lookback is not None else cfg.get(sym, {}).get("parabola_lookback", 50)),
                "parabola_confidence_threshold": (args.parabola_confidence_threshold if args.parabola_confidence_threshold is not None else cfg.get(sym, {}).get("parabola_confidence_threshold", 0.70)),
                "parabola_deviation_threshold": (args.parabola_deviation_threshold if args.parabola_deviation_threshold is not None else cfg.get(sym, {}).get("parabola_deviation_threshold", 0.02)),
                "parabola_use_atr_filter": (args.parabola_use_atr_filter if args.parabola_use_atr_filter is not None else cfg.get(sym, {}).get("parabola_use_atr_filter", True)),
                "parabola_use_adx_filter": (args.parabola_use_adx_filter if args.parabola_use_adx_filter is not None else cfg.get(sym, {}).get("parabola_use_adx_filter", True)),
                "parabola_atr_period": (args.parabola_atr_period if args.parabola_atr_period is not None else cfg.get(sym, {}).get("parabola_atr_period", 14)),
                "parabola_adx_period": (args.parabola_adx_period if args.parabola_adx_period is not None else cfg.get(sym, {}).get("parabola_adx_period", 14)),
                "parabola_adx_threshold": (args.parabola_adx_threshold if args.parabola_adx_threshold is not None else cfg.get(sym, {}).get("parabola_adx_threshold", 15)),
                "parabola_atr_threshold": (args.parabola_atr_threshold if args.parabola_atr_threshold is not None else cfg.get(sym, {}).get("parabola_atr_threshold", 0.3)),
                "parabola_persistence_bars": (args.parabola_persistence_bars if args.parabola_persistence_bars is not None else cfg.get(sym, {}).get("parabola_persistence_bars", 3)),
                "use_mtf_confirmation": (args.use_mtf_confirmation if args.use_mtf_confirmation is not None else cfg.get(sym, {}).get("use_mtf_confirmation", True)),
                "mtf_weekly": (args.mtf_weekly if args.mtf_weekly is not None else cfg.get(sym, {}).get("mtf_weekly", True)),
                "mtf_monthly": (args.mtf_monthly if args.mtf_monthly is not None else cfg.get(sym, {}).get("mtf_monthly", True)),
                # v11 ENHANCEMENT: Automatic threshold adjustment
                "auto_adjust_thresholds": (args.auto_adjust_thresholds if args.auto_adjust_thresholds else cfg.get(sym, {}).get("auto_adjust_thresholds", False)),
                "auto_adjust_lookback": (args.auto_adjust_lookback if args.auto_adjust_lookback is not None else cfg.get(sym, {}).get("auto_adjust_lookback", 100)),
                # v11 ENHANCEMENT: Improved exit logic
                "use_improved_exits": (args.use_improved_exits if args.use_improved_exits else cfg.get(sym, {}).get("use_improved_exits", False)),
                "exit_trailing_stop_pct": (args.exit_trailing_stop_pct if args.exit_trailing_stop_pct is not None else cfg.get(sym, {}).get("exit_trailing_stop_pct", 0.08)),
                "exit_trailing_stop_atr_mult": (args.exit_trailing_stop_atr_mult if args.exit_trailing_stop_atr_mult is not None else cfg.get(sym, {}).get("exit_trailing_stop_atr_mult", 2.0)),
                "exit_trailing_stop_market_cap": (args.exit_trailing_stop_market_cap if args.exit_trailing_stop_market_cap is not None else cfg.get(sym, {}).get("exit_trailing_stop_market_cap", "large")),
                "exit_confirmation_bars": (args.exit_confirmation_bars if args.exit_confirmation_bars is not None else cfg.get(sym, {}).get("exit_confirmation_bars", 2)),
                "exit_min_hold_bars": (args.exit_min_hold_bars if args.exit_min_hold_bars is not None else cfg.get(sym, {}).get("exit_min_hold_bars", 5)),
                "exit_early_on_parabola_break": (args.exit_early_on_parabola_break if args.exit_early_on_parabola_break is not None else cfg.get(sym, {}).get("exit_early_on_parabola_break", True)),
                "exit_early_on_adx_drop": (args.exit_early_on_adx_drop if args.exit_early_on_adx_drop is not None else cfg.get(sym, {}).get("exit_early_on_adx_drop", True)),
                "exit_adx_drop_threshold": (args.exit_adx_drop_threshold if args.exit_adx_drop_threshold is not None else cfg.get(sym, {}).get("exit_adx_drop_threshold", 15.0)),
                # Hard stop loss (3% from entry, only after 3 days)
                "use_hard_stop_loss": (args.use_hard_stop_loss if args.use_hard_stop_loss is not None else cfg.get(sym, {}).get("use_hard_stop_loss", True)),
                "hard_stop_loss_pct": (args.hard_stop_loss_pct if args.hard_stop_loss_pct is not None else cfg.get(sym, {}).get("hard_stop_loss_pct", 0.03)),
                "hard_stop_min_days": (args.hard_stop_min_days if args.hard_stop_min_days is not None else cfg.get(sym, {}).get("hard_stop_min_days", 3)),
                # Conservative take profit + "let it ride" scaling out
                "use_conservative_take_profit": (args.use_conservative_take_profit if args.use_conservative_take_profit is not None else cfg.get(sym, {}).get("use_conservative_take_profit", True)),
                "conservative_tp_profit_pct": (args.conservative_tp_profit_pct if args.conservative_tp_profit_pct is not None else cfg.get(sym, {}).get("conservative_tp_profit_pct", 0.025)),
                "conservative_tp_exit_pct": (args.conservative_tp_exit_pct if args.conservative_tp_exit_pct is not None else cfg.get(sym, {}).get("conservative_tp_exit_pct", 0.50)),
                # Overextension guard: RSI bearish divergence buy-block
                "rsi_bear_div_block_use": (args.rsi_bear_div_block_use if args.rsi_bear_div_block_use is not None else cfg.get(sym, {}).get("rsi_bear_div_block_use", True)),
                "rsi_bear_div_block_days": (args.rsi_bear_div_block_days if args.rsi_bear_div_block_days is not None else cfg.get(sym, {}).get("rsi_bear_div_block_days", 14)),
                "rsi_bear_div_event_lookback": (args.rsi_bear_div_event_lookback if args.rsi_bear_div_event_lookback is not None else cfg.get(sym, {}).get("rsi_bear_div_event_lookback", 120)),
                "rsi_bear_div_event_threshold": (args.rsi_bear_div_event_threshold if args.rsi_bear_div_event_threshold is not None else cfg.get(sym, {}).get("rsi_bear_div_event_threshold", 3)),
                "rsi_bear_div_include_hidden": (args.rsi_bear_div_include_hidden if args.rsi_bear_div_include_hidden is not None else cfg.get(sym, {}).get("rsi_bear_div_include_hidden", True)),
            }
            if args.print_effective_params and args.debug:
                print(f"Effective params for {sym}: {eff}")
            sig = generate_signals(
                ind,
                use_timing_filter=True,
                adx_thresh=eff["adx_thresh"],
                vol_ratio_min=eff["vol_ratio_min"],
                z_abs_max=eff["z_abs_max"],
                rsi_buy_max=eff["rsi_buy_max"],
                rsi_sell_min=eff["rsi_sell_min"],
                atr_presence_ratio=eff["atr_presence_ratio"],
                min_components_buy=eff["min_components_buy"],
                min_components_sell=eff["min_components_sell"],
                min_fraction=eff["min_fraction"],
                vwap_buy_above=eff["vwap_buy_above"],
                vwap_sell_below=eff["vwap_sell_below"],
                bb_squeeze_thresh=eff["bb_squeeze_thresh"],
                bb_bounce_thresh=eff["bb_bounce_thresh"],
                stoch_rsi_oversold=eff["stoch_rsi_oversold"],
                stoch_rsi_overbought=eff["stoch_rsi_overbought"],
                macd_above_zero=eff["macd_above_zero"],
                macd_histogram_positive=eff["macd_histogram_positive"],
                williams_r_oversold=eff["williams_r_oversold"],
                williams_r_overbought=eff["williams_r_overbought"],
                cci_oversold=eff["cci_oversold"],
                cci_overbought=eff["cci_overbought"],
                mfi_oversold=eff["mfi_oversold"],
                mfi_overbought=eff["mfi_overbought"],
                psar_above_price=eff["psar_above_price"],
                roc_positive=eff["roc_positive"],
                roc_negative=eff["roc_negative"],
                kc_squeeze_thresh=eff["kc_squeeze_thresh"],
                kc_bounce_thresh=eff["kc_bounce_thresh"],
                obv_trend_thresh=eff["obv_trend_thresh"],
                obv_divergence_thresh=eff["obv_divergence_thresh"],
                ichimoku_bullish_cloud=eff["ichimoku_bullish_cloud"],
                ichimoku_bearish_cloud=eff["ichimoku_bearish_cloud"],
                ichimoku_tenkan_kijun=eff["ichimoku_tenkan_kijun"],
                ichimoku_chikou=eff["ichimoku_chikou"],
                supertrend_use=eff["supertrend_use"],
                supertrend_dir_required=eff["supertrend_dir_required"],
                atr_channels_use=eff["atr_channels_use"],
                atr_channels_squeeze_thresh=eff["atr_channels_squeeze_thresh"],
                atr_channels_bounce_thresh=eff["atr_channels_bounce_thresh"],
                volume_profile_use=eff["volume_profile_use"],
                hvn_strength_thresh=eff["hvn_strength_thresh"],
                lvn_strength_thresh=eff["lvn_strength_thresh"],
                vwap_deviation_thresh=eff["vwap_deviation_thresh"],
                volume_trend_thresh=eff["volume_trend_thresh"],
                vroc_use=eff["vroc_use"],
                vroc_positive_thresh=eff["vroc_positive_thresh"],
                vroc_negative_thresh=eff["vroc_negative_thresh"],
                vroc_momentum_thresh=eff["vroc_momentum_thresh"],
                rsi_divergence_use=eff["rsi_divergence_use"],
                rsi_divergence_lookback=eff["rsi_divergence_lookback"],
                rsi_divergence_min_swings=eff["rsi_divergence_min_swings"],
                rsi_divergence_min_change=eff["rsi_divergence_min_change"],
                rsi_divergence_persistence_bars=eff["rsi_divergence_persistence_bars"],
                macd_divergence_use=eff["macd_divergence_use"],
                macd_divergence_lookback=eff["macd_divergence_lookback"],
                macd_divergence_min_swings=eff["macd_divergence_min_swings"],
                macd_divergence_min_change=eff["macd_divergence_min_change"],
                macd_divergence_persistence_bars=eff["macd_divergence_persistence_bars"],
                stoch_rsi_divergence_use=eff["stoch_rsi_divergence_use"],
                stoch_rsi_divergence_lookback=eff["stoch_rsi_divergence_lookback"],
                stoch_rsi_divergence_min_swings=eff["stoch_rsi_divergence_min_swings"],
                stoch_rsi_divergence_min_change=eff["stoch_rsi_divergence_min_change"],
                stoch_rsi_divergence_persistence_bars=eff["stoch_rsi_divergence_persistence_bars"],
                cci_divergence_use=eff["cci_divergence_use"],
                cci_divergence_lookback=eff["cci_divergence_lookback"],
                cci_divergence_min_swings=eff["cci_divergence_min_swings"],
                cci_divergence_min_change=eff["cci_divergence_min_change"],
                cci_divergence_persistence_bars=eff["cci_divergence_persistence_bars"],
                mfi_divergence_use=eff["mfi_divergence_use"],
                mfi_divergence_lookback=eff["mfi_divergence_lookback"],
                mfi_divergence_min_swings=eff["mfi_divergence_min_swings"],
                mfi_divergence_min_change=eff["mfi_divergence_min_change"],
                mfi_divergence_persistence_bars=eff["mfi_divergence_persistence_bars"],
                wpr_divergence_use=eff["wpr_divergence_use"],
                wpr_divergence_lookback=eff["wpr_divergence_lookback"],
                wpr_divergence_min_swings=eff["wpr_divergence_min_swings"],
                wpr_divergence_min_change=eff["wpr_divergence_min_change"],
                wpr_divergence_persistence_bars=eff["wpr_divergence_persistence_bars"],
                roc_divergence_use=eff["roc_divergence_use"],
                roc_divergence_lookback=eff["roc_divergence_lookback"],
                roc_divergence_min_swings=eff["roc_divergence_min_swings"],
                roc_divergence_min_change=eff["roc_divergence_min_change"],
                roc_divergence_persistence_bars=eff["roc_divergence_persistence_bars"],
                obv_divergence_use=eff["obv_divergence_use"],
                obv_divergence_lookback=eff["obv_divergence_lookback"],
                obv_divergence_min_swings=eff["obv_divergence_min_swings"],
                obv_divergence_min_change=eff["obv_divergence_min_change"],
                obv_divergence_persistence_bars=eff["obv_divergence_persistence_bars"],
                st_divergence_use=eff["st_divergence_use"],
                st_divergence_lookback=eff["st_divergence_lookback"],
                st_divergence_min_swings=eff["st_divergence_min_swings"],
                st_divergence_min_change=eff["st_divergence_min_change"],
                st_divergence_persistence_bars=eff["st_divergence_persistence_bars"],
                bb_divergence_use=eff["bb_divergence_use"],
                bb_divergence_lookback=eff["bb_divergence_lookback"],
                bb_divergence_min_swings=eff["bb_divergence_min_swings"],
                bb_divergence_min_change=eff["bb_divergence_min_change"],
                bb_divergence_persistence_bars=eff["bb_divergence_persistence_bars"],
                vroc_divergence_use=eff["vroc_divergence_use"],
                vroc_divergence_lookback=eff["vroc_divergence_lookback"],
                vroc_divergence_min_swings=eff["vroc_divergence_min_swings"],
                vroc_divergence_min_change=eff["vroc_divergence_min_change"],
                vroc_divergence_persistence_bars=eff["vroc_divergence_persistence_bars"],
                atr_divergence_use=eff["atr_divergence_use"],
                atr_divergence_lookback=eff["atr_divergence_lookback"],
                atr_divergence_min_swings=eff["atr_divergence_min_swings"],
                atr_divergence_min_change=eff["atr_divergence_min_change"],
                atr_divergence_persistence_bars=eff["atr_divergence_persistence_bars"],
                adx_divergence_use=eff["adx_divergence_use"],
                adx_divergence_lookback=eff["adx_divergence_lookback"],
                adx_divergence_min_swings=eff["adx_divergence_min_swings"],
                adx_divergence_min_change=eff["adx_divergence_min_change"],
                adx_divergence_persistence_bars=eff["adx_divergence_persistence_bars"],
                parabola_use=eff["parabola_use"],
                parabola_lookback=eff["parabola_lookback"],
                parabola_confidence_threshold=eff["parabola_confidence_threshold"],
                parabola_deviation_threshold=eff["parabola_deviation_threshold"],
                parabola_use_atr_filter=eff["parabola_use_atr_filter"],
                parabola_use_adx_filter=eff["parabola_use_adx_filter"],
                parabola_atr_period=eff["parabola_atr_period"],
                parabola_adx_period=eff["parabola_adx_period"],
                parabola_adx_threshold=eff["parabola_adx_threshold"],
                parabola_atr_threshold=eff["parabola_atr_threshold"],
                parabola_persistence_bars=eff["parabola_persistence_bars"],
                use_mtf_confirmation=eff["use_mtf_confirmation"],
                mtf_weekly=eff["mtf_weekly"],
                mtf_monthly=eff["mtf_monthly"],
                # v11 ENHANCEMENT: Improved exit logic
                use_improved_exits=eff["use_improved_exits"],
                exit_trailing_stop_pct=eff["exit_trailing_stop_pct"],
                exit_trailing_stop_atr_mult=eff["exit_trailing_stop_atr_mult"],
                exit_trailing_stop_market_cap=eff["exit_trailing_stop_market_cap"],
                exit_confirmation_bars=eff["exit_confirmation_bars"],
                exit_min_hold_bars=eff["exit_min_hold_bars"],
                exit_early_on_parabola_break=eff["exit_early_on_parabola_break"],
                exit_early_on_adx_drop=eff["exit_early_on_adx_drop"],
                exit_adx_drop_threshold=eff["exit_adx_drop_threshold"],
                # Hard stop loss (3% from entry, only after 3 days)
                use_hard_stop_loss=eff["use_hard_stop_loss"],
                hard_stop_loss_pct=eff["hard_stop_loss_pct"],
                hard_stop_min_days=eff["hard_stop_min_days"],
                # Conservative take profit + "let it ride" scaling out
                use_conservative_take_profit=eff["use_conservative_take_profit"],
                conservative_tp_profit_pct=eff["conservative_tp_profit_pct"],
                conservative_tp_exit_pct=eff["conservative_tp_exit_pct"],
                rsi_bear_div_block_use=eff["rsi_bear_div_block_use"],
                rsi_bear_div_block_days=eff["rsi_bear_div_block_days"],
                rsi_bear_div_event_lookback=eff["rsi_bear_div_event_lookback"],
                rsi_bear_div_event_threshold=eff["rsi_bear_div_event_threshold"],
                rsi_bear_div_include_hidden=eff["rsi_bear_div_include_hidden"],
            )

            if args.vwap_backtest and args.debug:
                try:
                    stats = vwap_backtest(ind, horizon=args.vwap_horizon)
                    print(
                        "VWAP backtest (horizon={} bars):\n"
                        "  above_vwap:   n={n1} | win={w1:.1%} | avg={a1:.4f} | median={m1:.4f}\n"
                        "  below_vwap:   n={n2} | win={w2:.1%} | avg={a2:.4f} | median={m2:.4f}\n"
                        "  cross_up:     n={n3} | win={w3:.1%} | avg={a3:.4f} | median={m3:.4f}\n"
                        "  cross_down:   n={n4} | win={w4:.1%} | avg={a4:.4f} | median={m4:.4f}".format(
                            stats["horizon"],
                            n1=stats["above_vwap"]["n"], w1=(stats["above_vwap"]["win_rate"] or 0), a1=(stats["above_vwap"]["avg_ret"] or 0), m1=(stats["above_vwap"]["median_ret"] or 0),
                            n2=stats["below_vwap"]["n"], w2=(stats["below_vwap"]["win_rate"] or 0), a2=(stats["below_vwap"]["avg_ret"] or 0), m2=(stats["below_vwap"]["median_ret"] or 0),
                            n3=stats["cross_up"]["n"],   w3=(stats["cross_up"]["win_rate"] or 0),   a3=(stats["cross_up"]["avg_ret"] or 0),   m3=(stats["cross_up"]["median_ret"] or 0),
                            n4=stats["cross_down"]["n"], w4=(stats["cross_down"]["win_rate"] or 0), a4=(stats["cross_down"]["avg_ret"] or 0), m4=(stats["cross_down"]["median_ret"] or 0),
                        )
                    )
                except Exception as e:
                    print(f"VWAP backtest error: {e}")

            if args.components_backtest and args.debug:
                try:
                    comp = components_backtest(ind, horizon=args.components_horizon)
                    def fmt(name):
                        s = comp.get(name, {})
                        return f"{name:14} n={s.get('n',0)} | win={(s.get('win_rate') or 0):.1%} | avg={(s.get('avg_ret') or 0):.4f} | median={(s.get('median_ret') or 0):.4f}"
                    names = [
                        "trend_up","trend_down","strong_trend","rsi_buy_ok","rsi_sell_ok",
                        "has_vol","vol_ok","don_break_up","don_break_down","bull_candle","bear_candle"
                    ]
                    if "above_vwap" in comp:
                        names += ["above_vwap","below_vwap"]
                    print(f"Components backtest (horizon={comp['horizon']} bars):")
                    for nm in names:
                        print("  " + fmt(nm))
                except Exception as e:
                    print(f"Components backtest error: {e}")

            # Single-parameter sweep
            if args.sweep_param and args.sweep_values and args.debug:
                try:
                    # Parse values as floats; cast later for integer params
                    raw_vals = [v.strip() for v in args.sweep_values.split(",") if v.strip()]
                    vals: list[float] = []
                    for v in raw_vals:
                        try:
                            vals.append(float(v))
                        except Exception:
                            pass
                    if not vals:
                        raise ValueError("No sweep values parsed")

                    def cast_value(name: str, value: float):
                        if name in ("min_components_buy", "min_components_sell"):
                            return int(value)
                        if name == "min_fraction":
                            return float(value)
                        return float(value)

                    rows = []
                    close = ind["Close"]
                    fwd = compute_forward_returns(close, horizon=args.sweep_horizon)

                    sweep_t0 = time.perf_counter()
                    durations: list[float] = []
                    total_vals = len(vals)

                    for idx_val, val in enumerate(vals, start=1):
                        iter_t0 = time.perf_counter()
                        eff_local = dict(eff)
                        eff_local[args.sweep_param] = cast_value(args.sweep_param, val)

                        # Keep sweep evaluation consistent with the actual signal run by passing
                        # the full effective parameter set (including feature toggles).
                        sig_local = generate_signals(ind, use_timing_filter=True, **eff_local)

                        buy_mask = sig_local["buy_signal"] & (~sig_local["sell_signal"])  # unambiguous buys
                        sell_mask = sig_local["sell_signal"] & (~sig_local["buy_signal"])  # unambiguous sells

                        buy_stats = boolean_sample_stats(buy_mask, fwd)
                        sell_stats = boolean_sample_stats(sell_mask, fwd)

                        msg = (
                            f"SWEEP {args.sweep_param}={eff_local[args.sweep_param]} | {sym} | "
                            f"BUY n={buy_stats['n']} win={(buy_stats['win_rate'] or 0):.1%} avg={(buy_stats['avg_ret'] or 0):.4f} | "
                            f"SELL n={sell_stats['n']} win={(sell_stats['win_rate'] or 0):.1%} avg={(sell_stats['avg_ret'] or 0):.4f}"
                        )
                        print(msg, flush=True)

                        # Progress + ETA (helps when running under nohup/tee)
                        try:
                            iter_dt = time.perf_counter() - iter_t0
                            durations.append(iter_dt)
                            avg_dt = sum(durations[-5:]) / max(1, len(durations[-5:]))  # rolling avg (last 5)
                            remaining = max(total_vals - idx_val, 0)
                            eta_sec = avg_dt * remaining
                            elapsed = time.perf_counter() - sweep_t0
                            print(
                                f"[sweep] {sym} {args.sweep_param}: {idx_val}/{total_vals} "
                                f"| last {iter_dt:.1f}s | elapsed {elapsed/60:.1f}m | ETA {eta_sec/60:.1f}m",
                                flush=True,
                            )
                        except Exception:
                            pass

                        rows.append({
                            "symbol": sym,
                            "param": args.sweep_param,
                            "value": eff_local[args.sweep_param],
                            "horizon": args.sweep_horizon,
                            "buy_n": buy_stats["n"],
                            "buy_win_rate": buy_stats["win_rate"],
                            "buy_avg_ret": buy_stats["avg_ret"],
                            "buy_median_ret": buy_stats["median_ret"],
                            "sell_n": sell_stats["n"],
                            "sell_win_rate": sell_stats["win_rate"],
                            "sell_avg_ret": sell_stats["avg_ret"],
                            "sell_median_ret": sell_stats["median_ret"],
                        })

                    if args.sweep_save_csv:
                        try:
                            pd.DataFrame(rows).to_csv(args.sweep_save_csv, index=False)
                            print(f"Saved sweep results to {args.sweep_save_csv}", flush=True)
                        except Exception as e:
                            print(f"Could not save sweep CSV: {e}", flush=True)
                except Exception as e:
                    print(f"Sweep error: {e}", flush=True)

            last = sig.iloc[-1]
            last_time = sig.index[-1]
            # Update breadth counters
            try:
                is_buy = bool(last["buy_signal"]) if "buy_signal" in last else False
                is_sell = bool(last["sell_signal"]) if "sell_signal" in last else False
                breadth_total += 1
                if is_buy and is_sell:
                    breadth_mixed_count += 1
                elif is_buy:
                    breadth_buy_count += 1
                elif is_sell:
                    breadth_sell_count += 1
            except Exception:
                pass

            # Compute per-symbol sentiment rating for universe bias snapshot
            sentiment_rating = None
            sentiment_buy_score = None
            sentiment_sell_score = None
            sentiment_total_buy = None
            sentiment_total_sell = None
            try:
                buy_score = int(last.get("buy_score", 0))
                sell_score = int(last.get("sell_score", 0))
                total_buy = int(last.get("total_buy_components", max(buy_score, 1)))
                total_sell = int(last.get("total_sell_components", max(sell_score, 1)))

                buy_norm = min(1.0, max(0.0, buy_score / max(1, total_buy)))
                sell_norm = min(1.0, max(0.0, sell_score / max(1, total_sell)))
                raw_rating = 100.0 * (buy_norm - sell_norm)
                sentiment_rating = int(round(raw_rating))

                sentiment_buy_score = buy_score
                sentiment_sell_score = sell_score
                sentiment_total_buy = total_buy
                sentiment_total_sell = total_sell
            except Exception:
                sentiment_rating = None

            if sentiment_rating is not None:
                universe_sentiment_sum += float(sentiment_rating)
                universe_sentiment_count += 1

            if args.debug:
                print(f"Last bar: {last_time} | Close={last['Close']:.2f} | buy={bool(last['buy_signal'])} | sell={bool(last['sell_signal'])}")
                # Continuous sentiment rating in [-100, 100] based on relative buy/sell votes.
                if sentiment_rating is not None:
                    rating = sentiment_rating
                    buy_score = sentiment_buy_score or 0
                    total_buy = sentiment_total_buy or max(buy_score, 1)
                    sell_score = sentiment_sell_score or 0
                    total_sell = sentiment_total_sell or max(sell_score, 1)

                    if rating >= 40:
                        bias = "strong bullish"
                    elif rating >= 20:
                        bias = "bullish"
                    elif rating > -20:
                        bias = "neutral"
                    elif rating > -40:
                        bias = "bearish"
                    else:
                        bias = "strong bearish"

                    print(
                        f"[sentiment] score={rating:+d}/100 ({bias}) "
                        f"[buy_votes={buy_score}/{total_buy}, sell_votes={sell_score}/{total_sell}]"
                    )

            # Human-readable explanation of signal quality (no webhook format changes)
            side = None
            passed = []  # reset per symbol
            # Blocked-buy candidate: buy threshold met, but suppressed by RSI bearish divergence block.
            blocked_buy_candidate = False
            blocked_buy_reason = ""
            try:
                if bool(last.get("buy_signal_raw", False)) and not bool(last.get("buy_signal", False)):
                    if bool(last.get("buy_blocked_rsi_bear_div", False)):
                        blocked_buy_candidate = True
                        timer = int(last.get("rsi_bear_div_block_timer", 0) or 0)
                        cnt = int(float(last.get("rsi_bear_div_event_count", 0) or 0))
                        blocked_buy_reason = f"BUY threshold met but HIGH divergences detected (RSI bearish divergence block active: {timer}d remaining, events≈{cnt}). Proceed with caution."
            except Exception:
                blocked_buy_candidate = False

            if last["buy_signal"] and not last["sell_signal"]:
                side = "buy"
                component_names = [
                    ("trend_up", bool(last["trend_up"])) ,
                    ("strong_trend", bool(last["strong_trend"])) ,
                    ("rsi_buy_ok", bool(last["rsi_buy_ok"])) ,
                    ("has_vol", bool(last["has_vol"])) ,
                    ("vol_ok", bool(last["vol_ok"])) ,
                    ("don_break_up_or_bull_candle", bool(last["don_break_up"]) or bool(last["bull_candle"])) ,
                    ("z_ok_buy", bool(last["z_ok_buy"])) ,
                    ("not_friday", bool(last["not_friday"])) ,
                ]
                passed = [name for name, ok in component_names if ok]
                if args.debug:
                    print(f"Signal quality: BUY score {int(last['buy_score'])}/8 | passed: {', '.join(passed) if passed else 'none'}")
                    # Multi-timeframe debug info
                    if eff.get("use_mtf_confirmation", True) and args.interval == "1d":
                        weekly_status = "✅" if last.get("mtf_weekly_buy", False) else "❌"
                        monthly_status = "✅" if last.get("mtf_monthly_buy", False) else "❌"
                        print(f"  MTF Alignment: Weekly {weekly_status} | Monthly {monthly_status}")
            elif last["sell_signal"] and not last["buy_signal"]:
                side = "sell"
                component_names = [
                    ("trend_down", bool(last["trend_down"])) ,
                    ("strong_trend", bool(last["strong_trend"])) ,
                    ("rsi_sell_ok", bool(last["rsi_sell_ok"])) ,
                    ("has_vol", bool(last["has_vol"])) ,
                    ("vol_ok", bool(last["vol_ok"])) ,
                    ("don_break_down_or_bear_candle", bool(last["don_break_down"]) or bool(last["bear_candle"])) ,
                    ("z_ok_sell", bool(last["z_ok_sell"])) ,
                    ("not_friday", bool(last["not_friday"])) ,
                ]
                passed = [name for name, ok in component_names if ok]
                if args.debug:
                    print(f"Signal quality: SELL score {int(last['sell_score'])}/8 | passed: {', '.join(passed) if passed else 'none'}")
                    # Multi-timeframe debug info
                    if eff.get("use_mtf_confirmation", True) and args.interval == "1d":
                        weekly_status = "✅" if last.get("mtf_weekly_sell", False) else "❌"
                        monthly_status = "✅" if last.get("mtf_monthly_sell", False) else "❌"
                        print(f"  MTF Alignment: Weekly {weekly_status} | Monthly {monthly_status}")
            else:
                if args.debug:
                    print("Signal quality: neutral/mixed (no unambiguous trade).")
            
            # PERSISTENCE ENHANCEMENT: Website signal file update (stocks)
            # This ensures signals persist until the next analysis run, preventing blank screens
            # Only do this for stock signals (not crypto) and when --send-webhook is enabled
            if args.send_webhook:
                try:
                    signals_file = Path("/Users/olivia2/Documents/GitHub/guitar/web/WebContent/signals/signals.json")
                    now_iso = datetime.utcnow().isoformat() + "Z"
                    
                    # Extract current scores (even if no signal)
                    buy_score = int(last.get("buy_score", 0))
                    sell_score = int(last.get("sell_score", 0))
                    total_buy = int(last.get("total_buy_components", 38))
                    total_sell = int(last.get("total_sell_components", 37))
                    
                    # Extract position sizing data
                    buy_conviction = float(last.get("buy_conviction", 0.0))
                    buy_persistence = int(last.get("buy_persistence", 0))
                    buy_multiplier = float(last.get("buy_position_multiplier", 1.0))
                    sell_conviction = float(last.get("sell_conviction", 0.0))
                    sell_persistence = int(last.get("sell_persistence", 0))
                    sell_multiplier = float(last.get("sell_position_multiplier", 1.0))
                    
                    if side in ("buy", "sell") or blocked_buy_candidate:
                        # Active signal: update with current data
                        note_parts = [f"buy {buy_score}/{total_buy}", f"sell {sell_score}/{total_sell}"]
                        # Only include Strength/MTF text when we actually have an active side (strength computed later).
                        if args.print_strength and side in ("buy", "sell"):
                            note_parts.append(f"Strength={strength}/10{mtf_text}")
                        if blocked_buy_candidate and blocked_buy_reason:
                            note_parts.append(blocked_buy_reason)
                        note_text = " | ".join(note_parts)
                    else:
                        # No active signal: update existing signal with current state (keeps it visible)
                        # Use "neutral" action or keep last action, but update timestamp to show it's current
                        note_parts = [f"buy {buy_score}/{total_buy}", f"sell {sell_score}/{total_sell}", "No active signal"]
                        note_text = " | ".join(note_parts)
                        # Don't change side - keep existing signal visible, just update timestamp
                        # We'll update the existing signal in append_signal_to_json_file
                    
                    # Always write/update signal file to ensure persistence
                    # append_signal_to_json_file will update existing signal for this symbol if it exists
                    if side in ("buy", "sell") or blocked_buy_candidate:
                        # Write active signal OR blocked-buy candidate (for website cards, but won't trigger trading)
                        website_action = side if side in ("buy", "sell") else "buy"
                        append_signal_to_json_file(
                            signals_file,
                            {
                                "action": website_action,
                                "symbol": sym,
                                "price": float(last["Close"]),
                                "quantity": None,
                                "source": "MAIN_stock_strat14",
                                "note": note_text,
                                "timestamp": now_iso,
                                "received_at": now_iso,
                                "id": f"{now_iso}-{sym}-{website_action}",
                                "buy_score": buy_score,
                                "sell_score": sell_score,
                                "total_buy_components": total_buy,
                                "total_sell_components": total_sell,
                                "buy_conviction": buy_conviction,
                                "buy_persistence": buy_persistence,
                                "buy_position_multiplier": buy_multiplier,
                                "sell_conviction": sell_conviction,
                                "sell_persistence": sell_persistence,
                                "sell_position_multiplier": sell_multiplier,
                                # Flags for UI filtering
                                "buy_signal_raw": bool(last.get("buy_signal_raw", False)),
                                "buy_blocked_rsi_bear_div": bool(last.get("buy_blocked_rsi_bear_div", False)),
                                "rsi_bear_div_block_timer": int(last.get("rsi_bear_div_block_timer", 0) or 0),
                            },
                        )
                    # Note: If side is None (no signal), we don't write anything new
                    # The existing signal will remain visible until next analysis
                except Exception:
                    pass  # Don't interrupt main execution if website signal fails

            # v6 ENHANCEMENT: Apply quality filters before printing/acting on signal
            if side in ("buy", "sell"):
                # Calculate signal strength first (needed for filters)
                strength = 1
                strength_text = ""
                mtf_text = ""
                skip_signal = False
                skip_reason = ""
                
                if args.print_strength:
                    try:
                        if side == "buy":
                            score = int(last["buy_score"]) if "buy_score" in last else 0
                            thresh = int(last["buy_threshold"]) if "buy_threshold" in last else score
                            total = int(last.get("total_buy_components", thresh))
                        else:
                            score = int(last["sell_score"]) if "sell_score" in last else 0
                            thresh = int(last["sell_threshold"]) if "sell_threshold" in last else score
                            total = int(last.get("total_sell_components", thresh))
                        over = max(0, score - thresh)
                        denom = max(1, total - thresh)
                        progress = over / denom
                        
                        # Apply MTF boost to strength calculation
                        mtf_boost = float(last.get("mtf_strength_boost", 0.0))
                        boosted_progress = min(1.0, progress + (progress * mtf_boost))  # Boost the progress
                        strength = max(1, min(10, int(round(1 + 9 * boosted_progress))))
                        confidence_pct = boosted_progress
                        strength_text = f" | Strength={strength}/10 | Conf={confidence_pct:.0%}"
                        
                        # Add MTF alignment indicator
                        if eff.get("use_mtf_confirmation", True):
                            mtf_labels = []
                            if side == "buy":
                                if last.get("mtf_weekly_buy", False):
                                    mtf_labels.append("W")
                                if last.get("mtf_monthly_buy", False):
                                    mtf_labels.append("M")
                            else:
                                if last.get("mtf_weekly_sell", False):
                                    mtf_labels.append("W")
                                if last.get("mtf_monthly_sell", False):
                                    mtf_labels.append("M")
                            if mtf_labels:
                                mtf_text = f" | MTF:{'+'.join(mtf_labels)}"
                            elif args.interval == "1d":
                                # MTF is advisory only: print a warning tag but DO NOT block the signal.
                                # This prevents MTF confirmation from collapsing real signal frequency to 0%.
                                mtf_text = " | MTF:D-only (no higher timeframe confirmation)"
                    except Exception:
                        strength_text = ""
                        mtf_text = ""
                
                # v6 FILTER #1: Minimum strength requirement (eliminates weak signals)
                MIN_STRENGTH_REQUIRED = 4
                if not skip_signal and strength < MIN_STRENGTH_REQUIRED:
                    skip_signal = True
                    skip_reason = f"Signal strength too weak ({strength}/10, need ≥{MIN_STRENGTH_REQUIRED}/10)"
                
                # Print signal with filters applied
                if skip_signal:
                    if args.debug:
                        skip_msg = f"⚠️ {sym} {side.upper()} signal SKIPPED: {skip_reason}"
                        print(skip_msg)
                        if log_file_path:
                            logging.warning(skip_msg)
                    side = None  # Clear side to prevent webhook/alerts
                else:
                    signal_msg = f"✅ {sym} {last_time} | {side.upper()} | Close={last['Close']:.2f}{strength_text}{mtf_text}"
                    print(signal_msg)
                    if log_file_path:
                        logging.info(signal_msg)
                    
                    # Send signal to website for display (only for active signals)
                    # Note: Signal file is already updated above for persistence
                    try:
                        # Extract scores for Top 3 signals display
                        buy_score = int(last.get("buy_score", 0))
                        sell_score = int(last.get("sell_score", 0))
                        total_buy = int(last.get("total_buy_components", 38))
                        total_sell = int(last.get("total_sell_components", 37))
                        
                        # Extract position sizing data (v12 enhancement)
                        buy_conviction = float(last.get("buy_conviction", 0.0))
                        buy_persistence = int(last.get("buy_persistence", 0))
                        buy_multiplier = float(last.get("buy_position_multiplier", 1.0))
                        sell_conviction = float(last.get("sell_conviction", 0.0))
                        sell_persistence = int(last.get("sell_persistence", 0))
                        sell_multiplier = float(last.get("sell_position_multiplier", 1.0))
                        
                        # Build note with scores (required for Top 3 signals display)
                        note_parts = [f"buy {buy_score}/{total_buy}", f"sell {sell_score}/{total_sell}"]
                        if args.print_strength:
                            note_parts.append(f"Strength={strength}/10{mtf_text}")
                        note_text = " | ".join(note_parts)
                        
                        send_website_signal(
                            symbol=sym,
                            action=side,
                            price=float(last['Close']),
                            source="MAIN_stock_strat14",
                            note=note_text,
                        )
                    except Exception:
                        pass  # Don't interrupt main execution if website signal fails

            # Signal strength analysis (diagnostic only; does not affect live signals)
            try:
                strength_analysis = analyze_signal_strength(sig, lookback=100)
                if args.debug:
                    lookback_used = int(strength_analysis.get("analysis_period", 100))
                    print(f"\n=== SIGNAL STRENGTH ANALYSIS ===")
                    print(
                        "Buy Score Stats (how many indicator votes BUY signals received over the last "
                        f"{lookback_used} bars): "
                        f"mean={strength_analysis['buy_score_stats']['mean']:.1f}, "
                        f"median={strength_analysis['buy_score_stats']['median']:.1f}, "
                        f"75th percentile={strength_analysis['buy_score_stats']['p75']:.1f}"
                    )
                    print(
                        "Sell Score Stats (indicator votes for SELL signals over the last "
                        f"{lookback_used} bars): "
                        f"mean={strength_analysis['sell_score_stats']['mean']:.1f}, "
                        f"median={strength_analysis['sell_score_stats']['median']:.1f}, "
                        f"75th percentile={strength_analysis['sell_score_stats']['p75']:.1f}"
                    )
                    print(
                        "Current Thresholds (minimum votes required right now for a real signal): "
                        f"Buy={int(last['buy_threshold'])} ({last['buy_threshold_pct']:.1%} of components), "
                        f"Sell={int(last['sell_threshold'])} ({last['sell_threshold_pct']:.1%})"
                    )
                    rec_buy = strength_analysis["recommended_buy_threshold"]
                    rec_view = strength_analysis["recommended_sell_threshold"]
                    print(
                        "Recommended Thresholds (≈75th percentile of past scores): "
                        f"Buy={rec_buy}, Sell={rec_view}"
                    )
                    # How often the recommended thresholds would have fired over the recent window
                    recent = sig.tail(lookback_used)
                    if len(recent) > 0:
                        buy_freq_rec = float((recent["buy_score"] >= rec_buy).sum()) / len(recent)
                        sell_freq_rec = float((recent["sell_score"] >= rec_view).sum()) / len(recent)
                        print(
                            f"At these recommended thresholds over the last {lookback_used} bars: "
                            f"BUY fired {buy_freq_rec:.1%} of bars, SELL fired {sell_freq_rec:.1%}."
                        )

                    print(
                        "\nSignal Frequency Stress‑Test "
                        "(hypothetical: if thresholds were set to the following fractions of total components, "
                        f"what fraction of the last {lookback_used} bars *would* have qualified?):"
                    )

                    def _fmt_freq(freq: float) -> str:
                        # Avoid scary exact 0% / 100% by annotating them explicitly
                        if freq >= 0.995:
                            return "≈100% (every bar)"
                        if freq <= 0.005:
                            return "≈0% (almost none)"
                        return f"{freq:.1%}"

                    for pct, data in strength_analysis["threshold_analysis"].items():
                        bf = data["buy_frequency"]
                        sf = data["sell_frequency"]
                        print(
                            f"  {pct} of components → "
                            f"BUY on {_fmt_freq(bf)} of bars (hits={data['buy_signals']}), "
                            f"SELL on {_fmt_freq(sf)} (hits={data['sell_signals']})"
                        )
            except Exception as e:
                if ARGS_DEBUG:
                    print(f"Signal strength analysis error: {e}")

            # Push notifications for signals (if enabled)
            if PUSH_ALERTS_AVAILABLE and side in ("buy", "sell"):
                try:
                    # Calculate signal strength based on score
                    if side == "buy":
                        signal_strength = last['buy_score'] / last['buy_threshold']
                    else:
                        signal_strength = last['sell_score'] / last['sell_threshold']
                    
                    # Prepare signal data for push notification
                    signal_data = {
                        'buy': side == "buy",
                        'sell': side == "sell",
                        'close_price': f"{last['Close']:.2f}",
                        'signal_quality': f"{side.upper()} score {int(last[f'{side}_score'])}/{8 if side == 'buy' else 7} | passed: {', '.join(passed) if passed else 'none'}",
                        'timestamp': str(last_time),
                        'symbol': sym
                    }
                    if args.print_strength:
                        try:
                            if side == "buy":
                                score = int(last["buy_score"])
                                thresh = int(last["buy_threshold"])
                                total = int(last.get("total_buy_components", thresh))
                            else:
                                score = int(last["sell_score"])
                                thresh = int(last["sell_threshold"])
                                total = int(last.get("total_sell_components", thresh))
                            over = max(0, score - thresh)
                            denom = max(1, total - thresh)
                            progress = over / denom
                            strength10 = max(1, min(10, int(round(1 + 9 * progress))))
                            signal_data['strength_1_10'] = strength10
                            signal_data['confidence_pct'] = f"{progress:.0%}"
                        except Exception:
                            pass
                    
                    # Send push notification
                    push_alerts = PushoverAlerts()
                    push_alerts.send_signal_alert(sym, signal_data, signal_strength)
                    
                    # Queue for daily summary
                    push_alerts.queue_signal(sym, signal_data, signal_strength)
                    
                except Exception as e:
                    print(f"⚠️  Push alert error for {sym}: {e}")
            
            # Fallback to email alerts if push not available
            elif EMAIL_ALERTS_AVAILABLE and side in ("buy", "sell"):
                try:
                    # Calculate signal strength based on score
                    if side == "buy":
                        signal_strength = last['buy_score'] / 8.0
                    else:
                        signal_strength = last['sell_score'] / 7.0  # Sell has 7 components
                    
                    # Prepare signal data for email
                    signal_data = {
                        'buy': side == "buy",
                        'sell': side == "sell",
                        'close_price': f"{last['Close']:.2f}",
                        'signal_quality': f"{side.upper()} score {int(last[f'{side}_score'])}/{8 if side == 'buy' else 7} | passed: {', '.join(passed) if passed else 'none'}",
                        'timestamp': str(last_time),
                        'symbol': sym
                    }
                    if args.print_strength:
                        try:
                            if side == "buy":
                                score = int(last["buy_score"])
                                thresh = int(last["buy_threshold"])
                                total = int(last.get("total_buy_components", thresh))
                            else:
                                score = int(last["sell_score"])
                                thresh = int(last["sell_threshold"])
                                total = int(last.get("total_sell_components", thresh))
                            over = max(0, score - thresh)
                            denom = max(1, total - thresh)
                            progress = over / denom
                            strength10 = max(1, min(10, int(round(1 + 9 * progress))))
                            signal_data['strength_1_10'] = strength10
                            signal_data['confidence_pct'] = f"{progress:.0%}"
                        except Exception:
                            pass
                    # Queue for bundled summary instead of immediate send
                    emailer = StockAlertEmailer()
                    emailer.queue_signal(sym, signal_data, signal_strength)
                    # Also attempt to send scheduled summaries when due (9am and optional EOD)
                    emailer.send_due_summaries()
                    
                except Exception as e:
                    print(f"⚠️  Email alert error for {sym}: {e}")

            # Optional webhook send (per symbol)
            if args.send_webhook and side in ("buy", "sell"):
                text_msg = None
                if args.webhook_mode == "text":
                    if side == "buy":
                        text_msg = (
                            f"MAIN_stock_strat | {ensure_usd_symbol(sym)} BUY | score {int(last['buy_score'])}/8 | "
                            f"passed: {', '.join(passed) if passed else ''} | Close={last['Close']:.2f} | {args.interval} | {last_time}"
                        )
                    else:
                        text_msg = (
                            f"MAIN_stock_strat | {ensure_usd_symbol(sym)} SELL | score {int(last['sell_score'])}/8 | "
                            f"passed: {', '.join(passed) if passed else ''} | Close={last['Close']:.2f} | {args.interval} | {last_time}"
                        )

                ok, msg = send_webhook(sym, side, url=args.webhook_url, mode=args.webhook_mode, message_text=text_msg)
                print(f"Webhook {side.upper()} {sym} → {ok}: {msg}")
            
            # ALWAYS write info signals for ALL symbols (regardless of thresholds or webhook settings)
            # This ensures the website can display Top 3 signals even when symbols don't meet thresholds
            # or when signals are filtered out by strength requirements
            if side is None or side not in ("buy", "sell"):
                # Write info signal for symbols that didn't generate a buy/sell signal
                # or for symbols whose signals were filtered out
                try:
                    now_iso = datetime.utcnow().isoformat() + "Z"
                    signals_file = Path("/Users/olivia2/Documents/GitHub/guitar/web/WebContent/signals/signals.json")
                    buy_score = int(last.get("buy_score", 0))
                    sell_score = int(last.get("sell_score", 0))
                    buy_threshold_actual = int(last.get("buy_threshold", 16))
                    sell_threshold_actual = int(last.get("sell_threshold", 13))
                    total_buy = int(last.get("total_buy_components", 38))
                    total_sell = int(last.get("total_sell_components", 37))
                    
                    # Extract position sizing data (v12 enhancement)
                    buy_conviction = float(last.get("buy_conviction", 0.0))
                    buy_persistence = int(last.get("buy_persistence", 0))
                    buy_multiplier = float(last.get("buy_position_multiplier", 1.0))
                    sell_conviction = float(last.get("sell_conviction", 0.0))
                    sell_persistence = int(last.get("sell_persistence", 0))
                    sell_multiplier = float(last.get("sell_position_multiplier", 1.0))
                    
                    # Determine if threshold was met (for display purposes)
                    threshold_met = (buy_score >= buy_threshold_actual) or (sell_score >= sell_threshold_actual)
                    
                    info_payload = {
                        "action": "info",
                        "symbol": sym,
                        "price": float(last.get("Close", float("nan"))),
                        "quantity": None,
                        "source": "MAIN_stock_strat12",
                        "note": f"{'Above' if threshold_met else 'Below'} thresholds | buy {buy_score}/{buy_threshold_actual} | sell {sell_score}/{sell_threshold_actual}",
                        "timestamp": now_iso,
                        "received_at": now_iso,
                        "id": f"{now_iso}-{sym}-info",
                        "threshold_met": threshold_met,
                        "buy_score": buy_score,
                        "sell_score": sell_score,
                        "total_buy_components": total_buy,
                        "total_sell_components": total_sell,
                        "buy_threshold": buy_threshold_actual,
                        "sell_threshold": sell_threshold_actual,
                        "strength_1_10": int(last.get("strength_1_10", 0)),
                        # Add position sizing data (v12 enhancement)
                        "buy_conviction": buy_conviction,
                        "buy_persistence": buy_persistence,
                        "buy_position_multiplier": buy_multiplier,
                        "sell_conviction": sell_conviction,
                        "sell_persistence": sell_persistence,
                        "sell_position_multiplier": sell_multiplier,
                    }
                    append_signal_to_json_file(signals_file, info_payload, max_entries=5000)
                    if args.debug:
                        print(
                            f"Info signal → {sym}: buy {buy_score}/{buy_threshold_actual}, sell {sell_score}/{sell_threshold_actual}"
                        )
                except Exception:
                    pass  # Don't interrupt main execution if info signal write fails

            rating_text = None
            try:
                buy_score = int(last.get("buy_score", 0))
                sell_score = int(last.get("sell_score", 0))
                total_buy = int(last.get("total_buy_components", max(buy_score, 1)))
                total_sell = int(last.get("total_sell_components", max(sell_score, 1)))
                close_val = float(last.get("Close", float("nan")))
                buy_signal = bool(last.get("buy_signal", False))
                sell_signal = bool(last.get("sell_signal", False))
                # Get thresholds from dataframe (stored by generate_signals)
                buy_threshold_actual = int(last.get("buy_threshold", 16))  # Default to 16 if not found
                sell_threshold_actual = int(last.get("sell_threshold", 13))  # Default to 13 if not found
                # Store thresholds from first symbol (they should be consistent across all symbols)
                if 'scan_thresholds' not in globals():
                    globals()['scan_thresholds'] = {'buy': buy_threshold_actual, 'sell': sell_threshold_actual}
                # Get conviction and persistence data (v12 enhancement)
                buy_conviction = float(last.get("buy_conviction", 0.0))
                buy_persistence = int(last.get("buy_persistence", 0))
                buy_multiplier = float(last.get("buy_position_multiplier", 1.0))
                sell_conviction = float(last.get("sell_conviction", 0.0))
                sell_persistence = int(last.get("sell_persistence", 0))
                sell_multiplier = float(last.get("sell_position_multiplier", 1.0))
                # Get sector from config (v11.1 enhancement - 2025-12-06)
                sector = cfg.get(sym, {}).get("sector", "N/A")
                rating_text = (
                    f"Close={close_val:.2f} | buy {buy_score}/{total_buy} | sell {sell_score}/{total_sell} | Sector={sector}"
                )
                # Store results for top signals summary (includes sector and conviction data)
                symbol_results.append((sym, close_val, buy_score, total_buy, sell_score, total_sell, buy_signal, sell_signal, sector, buy_conviction, buy_persistence, buy_multiplier, sell_conviction, sell_persistence, sell_multiplier))
            except Exception:
                rating_text = None
                # Still store basic info even if parsing fails (includes sector)
                sector = cfg.get(sym, {}).get("sector", "N/A")
                symbol_results.append((sym, float("nan"), 0, 1, 0, 1, False, False, sector, 0.0, 0, 1.0, 0.0, 0, 1.0))

            symbol_duration = time.perf_counter() - symbol_start_time
            symbols_processed += 1
            symbol_timings.append((sym, symbol_duration, not symbol_failed))
            _print_progress(sym, symbol_duration, not symbol_failed, rating_text=rating_text)

        # Print market breadth summary across scanned symbols
        # v6 ENHANCEMENT: Market breadth context for signal quality assessment
        # NOTE: In v6, breadth serves as a market regime indicator to help interpret signal quality
        # Signals that pass strength/MTF filters are already high-quality; breadth confirms market environment
        if args.print_breadth and breadth_total > 0:
            try:
                neutral_count = breadth_total - breadth_buy_count - breadth_sell_count - breadth_mixed_count
                buy_pct = breadth_buy_count / breadth_total
                sell_pct = breadth_sell_count / breadth_total
                mixed_pct = breadth_mixed_count / breadth_total
                neutral_pct = neutral_count / breadth_total
                
                breadth_msg = (
                    f"[MAIN_stock_strat12] Market breadth (N={breadth_total}): "
                    f"BUY {buy_pct:.0%} ({breadth_buy_count}), "
                    f"SELL {sell_pct:.0%} ({breadth_sell_count}), "
                    f"MIXED {mixed_pct:.0%} ({breadth_mixed_count}), "
                    f"NEUTRAL {neutral_pct:.0%} ({neutral_count})"
                )
                
                # v6: Warn if market breadth is very weak (context for traders)
                if buy_pct < 0.30 and breadth_buy_count > 0:
                    print(f"⚠️  WARNING: Market breadth weak for BUY signals ({buy_pct:.0%} < 30%) - proceed with caution")
                if sell_pct < 0.30 and breadth_sell_count > 0:
                    print(f"⚠️  WARNING: Market breadth weak for SELL signals ({sell_pct:.0%} < 30%) - proceed with caution")
            except Exception:
                pass

        # Scan completion summary (always prints, even without debug)
        scan_duration = (datetime.now() - scan_start_time).total_seconds()
        scan_end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        completion_msg = f"[MAIN_stock_strat12] Scan completed at {scan_end_time}: {breadth_total} symbols processed in {scan_duration:.1f}s"
        print(completion_msg)
        if log_file_path:
            logging.info(completion_msg)
        
        # Print top signals summary (sorted by score, like visualization)
        if symbol_results:
            # Get thresholds that were actually used (stored during symbol processing)
            scan_thresholds = globals().get('scan_thresholds', {})
            buy_threshold_used = scan_thresholds.get('buy', 16)  # Default to 16 if not found
            sell_threshold_used = scan_thresholds.get('sell', 13)  # Default to 13 if not found
            
            # Sort by buy_score descending, then by sell_score descending
            buy_signals_sorted = sorted(
                [r for r in symbol_results if r[6]],  # Filter for buy_signal=True
                key=lambda x: (x[2], x[4]),  # Sort by buy_score, then sell_score
                reverse=True
            )
            sell_signals_sorted = sorted(
                [r for r in symbol_results if r[7]],  # Filter for sell_signal=True
                key=lambda x: (x[4], x[2]),  # Sort by sell_score, then buy_score
                reverse=True
            )
            
            # Get highest sell scores that didn't meet threshold (for debugging)
            all_sell_scores = sorted(
                [(r[0], r[4], r[5]) for r in symbol_results],  # (sym, sell_score, total_sell)
                key=lambda x: x[1],
                reverse=True
            )
            
            # Print threshold information
            threshold_msg = f"\n📊 Signal Thresholds: BUY ≥{buy_threshold_used}/38 (≈{buy_threshold_used/38*100:.0f}%), SELL ≥{sell_threshold_used}/37 (≈{sell_threshold_used/37*100:.0f}%)"
            print(threshold_msg)
            if log_file_path:
                logging.info(threshold_msg)
            
            # Print top 3 buy signals
            if buy_signals_sorted:
                print("\n📊 Top 3 BUY Signals (sorted by score):")
                if log_file_path:
                    logging.info("Top 3 BUY Signals (sorted by score):")
                for idx, result in enumerate(buy_signals_sorted[:3], 1):
                    sym, close, buy_score, total_buy, sell_score, total_sell, _, _, sector, buy_conv, buy_persist, buy_mult, _, _, _ = result
                    conviction_str = f" | Conv={buy_conv:.2f} Persist={buy_persist}d Size={buy_mult:.1f}x"
                    threshold_status = "✅" if buy_score >= buy_threshold_used else f"❌ (need {buy_threshold_used})"
                    top_buy_msg = f"  #{idx} {sym:6s} | Close=${close:.2f} | buy {buy_score}/{total_buy} {threshold_status} | sell {sell_score}/{total_sell} | Sector={sector}{conviction_str}"
                    print(top_buy_msg)
                    if log_file_path:
                        logging.info(top_buy_msg)
            
            # Print top 3 sell signals
            if sell_signals_sorted:
                print("\n📊 Top 3 SELL Signals (sorted by score):")
                if log_file_path:
                    logging.info("Top 3 SELL Signals (sorted by score):")
                for idx, result in enumerate(sell_signals_sorted[:3], 1):
                    sym, close, buy_score, total_buy, sell_score, total_sell, _, _, sector, _, _, _, sell_conv, sell_persist, sell_mult = result
                    conviction_str = f" | Conv={sell_conv:.2f} Persist={sell_persist}d Size={sell_mult:.1f}x"
                    threshold_status = "✅" if sell_score >= sell_threshold_used else f"❌ (need {sell_threshold_used})"
                    top_sell_msg = f"  #{idx} {sym:6s} | Close=${close:.2f} | buy {buy_score}/{total_buy} | sell {sell_score}/{total_sell} {threshold_status} | Sector={sector}{conviction_str}"
                    print(top_sell_msg)
                    if log_file_path:
                        logging.info(top_sell_msg)
            else:
                # Show why no sell signals appeared
                if all_sell_scores:
                    top_3_near_sell = all_sell_scores[:3]
                    print(f"\n📊 No SELL Signals (threshold: ≥{sell_threshold_used}/37). Top 3 highest sell scores:")
                    if log_file_path:
                        logging.info(f"No SELL Signals (threshold: ≥{sell_threshold_used}/37). Top 3 highest sell scores:")
                    for idx, (sym, sell_score, total_sell) in enumerate(top_3_near_sell, 1):
                        gap = sell_threshold_used - sell_score
                        near_sell_msg = f"  #{idx} {sym:6s} | sell {sell_score}/{total_sell} (need {gap} more to reach threshold {sell_threshold_used})"
                        print(near_sell_msg)
                        if log_file_path:
                            logging.info(near_sell_msg)
                else:
                    no_sell_msg = f"\n📊 No SELL Signals found (threshold: ≥{sell_threshold_used}/37)"
                    print(no_sell_msg)
                    if log_file_path:
                        logging.info(no_sell_msg)
        
        if log_file_path:
            logging.info("=" * 80)  # Session separator
        
        # Universe-wide sentiment snapshot (always printed once per sweep if any symbols had data)
        if universe_sentiment_count > 0:
            try:
                avg_rating = universe_sentiment_sum / universe_sentiment_count
                avg_rating_int = int(round(avg_rating))
                if avg_rating_int >= 40:
                    universe_bias = "strong bullish"
                elif avg_rating_int >= 20:
                    universe_bias = "bullish"
                elif avg_rating_int > -20:
                    universe_bias = "neutral"
                elif avg_rating_int > -40:
                    universe_bias = "bearish"
                else:
                    universe_bias = "strong bearish"

                print(
                    f"[bias] Universe sentiment {avg_rating_int:+d}/100 ({universe_bias}) "
                    f"based on {universe_sentiment_count} symbols"
                )
            except Exception:
                pass

        # Send daily summary if it's morning and we have push alerts
        if PUSH_ALERTS_AVAILABLE:
            try:
                push_alerts = PushoverAlerts()
                if push_alerts.should_send_morning_summary():
                    push_alerts.send_daily_summary()
            except Exception as e:
                print(f"Daily summary error: {e}")

        now = datetime.now()
        if now - last_heartbeat >= heartbeat_interval:
            print(f"[heartbeat] MAIN_stock_strat7 alive at {now.strftime('%Y-%m-%d %H:%M:%S')} | symbols_processed={breadth_total}")
            last_heartbeat = now

        if not args.loop:
            break
        try:
            time.sleep(args.sleep_seconds)
        except KeyboardInterrupt:
            print("Stopping stock strategy...")
            break


if __name__ == "__main__":
    main()


