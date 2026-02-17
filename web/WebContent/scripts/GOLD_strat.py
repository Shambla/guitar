#!/usr/bin/env python3
"""
cd /Users/olivia2/Desktop/Stock_Strats/
python GOLD_strat.py

Gold (futures) strategy on 1-hour candles:
- Trend: EMA 20 / EMA 50 crossover (direction + triggers)
- Confirmation: price relative to intraday VWAP (daily reset)
- Chop filter: ATR must be "present" to avoid horizontal/boring regimes
- Dollar filter: gold is inversely correlated with the dollar. Default proxy is UUP (ETF); Yahoo's
  ^DX (US Dollar Index) often returns no data. If dollar Close > EMA 12 (dollar strong), allow shorts
  only; if below EMA 12 (dollar weak), allow longs only.
- Session levels (UTC): London 3–8 AM ET (08:00–12:00 UTC) → London High/Low (liquidity range).
  NY Open = 8:20 AM ET proxy = Open of 13:00 UTC bar. Booleans: above_ny_open, above_london_high, below_london_low.
  Mechanical framework: London sweep → reclaim/loss of NY Open → fade (reversion) or NY Open hold → continuation.
  Bias: Gold↑ & DXY↓ = long only; Gold↓ & DXY↑ = short only. Stop beyond sweep extreme; targets LH/LL or extension.

Default symbol is Yahoo Finance continuous gold futures: GC=F

Examples:
  cd /Users/olivia2/Desktop/Stock_Strats
  python3 -u GOLD_strat.py --symbol GC=F --interval 60m --period 90d --backtest
  python3 -u GOLD_strat.py --symbol GC=F --interval 60m --period 30d --loop --sleep-seconds 900

  Optimize N bars backtest for how long it has to cross VWAP
  Trailing stop back test what Percentage %?
"""

from __future__ import annotations

import argparse
import time
import signal
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except Exception as e:  # pragma: no cover
    yf = None

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

# When piping output (e.g., `... | head`), avoid noisy BrokenPipeError.
try:  # pragma: no cover
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except Exception:
    pass


BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)


def _safe_symbol(symbol: str) -> str:
    """Sanitize symbol for use in filenames (e.g. SI=F -> SI_F)."""
    return symbol.replace("/", "_").replace("-", "_").replace("=", "_")


def _cache_path(symbol: str, interval: str, period: str) -> Path:
    return CACHE_DIR / f"cache_{_safe_symbol(symbol)}_{interval}_{period}.csv"


