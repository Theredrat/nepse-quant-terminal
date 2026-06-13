"""
NEPSE Pre-Move Pattern Recognition Backtest
============================================
Scans 5 years of OHLCV data to find all significant upward moves,
then profiles what price + volume looked like in the windows BEFORE each move.

Usage:
    python nepse_pattern_backtest.py
    python nepse_pattern_backtest.py --db path/to/nepse_market_data.db
    python nepse_pattern_backtest.py --move-pct 12 --move-days 15 --pre-window 20
"""

import sqlite3
import argparse
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats

# ─── CONFIG DEFAULTS ────────────────────────────────────────────────────────
DEFAULT_DB      = "nepse_market_data.db"
MOVE_PCT        = 10          # % gain that defines a "significant move"
MOVE_DAYS       = 10          # within how many trading days
PRE_WINDOWS     = [5, 10, 20] # days before move to analyze
MIN_DATA_DAYS   = 60          # minimum history a stock needs
RSI_PERIOD      = 14
VOL_MA_PERIOD   = 20
SUPPORT_LOOKBACK= 20          # days to find support level
# ────────────────────────────────────────────────────────────────────────────

def connect_db(path):
    if not os.path.exists(path):
        print(f"[ERROR] Database not found: {path}")
        sys.exit(1)
    return sqlite3.connect(path)

def load_all_prices(conn):
    """Load full OHLCV history for all stocks."""
    query = """
        SELECT symbol, date, open, high, low, close, volume
        FROM stock_prices
        ORDER BY symbol, date
    """
    try:
        df = pd.read_sql_query(query, conn, parse_dates=["date"])
    except Exception:
        # Try alternate table names
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        print(f"[INFO] Tables in DB: {tables['name'].tolist()}")
        # Try common alternatives
        for tbl in ["daily_price", "prices", "ohlcv", "stock_ohlcv", "market_data"]:
            try:
                df = pd.read_sql_query(
                    f"SELECT * FROM {tbl} ORDER BY symbol, date",
                    conn, parse_dates=["date"]
                )
                print(f"[INFO] Loaded from table: {tbl}")
                break
            except Exception:
                continue
        else:
            print("[ERROR] Could not find price table. Please check your DB schema.")
            sys.exit(1)

    # Normalize column names to lowercase
    df.columns = [c.lower() for c in df.columns]
    required = {"symbol", "date", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        print(f"[ERROR] Missing columns: {missing}. Available: {df.columns.tolist()}")
        sys.exit(1)

    # Fill missing OHLC from close if needed
    for col in ["open", "high", "low"]:
        if col not in df.columns:
            df[col] = df["close"]

    # Coerce numeric columns
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["close", "volume"])
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    print(f"[INFO] Loaded {len(df):,} rows | {df['symbol'].nunique()} symbols | "
          f"{df['date'].min().date()} → {df['date'].max().date()}")
    return df

# ─── INDICATORS ─────────────────────────────────────────────────────────────

def compute_rsi(close, period=RSI_PERIOD):
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def compute_atr(high, low, close, period=14):
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def compute_indicators(df):
    """Add RSI, volume ratio, ATR, price range metrics per symbol."""
    frames = []
    for sym, grp in df.groupby("symbol"):
        grp = grp.copy().reset_index(drop=True)
        grp["rsi"]        = compute_rsi(grp["close"])
        grp["vol_ma"]     = grp["volume"].rolling(VOL_MA_PERIOD).mean()
        grp["vol_ratio"]  = grp["volume"] / grp["vol_ma"].replace(0, np.nan)
        grp["atr"]        = compute_atr(grp["high"], grp["low"], grp["close"])
        grp["ma20"]       = grp["close"].rolling(20).mean()
        grp["ma50"]       = grp["close"].rolling(50).mean()
        grp["ma200"]      = grp["close"].rolling(200).mean()
        grp["ret_1d"]     = grp["close"].pct_change()
        grp["ret_5d"]     = grp["close"].pct_change(5)
        # Price range compression: std of close over 10 days / close
        grp["range_comp"] = grp["close"].rolling(10).std() / grp["close"]
        # Support: rolling min of low over lookback
        grp["support"]    = grp["low"].rolling(SUPPORT_LOOKBACK).min()
        grp["dist_support"]= (grp["close"] - grp["support"]) / grp["support"]
        frames.append(grp)
    return pd.concat(frames, ignore_index=True)

# ─── MOVE DETECTION ─────────────────────────────────────────────────────────

