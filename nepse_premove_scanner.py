"""
nepse_premove_scanner.py  –  NEPSE Pre-Move Alert Scanner
==========================================================
Scores every stock daily on the 5 backtest-proven signals:
  1. Vol surge last 3 days (>1.5x)          edge: +43.3%
  2. Price range % expanding                 edge: +40.4%
  3. Avg daily range compression             edge: +28.3%
  4. Vol trending up                         edge: +7.7%  (confirmed across all windows)
  5. RSI trending up                         edge: +10.3%

Negative signals (logged as warnings):
  - Price consolidating <8% band            edge: -15.9%
  - Near support <5%                        edge: -33.2%
  - Price basing (flat)                     edge: -24.9%

Usage:
  python nepse_premove_scanner.py
  python nepse_premove_scanner.py --top 20
  python nepse_premove_scanner.py --min-score 3
  python nepse_premove_scanner.py --export
  python nepse_premove_scanner.py --symbol NABIL
"""

import sqlite3
import argparse
import sys
from datetime import datetime, date
import pandas as pd
import numpy as np

DB_PATH = "nepse_market_data.db"
TABLE   = "stock_prices"

# ── Signal weights (proportional to edge magnitude) ─────────────────────────
SIG_WEIGHTS = {
    "vol_surge_3d":        4.3,   # +43.3% edge
    "price_range_expand":  4.0,   # +40.4% edge
    "range_compression":   2.8,   # +28.3% edge
    "vol_trending_up":     1.8,   # +18.0% edge (10d window)
    "rsi_trending_up":     1.3,   # +12.6% edge (10d window)
}
MAX_SCORE = sum(SIG_WEIGHTS.values())   # 14.2


def _fmt_npr(val):
    """Format large numbers in Nepali style (Crore/Lakh)."""
    if val is None or np.isnan(val):
        return "N/A"
    if val >= 1e7:
        return f"{val/1e7:.2f}Cr"
    if val >= 1e5:
        return f"{val/1e5:.2f}L"
    return f"{val:,.0f}"


def load_data(conn: sqlite3.Connection, lookback: int = 60) -> pd.DataFrame:
    """Load last `lookback` trading days for equity symbols only.

    Excludes debentures, bonds, and mutual funds by filtering out symbols
    that end with known non-equity suffixes:
      - Debentures/bonds : digits at end e.g. CBLD88, NICD88, EBLD86, JSLBB
      - Mutual funds     : start with upper 'K' pattern or contain 'MF'/'FUND'
    A symbol is kept only if it looks like a plain equity ticker
    (2-6 uppercase letters, no trailing digits).
    """
    query = f"""
        SELECT symbol, date, open, high, low, close, volume
        FROM {TABLE}
        WHERE date >= (
            SELECT date(MAX(date), '-{lookback*2} days') FROM {TABLE}
        )
        ORDER BY symbol, date
    """
    df = pd.read_sql_query(query, conn, parse_dates=["date"])
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

    # ── Equity filter ────────────────────────────────────────────────────────
    import re
    # Keep only symbols that are purely alphabetic (no trailing digits)
    # and do not contain known non-equity keywords
    EXCLUDE_KEYWORDS = ["MF", "FUND", "BOND", "DBL", "DEBD", "DEBB"]
    def is_equity(sym: str) -> bool:
        if not re.match(r'^[A-Z]{2,10}$', sym):   # must be all letters
            return False
        for kw in EXCLUDE_KEYWORDS:
            if kw in sym:
                return False
        return True

    before = df["symbol"].nunique()
    equity_syms = [s for s in df["symbol"].unique() if is_equity(s)]
    df = df[df["symbol"].isin(equity_syms)].reset_index(drop=True)
    after = df["symbol"].nunique()
    print(f"  Equity filter: {before} → {after} symbols (removed {before - after} non-equity)")

    # ── Minimum liquidity filter: skip stocks with near-zero avg volume ──────
    vol_mean = df.groupby("symbol")["volume"].mean()
    liquid_syms = vol_mean[vol_mean >= 500].index
    df = df[df["symbol"].isin(liquid_syms)].reset_index(drop=True)
    print(f"  Liquidity filter: {after} → {df['symbol'].nunique()} symbols (min avg vol 500)")

    return df