def load_local_legacy_1h_cache(symbol: str) -> Optional[pd.DataFrame]:
    """
    Fallback for environments where yfinance is down:
    reuse existing Stock_Strats `data_cache/{SYMBOL}_*_1h.csv` files (created by other scripts).
    """
    try:
        legacy_dir = BASE_DIR / "data_cache"
        candidates = sorted(legacy_dir.glob(f"{_safe_symbol(symbol)}_*_1h.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            return None
        path = candidates[0]
        df = pd.read_csv(path)
        if df.empty or "Datetime" not in df.columns:
            return None
        df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True, errors="coerce")
        df = df.dropna(subset=["Datetime"]).sort_values("Datetime")
        # Keep the canonical columns we need
        keep = [c for c in ["Datetime", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        df = df[keep].copy()
        df.attrs["symbol_used"] = symbol
        df.attrs["source"] = f"local_legacy_cache:{path.name}"
        return df
    except Exception:
        return None


def load_cache(symbol: str, interval: str, period: str, max_age_minutes: int) -> Optional[pd.DataFrame]:
    path = _cache_path(symbol, interval, period)
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        if df.empty or "Datetime" not in df.columns:
            return None
        df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True, errors="coerce")
        df = df.dropna(subset=["Datetime"]).sort_values("Datetime")
        last_dt = df["Datetime"].iloc[-1]
        if (pd.Timestamp.utcnow() - last_dt) > pd.Timedelta(minutes=max_age_minutes):
            return None
        df.attrs["symbol_used"] = symbol
        df.attrs["source"] = "slv_strat_light_cache"
        return df
    except Exception:
        return None


def save_cache(df: pd.DataFrame, symbol: str, interval: str, period: str) -> None:
    if df is None or df.empty:
        return
    _cache_path(symbol, interval, period).write_text(df.to_csv(index=False), encoding="utf-8")


def _normalize_yf_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize yfinance DataFrame to canonical columns: Datetime, Open, High, Low, Close, Volume."""
    df = df.copy()
    # Flatten MultiIndex columns (e.g. (Close, SI=F) -> Close) so we have single-level column names.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0).astype(str)
    df = df.reset_index().rename(columns=str)
    # yfinance uses "Date" or "Datetime" for the index; after reset_index it becomes a column.
    dt_col = None
    for name in ("Datetime", "Date", "datetime"):
        if name in df.columns:
            dt_col = name
            break
    if dt_col is None and len(df.columns) > 0:
        # First column is often the datetime index (unnamed)
        first = df.columns[0]
        if pd.api.types.is_datetime64_any_dtype(df[first]) or "date" in str(first).lower():
            dt_col = first
    if dt_col and dt_col != "Datetime":
        df = df.rename(columns={dt_col: "Datetime"})
    df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True, errors="coerce")
    df = df.dropna(subset=["Datetime"]).sort_values("Datetime")
    return df


def fetch_ohlcv(
    symbol: str,
    interval: str,
    period: str,
    max_cache_age_minutes: int = 30,
    fallback_symbols: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Fetch OHLCV with lightweight caching.
    If yfinance is flaky (common), we try:
      1) yf.download()
      2) yf.Ticker(symbol).history()
      3) fallback symbols (e.g., SLV ETF) if provided
      4) stale cache
    """
    if fallback_symbols is None:
        fallback_symbols = []

    symbols_to_try = [symbol] + [s for s in fallback_symbols if s and s != symbol]

    if yf is None:
        raise RuntimeError("yfinance not installed; install it or run from the Stock_Strats venv.")

    last_err: Optional[Exception] = None

    for sym in symbols_to_try:
        cached = load_cache(sym, interval, period, max_age_minutes=max_cache_age_minutes)
        if cached is not None:
            cached.attrs["symbol_used"] = sym
            return cached

        print(f"🌐 Fetching {sym} ({interval}, {period}) via yfinance…", flush=True)

        for attempt in range(3):
            try:
                # auto_adjust=False: keep OHLC as-is (silences FutureWarning; we use raw for VWAP/ATR).
                # group_by="ticker" + single symbol often gives flat columns; flatten MultiIndex in _normalize_yf_df if not.
                df = yf.download(
                    sym,
                    interval=interval,
                    period=period,
                    progress=False,
                    threads=False,
                    auto_adjust=False,
                )
                if df is None or df.empty:
                    raise RuntimeError("Empty dataframe from yfinance download()")
                df = _normalize_yf_df(df)
                save_cache(df, sym, interval, period)
                df.attrs["symbol_used"] = sym
                df.attrs["source"] = "yfinance_download"
                return df
            except Exception as exc:
                last_err = exc
                wait_s = 2 ** attempt
                print(f"❌ yfinance download() error ({attempt+1}/3): {exc} – retrying in {wait_s}s", flush=True)
                time.sleep(wait_s)

        # Some yfinance failures are specific to download(); history() can still work.
        try:
            t = yf.Ticker(sym)
            df2 = t.history(period=period, interval=interval)
            if df2 is not None and not df2.empty:
                df2 = _normalize_yf_df(df2)
                save_cache(df2, sym, interval, period)
                df2.attrs["symbol_used"] = sym
                df2.attrs["source"] = "yfinance_history"
                print("✅ Fetched via yfinance history()", flush=True)
                return df2
        except Exception as exc:
            last_err = exc

        # Fall back to stale cache for this symbol if present
        stale = _cache_path(sym, interval, period)
        if stale.exists():
            try:
                df = pd.read_csv(stale)
                if "Datetime" in df.columns:
                    df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True, errors="coerce")
                df.attrs["symbol_used"] = sym
                print(f"⚠️ Using stale cache for {sym} because of: {last_err}", flush=True)
                return df
            except Exception:
                pass

        print(f"⚠️ Failed to fetch {sym}; trying next symbol (if any).", flush=True)

        # Last-resort fallback: local legacy 1h cache files.
        # If the user asked for 1h-ish bars, try loading `data_cache/{SYMBOL}_*_1h.csv`.
        if interval.lower() in ("1h", "60m", "60min", "1hr"):
            legacy = load_local_legacy_1h_cache(sym)
            if legacy is not None and not legacy.empty:
                print(f"✅ Loaded local legacy 1h cache for {sym} ({legacy.attrs.get('source')})", flush=True)
                return legacy

    raise RuntimeError(f"Failed to fetch any symbol {symbols_to_try}: {last_err}")


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def compute_intraday_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Intraday VWAP reset daily (UTC date). For futures, this is a reasonable proxy for a session VWAP.
    """
    d = df.sort_values("Datetime").copy()
    d["date"] = pd.to_datetime(d["Datetime"], utc=True).dt.date
    typical = (d["High"].astype(float) + d["Low"].astype(float) + d["Close"].astype(float)) / 3.0
    vol = d["Volume"].astype(float).replace(0, np.nan)
    pv = typical * vol
    vwap = pv.groupby(d["date"]).cumsum() / vol.groupby(d["date"]).cumsum()
    return vwap.ffill().rename("VWAP")


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    close = df["Close"].astype(float)
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    return atr.rename("ATR")


# Session boundaries (UTC) for gold — aligned with mechanical London/NY framework:
# - London session (gold): 3:00 AM – 8:00 AM ET = liquidity range; mark London High (LH) / London Low (LL).
#   In UTC (EST): 08:00–12:00 inclusive (3,4,5,6,7 AM ET). 8 AM ET = 13:00 UTC (NY open).
# - NY session open: 8:20 AM ET COMEX gold open; we use Open of 13:00 UTC bar (8 AM ET) as proxy.
#   Acts as VWAP-style anchor early in the session.
# Logic: London sets range; NY hunts liquidity. Sweep of LH/LL then reclaim/loss of NY Open → fade (reversion).
#        NY Open hold + acceptance above/below London range → continuation. Bias: Gold↑ & DXY↓ = long only; inverse = short.
NY_OPEN_HOUR_UTC = 13   # 8 AM ET (8:20 COMEX proxy)
LONDON_START_HOUR_UTC = 8   # 3 AM ET
LONDON_END_HOUR_UTC = 12    # 7 AM ET (London ends before 8 AM ET)


def compute_session_levels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add NY session open and London session high/low (liquidity levels) to the dataframe (Datetime must be UTC).
    London = 3–8 AM ET (08:00–12:00 UTC). NY Open = Open of 13:00 UTC bar (8:20 AM ET proxy).
    Adds columns: ny_session_open, above_ny_open, london_high, london_low, above_london_high, below_london_low.
    Use for: sweep of LL/LH → reclaim/loss of NY Open → entry; stop beyond sweep extreme; targets LH/LL or extension.
    """
    d = df.copy()
    dt = pd.to_datetime(d["Datetime"], utc=True, errors="coerce")
    d["_date"] = dt.dt.date
    d["_hour"] = dt.dt.hour

    # NY session open = Open of the first bar at 13:00 UTC each day. Merge backward so each bar gets the last 13:00 open.
    ny_bars = d.loc[d["_hour"] == NY_OPEN_HOUR_UTC, ["Datetime", "Open"]].copy()
    ny_bars = ny_bars.rename(columns={"Open": "ny_session_open"}).drop_duplicates(subset=["Datetime"])
    if ny_bars.empty:
        d["ny_session_open"] = np.nan
    else:
        d_sorted = d.sort_values("Datetime").reset_index(drop=True)
        ny_sorted = ny_bars.sort_values("Datetime")
        merged = pd.merge_asof(
            d_sorted[["Datetime"]],
            ny_sorted,
            on="Datetime",
            direction="backward",
        )
        d["ny_session_open"] = merged["ny_session_open"].reindex(d.index).values
    d["above_ny_open"] = (d["Close"].astype(float) > d["ny_session_open"]).fillna(False)

    # London session high/low: 08:00–16:00 UTC. Per date: full session high/low; within session use expanding.
    d["_in_london"] = d["_hour"].between(LONDON_START_HOUR_UTC, LONDON_END_HOUR_UTC, inclusive="both")
    d["_after_london"] = d["_hour"] > LONDON_END_HOUR_UTC
    d["_before_london"] = d["_hour"] < LONDON_START_HOUR_UTC

    london_bars = d[d["_in_london"]].sort_values("Datetime")
    if london_bars.empty:
        d["london_high"] = np.nan
        d["london_low"] = np.nan
    else:
        london_bars = london_bars.copy()
        london_bars["london_high"] = london_bars.groupby("_date")["High"].transform(lambda x: x.astype(float).cummax())
        london_bars["london_low"] = london_bars.groupby("_date")["Low"].transform(lambda x: x.astype(float).cummin())
        # Full session high/low per date (for after_london and before_london)
        full = london_bars.groupby("_date").agg(lh_full=("High", "max"), ll_full=("Low", "min"))
        dates_list = sorted(full.index.unique())
        date_to_prev = {dte: dates_list[i - 1] for i, dte in enumerate(dates_list) if i > 0}

        d["london_high"] = np.nan
        d["london_low"] = np.nan
        # Within London: merge expanding high/low from london_bars (by Datetime)
        in_london = d["_in_london"]
        d.loc[in_london, "london_high"] = d.loc[in_london, "Datetime"].map(
            london_bars.set_index("Datetime")["london_high"]
        )
        d.loc[in_london, "london_low"] = d.loc[in_london, "Datetime"].map(
            london_bars.set_index("Datetime")["london_low"]
        )
        after = d["_after_london"]
        before = d["_before_london"]
        d.loc[after, "london_high"] = d.loc[after, "_date"].map(full["lh_full"])
        d.loc[after, "london_low"] = d.loc[after, "_date"].map(full["ll_full"])
        d.loc[before, "london_high"] = d.loc[before, "_date"].map(date_to_prev).map(full["lh_full"])
        d.loc[before, "london_low"] = d.loc[before, "_date"].map(date_to_prev).map(full["ll_full"])
    d["above_london_high"] = (d["Close"].astype(float) > d["london_high"]).fillna(False)
    d["below_london_low"] = (d["Close"].astype(float) < d["london_low"]).fillna(False)

    d.drop(columns=["_date", "_hour", "_in_london", "_after_london", "_before_london"], inplace=True, errors="ignore")
    return d


@dataclass
class StrategyParams:
    ema_fast: int = 20
    ema_slow: int = 50
    atr_period: int = 14
    atr_presence_ratio: float = 0.90  # ATR must be >= ATR_SMA * ratio
    atr_sma_period: int = 50
    atr_min_pct: float = 0.0015  # ATR/Close must be >= this (avoid chop)
    stop_atr_mult: float = 2.0
    take_atr_mult: float = 3.0
    trailing_stop_pct: float = 0.01  # Percentage-based trailing stop (fallback if ATR not available)
    trailing_stop_atr_mult: float = 0.5  # ATR-based trailing stop multiplier (optimized 2026-01-21: 0.5x ATR best net PnL after $6/trade commission)
    min_hold_bars: int = 10  # Minimum bars to hold position before allowing exit (optimized 2026-01-21: 10 bars best net PnL, prevents premature exits)
    vwap_exit_bars: int = 1  # Require N consecutive bars below/above VWAP before exiting (default: 1 = immediate)
    commission_entry: float = 3.0  # Commission cost to enter a contract ($)
    commission_exit: float = 3.0  # Commission cost to exit a contract ($)

    # DXY (dollar) filter: gold is inversely correlated with the dollar.
    # If DXY Close > DXY EMA 12 (dollar strong) -> bearish for gold (allow shorts, block longs).
    dxy_symbol: str = "^DX"  # Yahoo symbol for US Dollar Index
    dxy_ema_period: int = 12  # 60-minute candle EMA period for DXY
    use_dxy_filter: bool = True  # If False, ignore DXY (e.g. when DXY fetch fails)

    # 10Y yield (proxy: ^TNX) — used for True/False checklist context.
    tenyr_symbol: str = "^TNX"  # Yahoo symbol for 10Y Treasury Yield (x10)
    tenyr_ema_period: int = 12  # 60-minute candle EMA period for 10Y yield
    use_tenyr: bool = True  # If False, skip 10Y yield fetch/merge


def _fetch_dxy(
    interval: str,
    period: str,
    max_cache_age_minutes: int,
    dxy_symbol: str,
) -> Optional[pd.DataFrame]:
    """
    Fetch dollar proxy OHLC (same interval/period as gold). Returns None on failure.
    When dxy_symbol is ^DX, we try UUP first (Yahoo often returns 404 for ^DX), then ^DX as fallback.
    """
    if yf is None:
        return None
    try:
        # Yahoo's ^DX (US Dollar Index) frequently returns 404 / "no data"; avoid 3 retries by trying UUP first.
        if dxy_symbol.strip().upper() == "^DX":
            df = fetch_ohlcv(
                "UUP",
                interval,
                period,
                max_cache_age_minutes=max_cache_age_minutes,
                fallback_symbols=["^DX"],
            )
        else:
            df = fetch_ohlcv(
                dxy_symbol,
                interval,
                period,
                max_cache_age_minutes=max_cache_age_minutes,
                fallback_symbols=["UUP"],
            )
        return df
    except Exception:
        return None


def _fetch_tenyr(
    interval: str,
    period: str,
    max_cache_age_minutes: int,
    tenyr_symbol: str,
) -> Optional[pd.DataFrame]:
    """Fetch 10Y Treasury Yield OHLC with same interval/period as gold. Returns None on failure."""
    if yf is None:
        return None
    try:
        df = fetch_ohlcv(
            tenyr_symbol,
            interval,
            period,
            max_cache_age_minutes=max_cache_age_minutes,
            fallback_symbols=["^TNX", "IEF"],  # ^TNX primary; IEF ETF fallback
        )
        return df
    except Exception:
        return None


def _merge_dxy_into_gold(gold_df: pd.DataFrame, dxy_df: pd.DataFrame, p: StrategyParams) -> pd.DataFrame:
    """
    Merge DXY Close and DXY EMA12 onto the gold DataFrame by Datetime.
    Adds column dxy_above_ema12: True when DXY Close > DXY EMA12 (dollar strong -> bearish for gold).
    """
    d = gold_df.copy()
    dxy = dxy_df.copy()
    dxy.columns = [str(c) for c in dxy.columns]
    if "Datetime" not in dxy.columns or "Close" not in dxy.columns:
        d["dxy_above_ema12"] = False
        return d
    dxy["Datetime"] = pd.to_datetime(dxy["Datetime"], utc=True, errors="coerce")
    dxy = dxy.dropna(subset=["Datetime"]).sort_values("Datetime")
    dxy["DXY_Close"] = dxy["Close"].astype(float)
    dxy["DXY_EMA12"] = ema(dxy["DXY_Close"], p.dxy_ema_period)
    dxy_merge = dxy[["Datetime", "DXY_Close", "DXY_EMA12"]].copy()
    d["Datetime"] = pd.to_datetime(d["Datetime"], utc=True, errors="coerce")
    d_sorted = d.sort_values("Datetime")
    merged = pd.merge_asof(
        d_sorted,
        dxy_merge.sort_values("Datetime"),
        on="Datetime",
        direction="backward",
        suffixes=("", "_dxy"),
    )
    merged["dxy_above_ema12"] = (merged["DXY_Close"] > merged["DXY_EMA12"]).fillna(False)
    return merged.reindex(d.index)


def _merge_tenyr_into_gold(gold_df: pd.DataFrame, tenyr_df: pd.DataFrame, p: StrategyParams) -> pd.DataFrame:
    """
    Merge 10Y Treasury Yield Close and EMA onto the gold DataFrame by Datetime.
    Adds column tenyr_above_ema: True when 10Y Close > 10Y EMA (yield rising/above trend).
    """
    d = gold_df.copy()
    y = tenyr_df.copy()
    y.columns = [str(c) for c in y.columns]
    if "Datetime" not in y.columns or "Close" not in y.columns:
        d["tenyr_above_ema"] = False
        return d
    y["Datetime"] = pd.to_datetime(y["Datetime"], utc=True, errors="coerce")
    y = y.dropna(subset=["Datetime"]).sort_values("Datetime")
    y["TENYR_Close"] = y["Close"].astype(float)
    y["TENYR_EMA"] = ema(y["TENYR_Close"], p.tenyr_ema_period)
    y_merge = y[["Datetime", "TENYR_Close", "TENYR_EMA"]].copy()
    d["Datetime"] = pd.to_datetime(d["Datetime"], utc=True, errors="coerce")
    d_sorted = d.sort_values("Datetime")
    merged = pd.merge_asof(
        d_sorted,
        y_merge.sort_values("Datetime"),
        on="Datetime",
        direction="backward",
        suffixes=("", "_tenyr"),
    )
    merged["tenyr_above_ema"] = (merged["TENYR_Close"] > merged["TENYR_EMA"]).fillna(False)
    return merged.reindex(d.index)


def build_indicators(
    df: pd.DataFrame,
    p: StrategyParams,
    dxy_df: Optional[pd.DataFrame] = None,
    tenyr_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    d = df.copy()
    d.columns = [str(c) for c in d.columns]

    d["Close"] = d["Close"].astype(float)
    d["EMA_FAST"] = ema(d["Close"], p.ema_fast)
    d["EMA_SLOW"] = ema(d["Close"], p.ema_slow)
    d["VWAP"] = compute_intraday_vwap(d)
    d["ATR"] = compute_atr(d, p.atr_period)
    d["ATR_SMA"] = d["ATR"].rolling(p.atr_sma_period, min_periods=1).mean()
    d["ATR_PCT"] = (d["ATR"] / d["Close"]).replace([np.inf, -np.inf], np.nan).fillna(0.0)

    d["trend_up"] = d["EMA_FAST"] > d["EMA_SLOW"]
    d["trend_down"] = d["EMA_FAST"] < d["EMA_SLOW"]
    # Use pandas' nullable boolean to avoid FutureWarning on downcasting after shift() introduces NA.
    prev_up = d["trend_up"].shift(1).astype("boolean").fillna(False).astype(bool)
    prev_down = d["trend_down"].shift(1).astype("boolean").fillna(False).astype(bool)
    d["cross_up"] = d["trend_up"].astype(bool) & (~prev_up)
    d["cross_down"] = d["trend_down"].astype(bool) & (~prev_down)

    d["vwap_bull"] = d["Close"] > d["VWAP"]
    d["vwap_bear"] = d["Close"] < d["VWAP"]

    # Chop filter: "atr_present" = volatility is high enough to trade (not consolidating).
    # When False, we treat the regime as flat/choppy and block entries (see long_entry/short_entry).
    d["atr_present"] = (d["ATR"] >= (d["ATR_SMA"] * float(p.atr_presence_ratio))) & (d["ATR_PCT"] >= float(p.atr_min_pct))

    # DXY (dollar) filter: inverse relationship with gold. Dollar above EMA12 -> bearish for gold.
    if p.use_dxy_filter and dxy_df is not None and not dxy_df.empty:
        d = _merge_dxy_into_gold(d, dxy_df, p)
    else:
        d["dxy_above_ema12"] = False  # No filter when DXY not available

    # 10Y yield (context-only): above/below EMA for checklist.
    if p.use_tenyr and tenyr_df is not None and not tenyr_df.empty:
        d = _merge_tenyr_into_gold(d, tenyr_df, p)
    else:
        d["tenyr_above_ema"] = False

    # Session levels (UTC): NY open 13:00; London 08:00–16:00. True/false for gold.
    d = compute_session_levels(d)

    return d


def generate_signals(d: pd.DataFrame) -> pd.DataFrame:
    """
    Entries:
      - Long: EMA20 crosses above EMA50 AND Close > VWAP AND ATR present AND DXY not above EMA12 (dollar weak)
      - Short: EMA20 crosses below EMA50 AND Close < VWAP AND ATR present AND DXY above EMA12 (dollar strong)

    Exits:
      - Long exit: EMA20 crosses below EMA50 OR Close < VWAP
      - Short exit: EMA20 crosses above EMA50 OR Close > VWAP
    """
    out = d.copy()
    dxy_ok = "dxy_above_ema12" in out.columns
    # When DXY filter off (dxy_ok False): don't block longs, don't require dollar-strong for shorts.
    dxy_block_long = out["dxy_above_ema12"].fillna(False) if dxy_ok else False
    dxy_allow_short = out["dxy_above_ema12"].fillna(False) if dxy_ok else True
    out["long_entry"] = out["cross_up"] & out["vwap_bull"] & out["atr_present"] & (~dxy_block_long)
    out["short_entry"] = out["cross_down"] & out["vwap_bear"] & out["atr_present"] & dxy_allow_short
    out["long_exit"] = out["cross_down"] | (~out["vwap_bull"])
    out["short_exit"] = out["cross_up"] | (~out["vwap_bear"])
    return out


def _calculate_trade_pnl(entry: float, exit: float, position: int, commission_entry: float, commission_exit: float) -> tuple[float, float]:
    """
    Calculate PnL for a trade including transaction costs.
    
    Args:
        entry: Entry price
        exit: Exit price
        position: 1 for long, -1 for short
        commission_entry: Commission to enter ($)
        commission_exit: Commission to exit ($)
    
    Returns:
        (gross_pnl, net_pnl) - Gross PnL before costs, Net PnL after costs
    """
    if position == 1:  # Long
        gross_pnl = exit - entry
    else:  # Short
        gross_pnl = entry - exit
    
    commission_total = commission_entry + commission_exit
    net_pnl = gross_pnl - commission_total
    
    return gross_pnl, net_pnl


def backtest(df: pd.DataFrame, p: StrategyParams, dxy_df: Optional[pd.DataFrame] = None) -> dict:
    """
    Simple 1-position backtest (either flat/long/short).
    Uses ATR-based stop and take profit, plus trailing stop.
    Includes transaction costs (commission_entry + commission_exit per round trip).
    """
    d = generate_signals(build_indicators(df, p, dxy_df=dxy_df)).reset_index(drop=True)
    if d.empty:
        return {"trades": 0, "total_pnl": 0.0, "win_rate": None, "total_commission": 0.0, "net_pnl": 0.0}

    pos = 0  # 0 flat, 1 long, -1 short
    entry = None
    entry_bar = None  # Bar index at entry (for min_hold_bars)
    stop = None
    take = None
    peak_price = None  # Highest price for long positions (for trailing stop)
    trough_price = None  # Lowest price for short positions (for trailing stop)
    trailing_stop_price = None  # Current trailing stop level
    vwap_exit_count = 0  # Consecutive bars below/above VWAP (for exit confirmation)
    wins = 0
    total = 0
    gross_pnl = 0.0  # PnL before costs
    total_commission = 0.0  # Track total commission costs

    for i in range(1, len(d)):
        row = d.iloc[i]
        price = float(row["Close"])
        high = float(row["High"]) if "High" in row else price
        low = float(row["Low"]) if "Low" in row else price
        atr = float(row["ATR"]) if not np.isnan(row["ATR"]) else 0.0

        # Manage open position: trailing stop first, then fixed stop/take
        if pos != 0 and entry is not None:
            bars_held = (i - entry_bar) if entry_bar is not None else 0
            
            if pos == 1:  # Long position
                # Update peak price (use High to catch intraday moves)
                if peak_price is None or high > peak_price:
                    peak_price = high
                    # Update trailing stop: ATR-based if specified, else percentage-based
                    if p.trailing_stop_atr_mult is not None and atr > 0:
                        trailing_stop_price = peak_price - (p.trailing_stop_atr_mult * atr)
                    else:
                        trailing_stop_price = peak_price * (1.0 - p.trailing_stop_pct)
                
                # Check trailing stop first (use Low to catch intraday stops)
                # Only exit if minimum hold period has passed
                if trailing_stop_price is not None and low <= trailing_stop_price and bars_held >= p.min_hold_bars:
                    exit_price = trailing_stop_price  # Exit at trailing stop level
                    gross_r, net_r = _calculate_trade_pnl(entry, exit_price, pos, p.commission_entry, p.commission_exit)
                    gross_pnl += gross_r
                    total_commission += (p.commission_entry + p.commission_exit)
                    total += 1
                    wins += 1 if net_r > 0 else 0
                    pos = 0
                    entry = entry_bar = stop = take = peak_price = trailing_stop_price = None
                    vwap_exit_count = 0
                    continue
                
                # Check fixed ATR stop (only if min hold period passed)
                if stop is not None and price <= stop and bars_held >= p.min_hold_bars:
                    gross_r, net_r = _calculate_trade_pnl(entry, price, pos, p.commission_entry, p.commission_exit)
                    gross_pnl += gross_r
                    total_commission += (p.commission_entry + p.commission_exit)
                    total += 1
                    wins += 1 if net_r > 0 else 0
                    pos = 0
                    entry = entry_bar = stop = take = peak_price = trailing_stop_price = None
                    vwap_exit_count = 0
                    continue
                # Check fixed ATR take profit (no min hold for take profit)
                if take is not None and price >= take:
                    gross_r, net_r = _calculate_trade_pnl(entry, price, pos, p.commission_entry, p.commission_exit)
                    gross_pnl += gross_r
                    total_commission += (p.commission_entry + p.commission_exit)
                    total += 1
                    wins += 1 if net_r > 0 else 0
                    pos = 0
                    entry = entry_bar = stop = take = peak_price = trailing_stop_price = None
                    vwap_exit_count = 0
                    continue
            else:  # Short position
                # Update trough price (use Low to catch intraday moves)
                if trough_price is None or low < trough_price:
                    trough_price = low
                    # Update trailing stop: ATR-based if specified, else percentage-based
                    if p.trailing_stop_atr_mult is not None and atr > 0:
                        trailing_stop_price = trough_price + (p.trailing_stop_atr_mult * atr)
                    else:
                        trailing_stop_price = trough_price * (1.0 + p.trailing_stop_pct)
                
                # Check trailing stop first (use High to catch intraday stops)
                # Only exit if minimum hold period has passed
                if trailing_stop_price is not None and high >= trailing_stop_price and bars_held >= p.min_hold_bars:
                    exit_price = trailing_stop_price  # Exit at trailing stop level
                    gross_r, net_r = _calculate_trade_pnl(entry, exit_price, pos, p.commission_entry, p.commission_exit)
                    gross_pnl += gross_r
                    total_commission += (p.commission_entry + p.commission_exit)
                    total += 1
                    wins += 1 if net_r > 0 else 0
                    pos = 0
                    entry = entry_bar = stop = take = trough_price = trailing_stop_price = None
                    vwap_exit_count = 0
                    continue
                
                # Check fixed ATR stop (only if min hold period passed)
                if stop is not None and price >= stop and bars_held >= p.min_hold_bars:
                    gross_r, net_r = _calculate_trade_pnl(entry, price, pos, p.commission_entry, p.commission_exit)
                    gross_pnl += gross_r
                    total_commission += (p.commission_entry + p.commission_exit)
                    total += 1
                    wins += 1 if net_r > 0 else 0
                    pos = 0
                    entry = entry_bar = stop = take = trough_price = trailing_stop_price = None
                    vwap_exit_count = 0
                    continue
                # Check fixed ATR take profit (no min hold for take profit)
                if take is not None and price <= take:
                    gross_r, net_r = _calculate_trade_pnl(entry, price, pos, p.commission_entry, p.commission_exit)
                    gross_pnl += gross_r
                    total_commission += (p.commission_entry + p.commission_exit)
                    total += 1
                    wins += 1 if net_r > 0 else 0
                    pos = 0
                    entry = entry_bar = stop = take = trough_price = trailing_stop_price = None
                    vwap_exit_count = 0
                    continue

        # Signal exits (with VWAP confirmation requirement and min hold period)
        # Calculate bars_held for position management
        bars_held = 0
        if pos != 0 and entry_bar is not None:
            bars_held = i - entry_bar
        
        if pos == 1:  # Long position
            # Check if EMA cross down (immediate exit, but respect min hold)
            if bool(row["cross_down"]) and bars_held >= p.min_hold_bars:
                gross_r, net_r = _calculate_trade_pnl(entry, price, pos, p.commission_entry, p.commission_exit)
                gross_pnl += gross_r
                total_commission += (p.commission_entry + p.commission_exit)
                total += 1
                wins += 1 if net_r > 0 else 0
                pos = 0
                entry = entry_bar = stop = take = peak_price = trailing_stop_price = None
                vwap_exit_count = 0
                continue
            # Check VWAP exit (requires N consecutive bars below VWAP and min hold period)
            if not bool(row["vwap_bull"]) and bars_held >= p.min_hold_bars:  # Price below VWAP
                vwap_exit_count += 1
                if vwap_exit_count >= p.vwap_exit_bars:
                    gross_r, net_r = _calculate_trade_pnl(entry, price, pos, p.commission_entry, p.commission_exit)
                    gross_pnl += gross_r
                    total_commission += (p.commission_entry + p.commission_exit)
                    total += 1
                    wins += 1 if net_r > 0 else 0
                    pos = 0
                    entry = entry_bar = stop = take = peak_price = trailing_stop_price = None
                    vwap_exit_count = 0
                    continue
            else:  # Price back above VWAP, reset counter
                vwap_exit_count = 0
        
        if pos == -1:  # Short position
            # Check if EMA cross up (immediate exit, but respect min hold)
            if bool(row["cross_up"]) and bars_held >= p.min_hold_bars:
                gross_r, net_r = _calculate_trade_pnl(entry, price, pos, p.commission_entry, p.commission_exit)
                gross_pnl += gross_r
                total_commission += (p.commission_entry + p.commission_exit)
                total += 1
                wins += 1 if net_r > 0 else 0
                pos = 0
                entry = entry_bar = stop = take = trough_price = trailing_stop_price = None
                vwap_exit_count = 0
                continue
            # Check VWAP exit (requires N consecutive bars above VWAP and min hold period)
            # For shorts: exit when price goes above VWAP (vwap_bear becomes False)
            if not bool(row["vwap_bear"]) and bars_held >= p.min_hold_bars:  # Price above VWAP (exit condition for shorts)
                vwap_exit_count += 1
                if vwap_exit_count >= p.vwap_exit_bars:
                    gross_r, net_r = _calculate_trade_pnl(entry, price, pos, p.commission_entry, p.commission_exit)
                    gross_pnl += gross_r
                    total_commission += (p.commission_entry + p.commission_exit)
                    total += 1
                    wins += 1 if net_r > 0 else 0
                    pos = 0
                    entry = entry_bar = stop = take = trough_price = trailing_stop_price = None
                    vwap_exit_count = 0
                    continue
            else:  # Price back below VWAP, reset counter
                vwap_exit_count = 0

        # Entries (only if flat)
        if pos == 0:
            vwap_exit_count = 0  # Reset counter when flat
            if bool(row["long_entry"]):
                pos = 1
                entry = price
                entry_bar = i  # Track entry bar for min_hold_bars
                peak_price = high  # Initialize peak with entry bar's high
                # Initialize trailing stop: ATR-based if specified, else percentage-based
                if p.trailing_stop_atr_mult is not None and atr > 0:
                    trailing_stop_price = peak_price - (p.trailing_stop_atr_mult * atr)
                else:
                    trailing_stop_price = peak_price * (1.0 - p.trailing_stop_pct)
                stop = entry - (p.stop_atr_mult * atr)
                take = entry + (p.take_atr_mult * atr)
                vwap_exit_count = 0  # Reset on entry
            elif bool(row["short_entry"]):
                pos = -1
                entry = price
                entry_bar = i  # Track entry bar for min_hold_bars
                trough_price = low  # Initialize trough with entry bar's low
                # Initialize trailing stop: ATR-based if specified, else percentage-based
                if p.trailing_stop_atr_mult is not None and atr > 0:
                    trailing_stop_price = trough_price + (p.trailing_stop_atr_mult * atr)
                else:
                    trailing_stop_price = trough_price * (1.0 + p.trailing_stop_pct)
                stop = entry + (p.stop_atr_mult * atr)
                take = entry - (p.take_atr_mult * atr)
                vwap_exit_count = 0  # Reset on entry

    win_rate = (wins / total) if total > 0 else None
    net_pnl = gross_pnl - total_commission
    return {
        "trades": int(total),
        "total_pnl": float(gross_pnl),  # Gross PnL before costs
        "total_commission": float(total_commission),
        "net_pnl": float(net_pnl),  # Net PnL after costs (this is what matters)
        "win_rate": win_rate,
    }


def latest_signal_summary(
    df: pd.DataFrame,
    p: StrategyParams,
    dxy_df: Optional[pd.DataFrame] = None,
    tenyr_df: Optional[pd.DataFrame] = None,
) -> str:
    d = generate_signals(build_indicators(df, p, dxy_df=dxy_df, tenyr_df=tenyr_df))
    if d.empty:
        return "No data."
    last = d.iloc[-1]
    dt = pd.to_datetime(last["Datetime"], utc=True) if "Datetime" in d.columns else None
    ts = dt.isoformat() if dt is not None and not pd.isna(dt) else "N/A"
    sym_used = df.attrs.get("symbol_used") if hasattr(df, "attrs") else None
    src = df.attrs.get("source") if hasattr(df, "attrs") else None
    sym_txt = f"{sym_used} | " if sym_used else ""
    src_txt = f"{src} | " if src else ""
    dxy_txt = ""
    dxy_sym = dxy_df.attrs.get("symbol_used", "DXY") if (dxy_df is not None and hasattr(dxy_df, "attrs")) else "DXY"
    if "DXY_Close" in last and pd.notna(last.get("DXY_Close")):
        dxy_txt = f" | {dxy_sym}={float(last['DXY_Close']):.2f} above_EMA12={bool(last.get('dxy_above_ema12', False))}"
    session_txt = f" | above_ny_open={bool(last.get('above_ny_open', False))} above_london_high={bool(last.get('above_london_high', False))} below_london_low={bool(last.get('below_london_low', False))}"
    return (
        sym_txt
        + src_txt
        + f"{ts} | Close={float(last['Close']):.4f} | EMA20={float(last['EMA_FAST']):.4f} EMA50={float(last['EMA_SLOW']):.4f} "
        + f"| VWAP={float(last['VWAP']):.4f} | ATR={float(last['ATR']):.4f} ({float(last['ATR_PCT'])*100:.2f}%) "
        + f"| consolidating={not bool(last['atr_present'])}{dxy_txt}{session_txt} | long_entry={bool(last['long_entry'])} short_entry={bool(last['short_entry'])}"
    )


def _status_payload(
    df: pd.DataFrame,
    p: StrategyParams,
    dxy_df: Optional[pd.DataFrame] = None,
    tenyr_df: Optional[pd.DataFrame] = None,
    other_metal_df: Optional[pd.DataFrame] = None,
) -> dict:
    d = generate_signals(build_indicators(df, p, dxy_df=dxy_df, tenyr_df=tenyr_df))
    if d.empty:
        return {"ok": False}
    last = d.iloc[-1]
    ts = "N/A"
    try:
        ts = pd.to_datetime(last["Datetime"], utc=True).isoformat()
    except Exception:
        pass

    trend = "BULL" if bool(last["trend_up"]) else ("BEAR" if bool(last["trend_down"]) else "FLAT")
    vwap_side = "ABOVE_VWAP" if bool(last["vwap_bull"]) else ("BELOW_VWAP" if bool(last["vwap_bear"]) else "AT_VWAP")
    # consolidating = True means low volatility / choppy regime (no entries); False = volatility present, entries allowed.
    consolidating = not bool(last["atr_present"])

    cross = None
    if bool(last.get("cross_up", False)):
        cross = "CROSS_UP"
    elif bool(last.get("cross_down", False)):
        cross = "CROSS_DOWN"

    entry = None
    if bool(last.get("long_entry", False)):
        entry = "LONG_ENTRY"
    elif bool(last.get("short_entry", False)):
        entry = "SHORT_ENTRY"

    sym_used = df.attrs.get("symbol_used") if hasattr(df, "attrs") else None
    src = df.attrs.get("source") if hasattr(df, "attrs") else None

    dxy_above = bool(last.get("dxy_above_ema12", False))
    dxy_close = float(last["DXY_Close"]) if "DXY_Close" in last and pd.notna(last.get("DXY_Close")) else None
    dxy_ema12 = float(last["DXY_EMA12"]) if "DXY_EMA12" in last and pd.notna(last.get("DXY_EMA12")) else None
    dxy_symbol_used = dxy_df.attrs.get("symbol_used") if (dxy_df is not None and hasattr(dxy_df, "attrs")) else None

    tenyr_above = bool(last.get("tenyr_above_ema", False))
    tenyr_close = float(last["TENYR_Close"]) if "TENYR_Close" in last and pd.notna(last.get("TENYR_Close")) else None
    tenyr_ema = float(last["TENYR_EMA"]) if "TENYR_EMA" in last and pd.notna(last.get("TENYR_EMA")) else None

    above_ny_open = bool(last.get("above_ny_open", False))
    above_london_high = bool(last.get("above_london_high", False))
    below_london_low = bool(last.get("below_london_low", False))
    long_entry = bool(last.get("long_entry", False))
    short_entry = bool(last.get("short_entry", False))
    trend_up = bool(last.get("trend_up", False))
    trend_down = bool(last.get("trend_down", False))
    vwap_bull = bool(last.get("vwap_bull", False))
    vwap_bear = bool(last.get("vwap_bear", False))
    atr_present = bool(last.get("atr_present", False))

    # Cross-confirm: Gold & Silver should agree on direction. Divergence (one bull, one bear) = alarming.
    cross_confirm_aligned: Optional[bool] = None
    if other_metal_df is not None and not other_metal_df.empty:
        try:
            other_d = build_indicators(other_metal_df, p, dxy_df=None, tenyr_df=None)
            if not other_d.empty:
                other_last = other_d.iloc[-1]
                ou = bool(other_last.get("trend_up", False))
                od = bool(other_last.get("trend_down", False))
                # Aligned = both bullish OR both bearish. Divergence = one bull, one bear.
                cross_confirm_aligned = (trend_up and ou) or (trend_down and od)
        except Exception:
            pass

    return {
        "ok": True,
        "timestamp": ts,
        "symbol_used": sym_used,
        "source": src,
        "close": float(last["Close"]),
        "ema_fast": float(last["EMA_FAST"]),
        "ema_slow": float(last["EMA_SLOW"]),
        "vwap": float(last["VWAP"]),
        "atr": float(last["ATR"]),
        "atr_pct": float(last["ATR_PCT"]),
        "trend": trend,
        "vwap_side": vwap_side,
        "consolidating": consolidating,
        "dxy_above_ema12": dxy_above,
        "dxy_close": dxy_close,
        "dxy_ema12": dxy_ema12,
        "tenyr_above_ema": tenyr_above,
        "tenyr_close": tenyr_close,
        "tenyr_ema": tenyr_ema,
        "cross": cross,
        "entry": entry,
        "above_ny_open": above_ny_open,
        "above_london_high": above_london_high,
        "below_london_low": below_london_low,
        "long_entry": long_entry,
        "short_entry": short_entry,
        "trend_up": trend_up,
        "trend_down": trend_down,
        "vwap_bull": vwap_bull,
        "vwap_bear": vwap_bear,
        "atr_present": atr_present,
        "cross_confirm_aligned": cross_confirm_aligned,
    }


def _checklist_cell(val: bool, bias: Optional[str]) -> str:
    """Format checklist cell: always show True/False and (Bull) or (Bear) so bias is clear either way."""
    if isinstance(val, str) or val is None:
        return str(val) if val is not None else "N/A"
    if bias:
        if val:
            return f"True ({bias})"
        return f"False ({'Bear' if bias == 'Bull' else 'Bull'})"
    return "True" if val else "False"


def print_status_checklist(s: dict, title: str = "GOLD") -> None:
    """
    Print a True/False checklist for quick daily status overview.
    Appends Bull/Bear when True so inexperienced traders can see the bias.
    Uses tabulate for | INDICATOR | TRUE/FALSE (Bull/Bear) | layout if available.
    Safe to call with s['ok'] False (prints minimal message).
    """
    if not s.get("ok"):
        print(f"{title} status: no data (ok=False)", flush=True)
        return
    sym = s.get("symbol_used") or ("SI=F" if "SILVER" in title else "GC=F")
    ts = s.get("timestamp") or "N/A"
    cc = s.get("cross_confirm_aligned")
    cross_row = ("Cross-confirm (Gold↔Silver aligned)", _checklist_cell(cc, None) if cc is not None else "N/A")
    rows = [
        ("Trend BULL", _checklist_cell(s.get("trend_up", False), "Bull")),
        ("Trend BEAR", _checklist_cell(s.get("trend_down", False), "Bear")),
        ("Above VWAP", _checklist_cell(s.get("vwap_bull", False), "Bull")),
        ("Below VWAP", _checklist_cell(s.get("vwap_bear", False), "Bear")),
        ("Volatility OK (not consolidating)", _checklist_cell(s.get("atr_present", False), None)),
        ("Consolidating (chop, no entries)", _checklist_cell(s.get("consolidating", False), None)),
        (f"Dollar ({s.get('dxy_symbol_used') or 'DXY'}) above EMA12 (dollar strong)", _checklist_cell(s.get("dxy_above_ema12", False), "Bear")),
        ("10Y above EMA (yields up)", _checklist_cell(s.get("tenyr_above_ema", False), "Bear")),
        cross_row,
        ("Above NY open (CAREFUL on weekends)", _checklist_cell(s.get("above_ny_open", False), "Bull")),
        ("Above London high (CAREFUL on weekends)", _checklist_cell(s.get("above_london_high", False), "Bull")),
        ("Below London low (CAREFUL on weekends)", _checklist_cell(s.get("below_london_low", False), "Bear")),
        ("Long entry signal", _checklist_cell(s.get("long_entry", False), "Bull")),
        ("Short entry signal", _checklist_cell(s.get("short_entry", False), "Bear")),
    ]
    print("", flush=True)
    print(f"  {title} STATUS CHECKLIST", flush=True)
    print(f"  {sym}  |  {ts}", flush=True)
    print("", flush=True)
    if tabulate is not None:
        print(tabulate(rows, headers=["INDICATOR", "TRUE/FALSE (Bull/Bear)"], tablefmt="grid"), flush=True)
    else:
        for label, val in rows:
            print(f"  {label:40} {val}", flush=True)
    print("", flush=True)
    print(
        f"  Close={s.get('close'):.4f}  VWAP={s.get('vwap'):.4f}  "
        f"ATR={s.get('atr'):.4f} ({s.get('atr_pct', 0)*100:.2f}%)",
        flush=True,
    )
    print("", flush=True)


def _format_status_line(s: dict) -> str:
    sym = s.get("symbol_used") or "N/A"
    src = s.get("source") or "N/A"
    dxy_str = ""
    if s.get("dxy_close") is not None:
        dxy_str = f" | DXY={s['dxy_close']:.2f} above_EMA12={s.get('dxy_above_ema12')}"
    session_str = f" | above_ny_open={s.get('above_ny_open')} | above_london_high={s.get('above_london_high')} below_london_low={s.get('below_london_low')}"
    return (
        f"[status] {sym} ({src}) | {s.get('timestamp')} | "
        f"{s.get('trend')} | {s.get('vwap_side')} | consolidating={s.get('consolidating')}{dxy_str}{session_str} | "
        f"Close={s.get('close'):.4f} VWAP={s.get('vwap'):.4f} "
        f"EMA20={s.get('ema_fast'):.4f} EMA50={s.get('ema_slow'):.4f} "
        f"ATR={s.get('atr'):.4f} ({s.get('atr_pct')*100:.2f}%)"
    )


def _format_flip_line(s: dict, prev: Optional[dict]) -> Optional[str]:
    """
    Emit a human-friendly line when the "state" changes (trend flip) or when a cross/entry fires.
    """
    if not s.get("ok"):
        return None

    parts = []
    # Trend flip detection (BULL<->BEAR)
    if prev and prev.get("ok") and prev.get("trend") != s.get("trend"):
        parts.append(f"TREND_FLIP {prev.get('trend')}→{s.get('trend')}")

    # Any cross event is noteworthy even if trend label already matches.
    if s.get("cross"):
        parts.append(s["cross"])

    # Entry event is the strongest "alert" signal
    if s.get("entry"):
        parts.append(s["entry"])

    # Also warn when consolidating toggles (chop → tradable or vice versa)
    if prev and prev.get("ok") and prev.get("consolidating") != s.get("consolidating"):
        parts.append(f"CONSOLIDATING {prev.get('consolidating')}→{s.get('consolidating')}")

    if not parts:
        return None

    sym = s.get("symbol_used") or "N/A"
    return f"[ALERT] {sym} | {s.get('timestamp')} | " + " | ".join(parts) + f" | {s.get('vwap_side')}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Gold futures 1H EMA/VWAP/ATR strategy")
    parser.add_argument("--symbol", type=str, default="GC=F", help="Yahoo symbol (default: GC=F)")
    parser.add_argument("--interval", type=str, default="60m", help="yfinance interval (default: 60m)")
    parser.add_argument("--period", type=str, default="90d", help="yfinance period (default: 90d)")
    parser.add_argument("--max-cache-age-minutes", type=int, default=30, help="Cache TTL in minutes (default: 30)")
    parser.add_argument(
        "--fallback-symbols",
        type=str,
        default="GLD,IAU",
        help="Comma-separated fallback symbols if GC=F fails (default: GLD,IAU)",
    )

    parser.add_argument("--ema-fast", type=int, default=20)
    parser.add_argument("--ema-slow", type=int, default=50)
    parser.add_argument("--atr-period", type=int, default=14)
    parser.add_argument("--atr-sma-period", type=int, default=50)
    parser.add_argument("--atr-presence-ratio", type=float, default=0.90)
    parser.add_argument("--atr-min-pct", type=float, default=0.0015)
    parser.add_argument("--stop-atr-mult", type=float, default=2.0)
    parser.add_argument("--take-atr-mult", type=float, default=3.0)
    parser.add_argument("--trailing-stop-pct", type=float, default=0.01, help="Trailing stop percentage (default: 0.01 = 1%%, used if --trailing-stop-atr-mult not set)")
    parser.add_argument("--trailing-stop-atr-mult", type=float, default=None, help="ATR-based trailing stop multiplier (None = use percentage-based, e.g., 1.5 = trail by 1.5x ATR)")
    parser.add_argument("--min-hold-bars", type=int, default=3, help="Minimum bars to hold position before allowing exit (prevents premature exits, default: 3)")
    parser.add_argument("--commission-entry", type=float, default=3.0, help="Commission cost to enter contract ($, default: 3.0)")
    parser.add_argument("--commission-exit", type=float, default=3.0, help="Commission cost to exit contract ($, default: 3.0)")
    parser.add_argument("--vwap-exit-bars", type=int, default=1, help="Require N consecutive bars below/above VWAP before exiting (default: 1 = immediate)")
    parser.add_argument("--dxy-symbol", type=str, default="^DX", help="Yahoo symbol for US Dollar Index (default: ^DX)")
    parser.add_argument("--dxy-ema-period", type=int, default=12, help="DXY 60m EMA period for dollar filter (default: 12)")
    parser.add_argument("--no-dxy-filter", action="store_true", help="Disable DXY (dollar) filter; trade gold without dollar confirmation")
    parser.add_argument("--tenyr-symbol", type=str, default="^TNX", help="Yahoo symbol for 10Y Treasury Yield (default: ^TNX)")
    parser.add_argument("--tenyr-ema-period", type=int, default=12, help="10Y 60m EMA period (default: 12)")
    parser.add_argument("--no-tenyr", action="store_true", help="Disable 10Y yield fetch/merge for checklist")
    parser.add_argument("--no-cross-confirm", action="store_true", help="Disable Gold↔Silver cross-confirmation (skip fetching other metal)")

    parser.add_argument("--backtest", action="store_true", help="Run backtest summary and exit")
    parser.add_argument("--loop", action="store_true", help="Loop and print latest signal")
    parser.add_argument("--sleep-seconds", type=int, default=900, help="Loop sleep seconds (default: 900)")
    parser.add_argument("--beep", action="store_true", help="Terminal beep on alerts (ASCII bell)")
    parser.add_argument("--print-status-every", type=int, default=1, help="Print status every N loop iterations (default: 1)")

    args = parser.parse_args()

    p = StrategyParams(
        ema_fast=int(args.ema_fast),
        ema_slow=int(args.ema_slow),
        atr_period=int(args.atr_period),
        atr_presence_ratio=float(args.atr_presence_ratio),
        atr_sma_period=int(args.atr_sma_period),
        atr_min_pct=float(args.atr_min_pct),
        stop_atr_mult=float(args.stop_atr_mult),
        take_atr_mult=float(args.take_atr_mult),
        trailing_stop_pct=float(args.trailing_stop_pct),
        trailing_stop_atr_mult=float(args.trailing_stop_atr_mult) if args.trailing_stop_atr_mult is not None else None,
        min_hold_bars=int(args.min_hold_bars),
        vwap_exit_bars=int(args.vwap_exit_bars),
        commission_entry=float(args.commission_entry),
        commission_exit=float(args.commission_exit),
        dxy_symbol=str(args.dxy_symbol),
        dxy_ema_period=int(args.dxy_ema_period),
        use_dxy_filter=not args.no_dxy_filter,
        tenyr_symbol=str(args.tenyr_symbol),
        tenyr_ema_period=int(args.tenyr_ema_period),
        use_tenyr=not args.no_tenyr,
    )

    if args.loop:
        print(f"🔁 Looping {args.symbol} ({args.interval}, {args.period}) | {datetime.utcnow().isoformat()}Z", flush=True)
        prev_status: Optional[dict] = None
        iter_n = 0
        while True:
            iter_n += 1
            fallback_syms = [s.strip() for s in str(args.fallback_symbols).split(",") if s.strip()]
            df = fetch_ohlcv(
                args.symbol,
                args.interval,
                args.period,
                max_cache_age_minutes=args.max_cache_age_minutes,
                fallback_symbols=fallback_syms,
            )
            dxy_df = _fetch_dxy(args.interval, args.period, args.max_cache_age_minutes, p.dxy_symbol) if p.use_dxy_filter else None
            tenyr_df = _fetch_tenyr(args.interval, args.period, args.max_cache_age_minutes, p.tenyr_symbol) if p.use_tenyr else None
            s = _status_payload(df, p, dxy_df=dxy_df, tenyr_df=tenyr_df)
            alert_line = _format_flip_line(s, prev_status)
            if alert_line:
                if args.beep:
                    print("\a", end="")  # ASCII bell
                print(alert_line, flush=True)

            if args.print_status_every > 0 and (iter_n % int(args.print_status_every) == 0):
                print(_format_status_line(s), flush=True)

            prev_status = s
            time.sleep(max(5, int(args.sleep_seconds)))
        return

    fallback_syms = [s.strip() for s in str(args.fallback_symbols).split(",") if s.strip()]
    df = fetch_ohlcv(
        args.symbol,
        args.interval,
        args.period,
        max_cache_age_minutes=args.max_cache_age_minutes,
        fallback_symbols=fallback_syms,
    )
    dxy_df = _fetch_dxy(args.interval, args.period, args.max_cache_age_minutes, p.dxy_symbol) if p.use_dxy_filter else None
    if dxy_df is not None and getattr(dxy_df, "attrs", {}).get("symbol_used") != p.dxy_symbol:
        print(f"Using {dxy_df.attrs.get('symbol_used')} for dollar ({p.dxy_symbol} unavailable).", flush=True)
    tenyr_df = _fetch_tenyr(args.interval, args.period, args.max_cache_age_minutes, p.tenyr_symbol) if p.use_tenyr else None
    silver_df = None
    if not args.no_cross_confirm:
        silver_df = fetch_ohlcv("SI=F", args.interval, args.period, max_cache_age_minutes=args.max_cache_age_minutes, fallback_symbols=["SLV", "SIL"])

    if args.backtest:
        res = backtest(df, p, dxy_df=dxy_df)
        print(
            f"Backtest {args.symbol} {args.interval} {args.period} | trades={res['trades']} "
            f"| total_pnl(pts)={res['total_pnl']:.4f} | win_rate={(res['win_rate'] or 0):.1%}",
            flush=True,
        )
        return

    # Default: print True/False checklist for quick daily gold overview
    s = _status_payload(df, p, dxy_df=dxy_df, tenyr_df=tenyr_df, other_metal_df=silver_df)
    print_status_checklist(s, title="GOLD")


if __name__ == "__main__":
    main()