def find_moves(df, move_pct=MOVE_PCT, move_days=MOVE_DAYS):
    """
    For each bar, check if price gains >= move_pct% within move_days.
    Returns a list of (symbol, start_date, end_date, actual_gain_pct, start_idx).
    """
    moves = []
    threshold = move_pct / 100.0

    for sym, grp in df.groupby("symbol"):
        if len(grp) < MIN_DATA_DAYS:
            continue
        closes = grp["close"].values
        dates  = grp["date"].values
        idxmap = grp.index.values  # original df indices

        for i in range(len(closes) - move_days):
            base  = closes[i]
            if base <= 0:
                continue
            future = closes[i+1 : i+move_days+1]
            best   = (future.max() - base) / base
            if best >= threshold:
                # Find actual day of peak
                peak_offset = np.argmax(future) + 1
                moves.append({
                    "symbol"    : sym,
                    "start_date": dates[i],
                    "end_date"  : dates[i + peak_offset],
                    "gain_pct"  : round(best * 100, 2),
                    "start_idx" : idxmap[i],
                    "grp_pos"   : i,          # position within group
                })

    print(f"[INFO] Found {len(moves):,} qualifying moves (≥{move_pct}% in ≤{move_days} days)")
    return moves

# ─── PRE-MOVE PROFILING ──────────────────────────────────────────────────────

def extract_pre_move_window(grp, pos, window):
    """Extract the `window` bars ending at pos (exclusive) — the pre-move slice."""
    start = max(0, pos - window)
    return grp.iloc[start:pos]

def profile_window(w):
    """Compute pattern metrics for a pre-move window DataFrame."""
    if len(w) < 3:
        return None

    c   = w["close"].values
    v   = w["volume"].values
    vr  = w["vol_ratio"].values
    rsi = w["rsi"].values
    rc  = w["range_comp"].values
    ds  = w["dist_support"].values

    # Volume buildup: is volume trending up?
    vol_slope, _, _, _, _ = stats.linregress(range(len(v)), v)
    vol_buildup = float(vol_slope > 0)
    with np.errstate(all="ignore"):
        avg_vol_ratio = float(np.nanmean(vr))
        vol_surge_last3 = float(np.nanmean(vr[-3:]) > 1.5) if len(vr) >= 3 else 0.0

    # Price consolidation: tight range
    price_range_pct = float((c.max() - c.min()) / c.min() * 100) if c.min() > 0 else 0.0
    is_consolidating = float(price_range_pct < 8.0)   # within 8% band

    # Range compression: std shrinking
    with np.errstate(all="ignore"):
        avg_range_comp = float(np.nanmean(rc))

    # RSI behavior
    rsi_valid   = rsi[~np.isnan(rsi)]
    avg_rsi     = float(np.nanmean(rsi_valid)) if len(rsi_valid) else np.nan
    rsi_oversold= float(avg_rsi < 40) if not np.isnan(avg_rsi) else 0.0
    rsi_rising  = 0.0
    if len(rsi_valid) >= 3:
        slope, _, _, _, _ = stats.linregress(range(len(rsi_valid)), rsi_valid)
        rsi_rising = float(slope > 0)

    # Support test: how close to support before the move?
    ds_valid = ds[~np.isnan(ds)]
    avg_dist_support = float(np.nanmean(ds_valid)) if len(ds_valid) else np.nan
    near_support = float(avg_dist_support < 0.05) if not np.isnan(avg_dist_support) else 0.0

    # Price trend: is price flat/down going into the move (basing)?
    price_slope, _, _, _, _ = stats.linregress(range(len(c)), c)
    price_basing = float(abs(price_slope / c.mean()) < 0.005) if c.mean() > 0 else 0.0

    return {
        "vol_buildup"       : vol_buildup,
        "avg_vol_ratio"     : avg_vol_ratio,
        "vol_surge_last3"   : vol_surge_last3,
        "price_range_pct"   : price_range_pct,
        "is_consolidating"  : is_consolidating,
        "avg_range_comp"    : avg_range_comp,
        "avg_rsi"           : avg_rsi,
        "rsi_oversold"      : rsi_oversold,
        "rsi_rising"        : rsi_rising,
        "avg_dist_support"  : avg_dist_support,
        "near_support"      : near_support,
        "price_basing"      : price_basing,
    }

def profile_all_moves(df, moves):
    """For each move, extract pre-move windows and compute pattern profiles."""
    # Build a fast lookup: symbol → grp DataFrame
    sym_grps = {sym: grp.reset_index(drop=True) for sym, grp in df.groupby("symbol")}

    results = defaultdict(list)  # window_size → list of profile dicts

    for m in moves:
        sym = m["symbol"]
        pos = m["grp_pos"]
        grp = sym_grps.get(sym)
        if grp is None or pos < 5:
            continue

        for w in PRE_WINDOWS:
            window_df = extract_pre_move_window(grp, pos, w)
            prof = profile_window(window_df)
            if prof:
                prof["symbol"]    = sym
                prof["start_date"]= m["start_date"]
                prof["gain_pct"]  = m["gain_pct"]
                prof["window"]    = w
                results[w].append(prof)

    return results