def compute_rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    delta  = closes.diff()
    gain   = delta.clip(lower=0)
    loss   = (-delta).clip(lower=0)
    avg_g  = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_l  = loss.ewm(com=period - 1, min_periods=period).mean()
    rs     = avg_g / avg_l.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def score_stock(grp: pd.DataFrame) -> dict | None:
    """Score one stock's recent data. Returns None if insufficient history."""
    grp = grp.tail(30).copy()
    if len(grp) < 20:
        return None

    closes  = grp["close"].values
    volumes = grp["volume"].values
    highs   = grp["high"].values
    lows    = grp["low"].values

    last_close  = closes[-1]
    last_vol    = volumes[-1]
    last_date   = grp["date"].iloc[-1]

    # ── Vol 20-day moving average ────────────────────────────────────────────
    vol_ma20 = np.nanmean(volumes[-20:])

    # ── Signal 1: Vol surge last 3 days (>1.5x of 20d MA) ───────────────────
    vol_3d_avg = np.nanmean(volumes[-3:])
    vol_surge_3d = (vol_3d_avg / vol_ma20) > 1.5 if vol_ma20 > 0 else False

    # ── Signal 2: Price range % expanding (last 5d range > prior 5d range) ──
    range_last5  = np.nanmean((highs[-5:]  - lows[-5:])  / lows[-5:])  * 100
    range_prev5  = np.nanmean((highs[-10:-5] - lows[-10:-5]) / lows[-10:-5]) * 100
    price_range_expand = range_last5 > range_prev5 * 1.1   # 10% wider

    # ── Signal 3: Daily range compression (ATR shrinking = squeeze) ─────────
    atr5  = np.nanmean((highs[-5:]  - lows[-5:])  / closes[-5:])
    atr10 = np.nanmean((highs[-10:] - lows[-10:]) / closes[-10:])
    range_compression = atr5 < atr10 * 0.85  # recent range 15% tighter

    # ── Signal 4: Volume trending up (5d MA vol > 10d MA vol) ───────────────
    vol_ma5  = np.nanmean(volumes[-5:])
    vol_ma10 = np.nanmean(volumes[-10:])
    vol_trending_up = vol_ma5 > vol_ma10 * 1.05

    # ── Signal 5: RSI trending up ────────────────────────────────────────────
    rsi_series = compute_rsi(grp["close"], 14)
    rsi_vals   = rsi_series.dropna().values
    if len(rsi_vals) >= 5:
        rsi_now  = rsi_vals[-1]
        rsi_5ago = rsi_vals[-5]
        rsi_trending_up = rsi_now > rsi_5ago + 3
    else:
        rsi_now = np.nan
        rsi_trending_up = False

    # ── Negative signals (warning flags) ────────────────────────────────────
    price_hi5  = np.max(closes[-5:])
    price_lo5  = np.min(closes[-5:])
    band_pct   = (price_hi5 - price_lo5) / price_lo5 * 100 if price_lo5 > 0 else 0
    consolidating = band_pct < 8.0

    # Support: use 20d low as proxy support
    support_20d   = np.min(lows[-20:])
    dist_support  = (last_close - support_20d) / support_20d * 100 if support_20d > 0 else 100
    near_support  = dist_support < 5.0

    # Basing: flat price over 10 days
    ret_10d    = abs((closes[-1] - closes[-10]) / closes[-10]) * 100 if closes[-10] > 0 else 99
    price_basing = ret_10d < 3.0

    # ── Score calculation ────────────────────────────────────────────────────
    signals = {
        "vol_surge_3d":       vol_surge_3d,
        "price_range_expand": price_range_expand,
        "range_compression":  range_compression,
        "vol_trending_up":    vol_trending_up,
        "rsi_trending_up":    rsi_trending_up,
    }
    raw_score  = sum(SIG_WEIGHTS[k] for k, v in signals.items() if v)
    pct_score  = round(raw_score / MAX_SCORE * 100, 1)
    sig_count  = sum(signals.values())

    # ── Change metrics ───────────────────────────────────────────────────────
    chg1d  = (closes[-1] / closes[-2]  - 1) * 100 if len(closes) >= 2  and closes[-2]  > 0 else np.nan
    chg5d  = (closes[-1] / closes[-5]  - 1) * 100 if len(closes) >= 5  and closes[-5]  > 0 else np.nan
    chg20d = (closes[-1] / closes[-20] - 1) * 100 if len(closes) >= 20 and closes[-20] > 0 else np.nan

    return {
        "symbol":           grp["symbol"].iloc[0],
        "date":             last_date.strftime("%Y-%m-%d"),
        "close":            round(last_close, 2),
        "chg_1d":           round(chg1d,  2) if not np.isnan(chg1d)  else None,
        "chg_5d":           round(chg5d,  2) if not np.isnan(chg5d)  else None,
        "chg_20d":          round(chg20d, 2) if not np.isnan(chg20d) else None,
        "volume":           int(last_vol),
        "vol_vs_ma20":      round(last_vol / vol_ma20, 2) if vol_ma20 > 0 else None,
        "rsi":              round(rsi_now, 1) if not np.isnan(rsi_now) else None,
        "score_pct":        pct_score,
        "sig_count":        sig_count,
        # individual signals
        "sig_vol_surge":    vol_surge_3d,
        "sig_range_expand": price_range_expand,
        "sig_compression":  range_compression,
        "sig_vol_trend":    vol_trending_up,
        "sig_rsi_up":       rsi_trending_up,
        # warning flags
        "warn_consolidating": consolidating,
        "warn_near_support":  near_support,
        "warn_basing":        price_basing,
        "warn_count":         int(consolidating) + int(near_support) + int(price_basing),
    }