# ─── BASELINE (non-move days) ─────────────────────────────────────────────

def build_baseline(df, moves, n_samples=3000):
    """Sample random non-move windows as a control group."""
    move_set = set()
    for m in moves:
        move_set.add((m["symbol"], str(m["start_date"])[:10]))

    sym_grps = {sym: grp.reset_index(drop=True) for sym, grp in df.groupby("symbol")}
    baseline = defaultdict(list)
    rng = np.random.default_rng(42)

    symbols = list(sym_grps.keys())
    attempts = 0
    while sum(len(v) for v in baseline.values()) < n_samples * len(PRE_WINDOWS) and attempts < 50000:
        attempts += 1
        sym = rng.choice(symbols)
        grp = sym_grps[sym]
        if len(grp) < 30:
            continue
        pos = int(rng.integers(20, len(grp)))
        date_str = str(grp.iloc[pos]["date"])[:10]
        if (sym, date_str) in move_set:
            continue
        for w in PRE_WINDOWS:
            window_df = extract_pre_move_window(grp, pos, w)
            prof = profile_window(window_df)
            if prof:
                prof["symbol"] = sym
                prof["window"] = w
                baseline[w].append(prof)

    print(f"[INFO] Baseline samples: { {k: len(v) for k, v in baseline.items()} }")
    return baseline

# ─── REPORT ──────────────────────────────────────────────────────────────────

PATTERN_COLS = [
    "vol_buildup", "avg_vol_ratio", "vol_surge_last3",
    "price_range_pct", "is_consolidating", "avg_range_comp",
    "avg_rsi", "rsi_oversold", "rsi_rising",
    "avg_dist_support", "near_support", "price_basing",
]

PATTERN_LABELS = {
    "vol_buildup"       : "Volume trending up before move",
    "avg_vol_ratio"     : "Avg volume vs 20d MA",
    "vol_surge_last3"   : "Vol surge in last 3 days (>1.5x)",
    "price_range_pct"   : "Price range % in window",
    "is_consolidating"  : "Price consolidating (<8% band)",
    "avg_range_comp"    : "Avg daily range compression",
    "avg_rsi"           : "Avg RSI in window",
    "rsi_oversold"      : "RSI was oversold (<40)",
    "rsi_rising"        : "RSI trending up",
    "avg_dist_support"  : "Avg distance from support",
    "near_support"      : "Near support (<5%)",
    "price_basing"      : "Price basing (flat before move)",
}

def print_section(title):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_pattern_report(move_profiles, baseline_profiles, window):
    print_section(f"PRE-MOVE PATTERN ANALYSIS  |  Window: {window} days before move")

    move_df = pd.DataFrame(move_profiles)
    base_df = pd.DataFrame(baseline_profiles)

    print(f"\n  Qualifying moves analysed : {len(move_df):,}")
    print(f"  Baseline samples          : {len(base_df):,}")
    print()
    print(f"  {'Pattern':<42} {'Before Move':>12} {'Baseline':>12} {'Edge':>8}")
    print(f"  {'-'*42} {'-'*12} {'-'*12} {'-'*8}")

    edges = []
    for col in PATTERN_COLS:
        if col not in move_df.columns or col not in base_df.columns:
            continue
        m_val = move_df[col].dropna().mean()
        b_val = base_df[col].dropna().mean()
        if b_val != 0:
            edge = ((m_val - b_val) / abs(b_val)) * 100
        else:
            edge = 0.0
        label = PATTERN_LABELS.get(col, col)
        sign  = "+" if edge >= 0 else ""
        print(f"  {label:<42} {m_val:>12.3f} {b_val:>12.3f} {sign}{edge:>7.1f}%")
        edges.append((label, edge))

    # Top 5 strongest signals
    edges_sorted = sorted(edges, key=lambda x: abs(x[1]), reverse=True)
    print()
    print("  ── TOP SIGNALS (by edge vs baseline) ──────────────────────────")
    for label, edge in edges_sorted[:5]:
        sign = "▲" if edge > 0 else "▼"
        print(f"  {sign} {label:<42} edge: {edge:+.1f}%")

def print_move_distribution(moves):
    print_section("MOVE DISTRIBUTION SUMMARY")
    gains = [m["gain_pct"] for m in moves]
    df = pd.Series(gains)
    print(f"\n  Total qualifying moves  : {len(gains):,}")
    print(f"  Avg gain                : {df.mean():.1f}%")
    print(f"  Median gain             : {df.median():.1f}%")
    print(f"  Max gain                : {df.max():.1f}%")
    print(f"  Moves ≥ 20%             : {(df >= 20).sum():,}")
    print(f"  Moves ≥ 30%             : {(df >= 30).sum():,}")

    # Symbol frequency
    sym_counts = pd.Series([m["symbol"] for m in moves]).value_counts()
    print(f"\n  Top 10 most frequently moving stocks:")
    for sym, cnt in sym_counts.head(10).items():
        print(f"    {sym:<12} {cnt:>4} moves")

def print_seasonal_pattern(moves):
    print_section("SEASONAL / CALENDAR PATTERN")
    df = pd.DataFrame(moves)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["month"] = df["start_date"].dt.month
    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly = df.groupby("month")["gain_pct"].agg(["count","mean"])
    print(f"\n  {'Month':<8} {'# Moves':>8} {'Avg Gain%':>10}")
    print(f"  {'-'*8} {'-'*8} {'-'*10}")
    for m, row in monthly.iterrows():
        bar = "█" * int(row["count"] / max(monthly["count"]) * 20)
        print(f"  {month_names[m-1]:<8} {int(row['count']):>8} {row['mean']:>9.1f}%  {bar}")

def print_combined_signal_stats(move_profiles, window):
    """Show what % of moves had ALL key patterns aligned."""
    print_section(f"COMBINED SIGNAL ALIGNMENT  |  Window: {window} days")
    df = pd.DataFrame(move_profiles)
    if df.empty:
        return

    checks = {
        "Vol buildup + consolidation + RSI rising"    : lambda r: r["vol_buildup"] and r["is_consolidating"] and r["rsi_rising"],
        "Near support + vol buildup"                   : lambda r: r["near_support"] and r["vol_buildup"],
        "Oversold RSI + vol surge last 3d"             : lambda r: r["rsi_oversold"] and r["vol_surge_last3"],
        "All 4 signals aligned"                        : lambda r: r["vol_buildup"] and r["is_consolidating"] and r["rsi_rising"] and r["near_support"],
        "Basing + vol buildup + oversold"              : lambda r: r["price_basing"] and r["vol_buildup"] and r["rsi_oversold"],
    }

    print(f"\n  {'Signal Combo':<50} {'% of Moves':>10}")
    print(f"  {'-'*50} {'-'*10}")
    for label, fn in checks.items():
        try:
            pct = df.apply(fn, axis=1).mean() * 100
            print(f"  {label:<50} {pct:>9.1f}%")
        except Exception:
            pass

def export_csv(move_profiles, window, path="pre_move_patterns.csv"):
    df = pd.DataFrame(move_profiles[window])
    df.to_csv(path, index=False)
    print(f"\n  [CSV] Exported {len(df)} rows → {path}")

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="NEPSE Pre-Move Pattern Backtest")
    parser.add_argument("--db",         default=DEFAULT_DB,  help="Path to nepse_market_data.db")
    parser.add_argument("--move-pct",   type=float, default=MOVE_PCT,   help="Min gain %% to qualify as a move")
    parser.add_argument("--move-days",  type=int,   default=MOVE_DAYS,  help="Max days within which gain must occur")
    parser.add_argument("--export-csv", action="store_true",            help="Export raw pattern data to CSV")
    args = parser.parse_args()

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║       NEPSE PRE-MOVE PATTERN RECOGNITION BACKTEST               ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"  DB          : {args.db}")
    print(f"  Move def    : ≥{args.move_pct}% within {args.move_days} trading days")
    print(f"  Pre-windows : {PRE_WINDOWS} days")
    print()

    conn = connect_db(args.db)

    print("[1/5] Loading price data...")
    df = load_all_prices(conn)

    print("[2/5] Computing indicators...")
    df = compute_indicators(df)

    print("[3/5] Detecting significant moves...")
    moves = find_moves(df, move_pct=args.move_pct, move_days=args.move_days)
    if not moves:
        print("[ERROR] No moves found. Try lowering --move-pct or --move-days.")
        sys.exit(1)

    print("[4/5] Profiling pre-move windows...")
    move_profiles = profile_all_moves(df, moves)

    print("[5/5] Building baseline (random non-move windows)...")
    baseline_profiles = build_baseline(df, moves)

    # ── Reports ──
    print_move_distribution(moves)
    print_seasonal_pattern(moves)

    for w in PRE_WINDOWS:
        if move_profiles.get(w) and baseline_profiles.get(w):
            print_pattern_report(move_profiles[w], baseline_profiles[w], w)
            print_combined_signal_stats(move_profiles[w], w)
        else:
            print(f"\n[WARN] Not enough data for window={w}")

    if args.export_csv:
        for w in PRE_WINDOWS:
            if move_profiles.get(w):
                export_csv(move_profiles, w, path=f"pre_move_patterns_{w}d.csv")

    print()
    print("═" * 70)
    print("  DONE. Run with --export-csv to save full pattern data to CSV.")
    print("  Tip: Run option 35 on high-frequency movers shown above.")
    print("═" * 70)
    print()

if __name__ == "__main__":
    main()