def signal_bar(row: dict) -> str:
    """Compact visual signal bar."""
    parts = [
        ("V3", row["sig_vol_surge"]),
        ("RE", row["sig_range_expand"]),
        ("RC", row["sig_compression"]),
        ("VT", row["sig_vol_trend"]),
        ("RI", row["sig_rsi_up"]),
    ]
    on  = " ".join(k for k, v in parts if v)
    off = " ".join(k for k, v in parts if not v)
    bar = f"[{'●' * row['sig_count']}{'○' * (5 - row['sig_count'])}]"
    return f"{bar}  ON:{on or '-'}  off:{off or '-'}"


def warn_bar(row: dict) -> str:
    flags = []
    if row["warn_consolidating"]: flags.append("TIGHT_BAND")
    if row["warn_near_support"]:  flags.append("NEAR_SUP")
    if row["warn_basing"]:        flags.append("FLAT_BASE")
    return "  ⚠ " + " | ".join(flags) if flags else ""


def print_results(results: list[dict], top_n: int, min_score: int):
    df = pd.DataFrame(results)
    df = df[df["sig_count"] >= min_score]
    df = df.sort_values("score_pct", ascending=False).head(top_n)

    if df.empty:
        print(f"\n  No stocks with ≥{min_score} signals today.\n")
        return

    as_of = df["date"].iloc[0]
    print()
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║          NEPSE PRE-MOVE ALERT SCANNER                                   ║")
    print(f"║          As of: {as_of}   |   Min signals: {min_score}   |   Showing top {top_n}         ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()
    print("  Signal legend:  V3=VolSurge3d  RE=RangeExpand  RC=Compression  VT=VolTrend  RI=RSIup")
    print()
    print(f"  {'#':>3}  {'SYMBOL':<8}  {'CLOSE':>7}  {'1D%':>6}  {'5D%':>6}  {'VOL/MA':>6}  {'RSI':>5}  {'SCORE':>5}  SIGNALS")
    print(f"  {'─'*3}  {'─'*8}  {'─'*7}  {'─'*6}  {'─'*6}  {'─'*6}  {'─'*5}  {'─'*5}  {'─'*40}")

    for i, row in enumerate(df.to_dict("records"), 1):
        chg1  = f"{row['chg_1d']:+.1f}%" if row["chg_1d"] is not None else "  N/A"
        chg5  = f"{row['chg_5d']:+.1f}%" if row["chg_5d"] is not None else "  N/A"
        volma = f"{row['vol_vs_ma20']:.2f}x"     if row["vol_vs_ma20"] is not None else "  N/A"
        rsi   = f"{row['rsi']:.0f}"              if row["rsi"] is not None else " N/A"
        score = f"{row['score_pct']:.0f}%"

        bar   = signal_bar(row)
        warns = warn_bar(row)

        print(f"  {i:>3}  {row['symbol']:<8}  {row['close']:>7,.1f}  {chg1:>6}  {chg5:>6}  {volma:>6}  {rsi:>5}  {score:>5}  {bar}{warns}")

    print()

    # ── All-4-signals group ──────────────────────────────────────────────────
    all4 = df[df["sig_count"] >= 4]
    if not all4.empty:
        print("  ★  ALL 4+ SIGNALS ALIGNED (highest quality setups):")
        for _, r in all4.iterrows():
            warns = warn_bar(r)
            print(f"     → {r['symbol']:<8}  score:{r['score_pct']:.0f}%  RSI:{r['rsi']:.0f}  vol:{r['vol_vs_ma20']:.2f}x{warns}")
        print()

    # ── Summary ──────────────────────────────────────────────────────────────
    total_scanned = len(results)
    hit_3plus = len([r for r in results if r["sig_count"] >= 3])
    hit_4plus = len([r for r in results if r["sig_count"] >= 4])
    hit_5     = len([r for r in results if r["sig_count"] == 5])
    print(f"  Scanned: {total_scanned} stocks  |  ≥3 signals: {hit_3plus}  |  ≥4 signals: {hit_4plus}  |  All 5: {hit_5}")
    print()


def export_csv(results: list[dict]):
    df = pd.DataFrame(results)
    df = df.sort_values("score_pct", ascending=False)
    ts  = datetime.now().strftime("%Y%m%d_%H%M")
    fn  = f"premove_scan_{ts}.csv"
    df.to_csv(fn, index=False)
    print(f"  [EXPORT] Saved {len(df)} rows → {fn}")


def single_stock_report(results: list[dict], symbol: str):
    symbol = symbol.upper()
    row = next((r for r in results if r["symbol"] == symbol), None)
    if row is None:
        print(f"\n  Symbol '{symbol}' not found or insufficient data.\n")
        return
    print()
    print(f"  ╔══ PRE-MOVE SIGNAL REPORT: {symbol} ══╗")
    print(f"  Date       : {row['date']}")
    print(f"  Close      : Rs {row['close']:,.2f}   1d: {row['chg_1d']:+.1f}%   5d: {row['chg_5d']:+.1f}%   20d: {row['chg_20d']:+.1f}%")
    print(f"  Volume     : {_fmt_npr(row['volume'])}   ({row['vol_vs_ma20']:.2f}x 20d MA)")
    print(f"  RSI(14)    : {row['rsi']}")
    print(f"  Score      : {row['score_pct']}%   ({row['sig_count']}/5 signals active)")
    print()
    print(f"  POSITIVE SIGNALS:")
    sigs = [
        ("Vol surge last 3d (>1.5x MA)",  "sig_vol_surge",    "+43.3%"),
        ("Price range expanding",          "sig_range_expand", "+40.4%"),
        ("Daily range compression",        "sig_compression",  "+28.3%"),
        ("Volume trending up",             "sig_vol_trend",    "+18.0%"),
        ("RSI trending up",                "sig_rsi_up",       "+12.6%"),
    ]
    for label, key, edge in sigs:
        mark = "✓" if row[key] else "✗"
        print(f"    {mark}  {label:<38}  edge: {edge}")
    print()
    if row["warn_count"] > 0:
        print(f"  WARNING FLAGS (negative edge signals present):")
        if row["warn_consolidating"]: print("    ⚠  Price consolidating in tight band (<8%)  edge: -15.9%")
        if row["warn_near_support"]:  print("    ⚠  Near support level (<5%)                edge: -33.2%")
        if row["warn_basing"]:        print("    ⚠  Price basing / flat (ret10d < 3%)       edge: -24.9%")
        print()


def main():
    parser = argparse.ArgumentParser(description="NEPSE Pre-Move Alert Scanner")
    parser.add_argument("--top",       type=int,  default=30,    help="Show top N results (default: 30)")
    parser.add_argument("--min-score", type=int,  default=2,     help="Min signals required (default: 2)")
    parser.add_argument("--export",    action="store_true",      help="Export full results to CSV")
    parser.add_argument("--symbol",    type=str,  default=None,  help="Single stock deep report")
    args = parser.parse_args()

    print(f"\n  [NEPSE Pre-Move Scanner]  Loading data from {DB_PATH}...")

    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"  [ERROR] Cannot connect to DB: {e}")
        sys.exit(1)

    df = load_data(conn, lookback=60)
    conn.close()

    if df.empty:
        print("  [ERROR] No data loaded.")
        sys.exit(1)

    print(f"  Loaded {len(df):,} rows | {df['symbol'].nunique()} symbols | scoring signals...")

    results = []
    for sym, grp in df.groupby("symbol"):
        result = score_stock(grp)
        if result:
            results.append(result)

    if args.symbol:
        single_stock_report(results, args.symbol)
    else:
        print_results(results, top_n=args.top, min_score=args.min_score)

    if args.export:
        export_csv(results)


if __name__ == "__main__":
    main()
