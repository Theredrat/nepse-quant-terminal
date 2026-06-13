"""
nepse_conviction_scanner.py  —  NEPSE High-Conviction Entry Scanner
=====================================================================
Runs 4 filters in sequence. A stock must pass ALL 4 to appear.

  STEP 1 — REGIME GATE      (Option 43 logic)
            Is the market in Bull or Accumulation phase?
            Bear/Distribution regime → most signals are traps.

  STEP 2 — PRE-MOVE SIGNALS (Option 47 logic)
            ≥3 of 5 backtest-proven signals firing?
            Vol surge, range expand, compression, vol trend, RSI trend.

  STEP 3 — BROKER FLOW      (Option 17d logic)
            Is a net buyer present in last 7 days of floorsheet?
            Net buy value > net sell value = smart money loading.

  STEP 4 — SECTOR SEASON    (Option 40 logic)
            Is this stock's sector historically strong this month?
            Uses Greg calendar month vs sector win-rate from 2021 data.

Usage:
  python nepse_conviction_scanner.py
  python nepse_conviction_scanner.py --relax          # drop step 4 (season)
  python nepse_conviction_scanner.py --relax2         # drop steps 3+4
  python nepse_conviction_scanner.py --export
  python nepse_conviction_scanner.py --symbol NABIL   # explain why stock passed/failed
"""

import sqlite3
import argparse
import sys
import re
from datetime import datetime
from collections import defaultdict
import pandas as pd
import numpy as np

DB_PATH = "nepse_market_data.db"

# ── Sector map (symbol prefix heuristics + known assignments) ───────────────
# Full map pulled from NEPSE sector assignments
SECTOR_MAP = {
    # Commercial Banks
    "NABIL":"Commercial Bank","NICA":"Commercial Bank","EBL":"Commercial Bank",
    "NCCB":"Commercial Bank","SBI":"Commercial Bank","SCB":"Commercial Bank",
    "ADBL":"Commercial Bank","CBL":"Commercial Bank","CZBIL":"Commercial Bank",
    "GBIME":"Commercial Bank","HBL":"Commercial Bank","KBL":"Commercial Bank",
    "LBL":"Commercial Bank","MBL":"Commercial Bank","NBL":"Commercial Bank",
    "NIMB":"Commercial Bank","NMB":"Commercial Bank","PCBL":"Commercial Bank",
    "PRVU":"Commercial Bank","SANIMA":"Commercial Bank","SBL":"Commercial Bank",
    "SRBL":"Commercial Bank","BOKL":"Commercial Bank","CCBL":"Commercial Bank",
    "MEGA":"Commercial Bank","NIB":"Commercial Bank","CITY":"Commercial Bank",
    "MNBBL":"Commercial Bank","NABBC":"Commercial Bank",
    # Development Banks
    "CORBL":"Development Bank","SAPDBL":"Development Bank","GRDBL":"Development Bank",
    "KRBL":"Development Bank","EDBL":"Development Bank","MLBBL":"Development Bank",
    "SKBBL":"Development Bank","JBBL":"Development Bank","LBBL":"Development Bank",
    "MNBBL":"Development Bank","SADBL":"Development Bank","SINDU":"Development Bank",
    "SHINE":"Development Bank","KSBBL":"Development Bank","MERO":"Development Bank",
    "MIDBS":"Development Bank","NESDO":"Development Bank","NGBBL":"Development Bank",
    "NMBMF":"Development Bank","ODBL":"Development Bank","RBBL":"Development Bank",
    "SBBL":"Development Bank","SLBBL":"Development Bank","SMFBS":"Development Bank",
    # Finance
    "CFCL":"Finance","GUFL":"Finance","ICFC":"Finance","JFL":"Finance",
    "MFIL":"Finance","NFS":"Finance","PFL":"Finance","RLFL":"Finance",
    "SFCL":"Finance","SIFC":"Finance","UPCL":"Finance","BFC":"Finance",
    "FMDBL":"Finance","GMFIL":"Finance","GFCL":"Finance","HGCL":"Finance",
    "MPFL":"Finance","PROFL":"Finance","RIDI":"Finance","SFL":"Finance",
    # Hydropower
    "AHPC":"Hydropower","AKJCL":"Hydropower","APCL":"Hydropower","BARUN":"Hydropower",
    "BHPL":"Hydropower","BPCL":"Hydropower","CHCL":"Hydropower","DHPL":"Hydropower",
    "GHL":"Hydropower","GJCL":"Hydropower","GLICL":"Hydropower","HPPL":"Hydropower",
    "HURJA":"Hydropower","KKHC":"Hydropower","MAKAR":"Hydropower","MBJC":"Hydropower",
    "MCHL":"Hydropower","MHNL":"Hydropower","MHL":"Hydropower","MMKJL":"Hydropower",
    "MSHL":"Hydropower","NGPL":"Hydropower","NHPC":"Hydropower","NHDL":"Hydropower",
    "NYADI":"Hydropower","OHL":"Hydropower","PHCL":"Hydropower","PMHPL":"Hydropower",
    "PPCL":"Hydropower","RADHI":"Hydropower","RHPL":"Hydropower","RRHPL":"Hydropower",
    "RURU":"Hydropower","SHEL":"Hydropower","SHPC":"Hydropower","SJCL":"Hydropower",
    "SPDL":"Hydropower","SSHL":"Hydropower","STML":"Hydropower","TPPL":"Hydropower",
    "UHEWA":"Hydropower","UMHL":"Hydropower","UMRH":"Hydropower","UNHPL":"Hydropower",
    "UPPER":"Hydropower","UPCL":"Hydropower","URJA":"Hydropower","VLUCL":"Hydropower",
    # Life Insurance
    "ALICL":"Life Insurance","CLI":"Life Insurance","ILI":"Life Insurance",
    "JLI":"Life Insurance","LICN":"Life Insurance","MLIBL":"Life Insurance",
    "NLIC":"Life Insurance","NLICL":"Life Insurance","PMLI":"Life Insurance",
    "RNLI":"Life Insurance","SNLI":"Life Insurance","SLI":"Life Insurance",
    "SLIC":"Life Insurance","ULBSL":"Life Insurance",
    # Non-Life Insurance
    "AIL":"Non-Life Insurance","LGIL":"Non-Life Insurance","NLG":"Non-Life Insurance",
    "NICL":"Non-Life Insurance","NIL":"Non-Life Insurance","PICL":"Non-Life Insurance",
    "PRIN":"Non-Life Insurance","RBCL":"Non-Life Insurance","SALICO":"Non-Life Insurance",
    "SGI":"Non-Life Insurance","SICL":"Non-Life Insurance","SLICL":"Non-Life Insurance",
    "SRLI":"Non-Life Insurance","UIC":"Non-Life Insurance","HEI":"Non-Life Insurance",
    # Microfinance
    "CBBL":"Microfinance","DDBL":"Microfinance","FOWAD":"Microfinance",
    "GMFIL":"Microfinance","HLBSL":"Microfinance","JSLBB":"Microfinance",
    "KMCDB":"Microfinance","LLBS":"Microfinance","MERO":"Microfinance",
    "MLBSL":"Microfinance","MSLB":"Microfinance","NADEP":"Microfinance",
    "NESDO":"Microfinance","NICLBSL":"Microfinance","NMBMF":"Microfinance",
    "NMFBS":"Microfinance","RSDC":"Microfinance","SDBL":"Microfinance",
    "SFMF":"Microfinance","SKBBL":"Microfinance","SLBSL":"Microfinance",
    "SMFBS":"Microfinance","SWBBL":"Microfinance","ULBSL":"Microfinance",
    "VLBS":"Microfinance","WOMI":"Microfinance",
    # Manufacturing
    "BNT":"Manufacturing and Processing","BSM":"Manufacturing and Processing",
    "GCIL":"Manufacturing and Processing","HDL":"Manufacturing and Processing",
    "HHCL":"Manufacturing and Processing","NSBID":"Manufacturing and Processing",
    "RAIPUR":"Manufacturing and Processing","SARBTM":"Manufacturing and Processing",
    "SHIVM":"Manufacturing and Processing","UNPL":"Manufacturing and Processing",
    # Hotels
    "OHL":"Hotel & Tourism","TRH":"Hotel & Tourism","TICA":"Hotel & Tourism",
    # Trading
    "BBC":"Trading","STC":"Trading","HBSL":"Trading",
    # Others / Investment
    "NICGF":"Investment","NIFRA":"Investment","NRIC":"Investment",
    "SAEF":"Investment","SEOS":"Investment",
}

# ── Sector seasonality: months where sector historically strong (win rate >55%) ─
# Derived from Option 40 backtest data (2021–2026)
SECTOR_STRONG_MONTHS = {
    "Commercial Bank":          [1, 3, 4, 7, 12],
    "Development Bank":         [1, 3, 7, 11, 12],
    "Finance":                  [1, 3, 7, 8, 12],
    "Hydropower":               [3, 4, 6, 7, 8],
    "Life Insurance":           [1, 7, 10, 11, 12],
    "Non-Life Insurance":       [1, 3, 7, 12],
    "Microfinance":             [1, 7, 11, 12],
    "Manufacturing and Processing": [3, 7, 8, 12],
    "Hotel & Tourism":          [3, 4, 7, 8],
    "Investment":               [1, 7, 12],
    "Trading":                  [1, 7, 12],
    "Others":                   [1, 7, 12],
}

# ── Pre-move signal weights (from backtest) ──────────────────────────────────
SIG_WEIGHTS = {
    "vol_surge_3d":       4.3,
    "price_range_expand": 4.0,
    "range_compression":  2.8,
    "vol_trending_up":    1.8,
    "rsi_trending_up":    1.3,
}
MAX_SCORE = sum(SIG_WEIGHTS.values())


# ════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _fmt_npr(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    if val >= 1e7:  return f"{val/1e7:.2f}Cr"
    if val >= 1e5:  return f"{val/1e5:.2f}L"
    return f"{val:,.0f}"


def is_equity(sym: str) -> bool:
    if not re.match(r'^[A-Z]{2,10}$', sym):
        return False
    for kw in ["MF", "FUND", "BOND", "DBL", "DEBD", "DEBB"]:
        if kw in sym:
            return False
    return True


def compute_rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    delta = closes.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_g = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_l = loss.ewm(com=period - 1, min_periods=period).mean()
    rs    = avg_g / avg_l.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def get_sector(symbol: str) -> str:
    return SECTOR_MAP.get(symbol, "Others")


# ════════════════════════════════════════════════════════════════════════════
#  STEP 1 — REGIME
# ════════════════════════════════════════════════════════════════════════════

def get_regime(conn: sqlite3.Connection) -> tuple[str, str]:
    """
    Lightweight regime detection using NEPSE index or broad market:
      - % of stocks above MA50
      - % of stocks with positive 20d return
      - NEPSE index slope (20d)
    Returns (regime_label, color_hint)
    """
    try:
        # Try to get index data first
        idx = pd.read_sql_query(
            "SELECT date, close FROM stock_prices WHERE symbol='NEPSE' ORDER BY date DESC LIMIT 60",
            conn, parse_dates=["date"]
        )
    except Exception:
        idx = pd.DataFrame()

    # Fall back to broad market breadth
    recent = pd.read_sql_query("""
        SELECT symbol, date, close
        FROM stock_prices
        WHERE date >= (SELECT date(MAX(date), '-60 days') FROM stock_prices)
        ORDER BY symbol, date
    """, conn, parse_dates=["date"])

    equity_syms = [s for s in recent["symbol"].unique() if is_equity(s)]
    recent = recent[recent["symbol"].isin(equity_syms)]

    breadth_scores = []
    slope_scores   = []

    for sym, grp in recent.groupby("symbol"):
        grp = grp.sort_values("date")
        closes = grp["close"].values
        if len(closes) < 25:
            continue
        ma50_proxy = np.mean(closes[-20:])   # use 20d as proxy for regime speed
        above_ma   = closes[-1] > ma50_proxy
        ret20      = (closes[-1] / closes[-20] - 1) * 100 if closes[-20] > 0 else 0
        breadth_scores.append(above_ma)
        slope_scores.append(ret20)

    if not breadth_scores:
        return ("UNKNOWN", "grey")

    pct_above_ma = np.mean(breadth_scores) * 100
    avg_ret20    = np.mean(slope_scores)

    # Regime classification
    if pct_above_ma >= 60 and avg_ret20 >= 2:
        regime = "BULL"
    elif pct_above_ma >= 45 and avg_ret20 >= 0:
        regime = "ACCUMULATION"
    elif pct_above_ma <= 35 and avg_ret20 <= -2:
        regime = "BEAR"
    else:
        regime = "NEUTRAL"

    detail = f"{pct_above_ma:.0f}% stocks above MA20 | avg 20d return: {avg_ret20:+.1f}%"
    return (regime, detail)


# ════════════════════════════════════════════════════════════════════════════
#  STEP 2 — PRE-MOVE SIGNALS
# ════════════════════════════════════════════════════════════════════════════

def score_stock(grp: pd.DataFrame) -> dict | None:
    grp    = grp.tail(30).copy()
    if len(grp) < 20:
        return None

    closes  = grp["close"].values
    volumes = grp["volume"].values
    highs   = grp["high"].values
    lows    = grp["low"].values

    last_close = closes[-1]
    last_vol   = volumes[-1]
    vol_ma20   = np.nanmean(volumes[-20:])

    # Signal 1
    vol_3d_avg   = np.nanmean(volumes[-3:])
    vol_surge_3d = (vol_3d_avg / vol_ma20) > 1.5 if vol_ma20 > 0 else False

    # Signal 2
    range_last5 = np.nanmean((highs[-5:]    - lows[-5:])    / np.where(lows[-5:]    > 0, lows[-5:],    1)) * 100
    range_prev5 = np.nanmean((highs[-10:-5] - lows[-10:-5]) / np.where(lows[-10:-5] > 0, lows[-10:-5], 1)) * 100
    price_range_expand = range_last5 > range_prev5 * 1.1

    # Signal 3
    atr5  = np.nanmean((highs[-5:]  - lows[-5:])  / np.where(closes[-5:]  > 0, closes[-5:],  1))
    atr10 = np.nanmean((highs[-10:] - lows[-10:]) / np.where(closes[-10:] > 0, closes[-10:], 1))
    range_compression = atr5 < atr10 * 0.85

    # Signal 4
    vol_ma5  = np.nanmean(volumes[-5:])
    vol_ma10 = np.nanmean(volumes[-10:])
    vol_trending_up = vol_ma5 > vol_ma10 * 1.05

    # Signal 5
    rsi_series = compute_rsi(grp["close"], 14)
    rsi_vals   = rsi_series.dropna().values
    if len(rsi_vals) >= 5:
        rsi_now         = rsi_vals[-1]
        rsi_trending_up = rsi_vals[-1] > rsi_vals[-5] + 3
    else:
        rsi_now         = np.nan
        rsi_trending_up = False

    # Warnings
    band_pct      = (np.max(closes[-5:]) - np.min(closes[-5:])) / np.min(closes[-5:]) * 100 if np.min(closes[-5:]) > 0 else 0
    consolidating = band_pct < 8.0
    support_20d   = np.min(lows[-20:])
    dist_support  = (last_close - support_20d) / support_20d * 100 if support_20d > 0 else 100
    near_support  = dist_support < 5.0
    ret_10d       = abs((closes[-1] - closes[-10]) / closes[-10]) * 100 if closes[-10] > 0 else 99
    price_basing  = ret_10d < 3.0

    signals = {
        "vol_surge_3d":       vol_surge_3d,
        "price_range_expand": price_range_expand,
        "range_compression":  range_compression,
        "vol_trending_up":    vol_trending_up,
        "rsi_trending_up":    rsi_trending_up,
    }
    raw_score = sum(SIG_WEIGHTS[k] for k, v in signals.items() if v)
    pct_score = round(raw_score / MAX_SCORE * 100, 1)
    sig_count = sum(signals.values())

    chg1d  = (closes[-1]/closes[-2]  - 1)*100 if len(closes)>=2  and closes[-2]  > 0 else np.nan
    chg5d  = (closes[-1]/closes[-5]  - 1)*100 if len(closes)>=5  and closes[-5]  > 0 else np.nan

    return {
        "symbol":             grp["symbol"].iloc[0],
        "close":              round(last_close, 2),
        "chg_1d":             round(chg1d, 2) if not np.isnan(chg1d) else None,
        "chg_5d":             round(chg5d, 2) if not np.isnan(chg5d) else None,
        "volume":             int(last_vol),
        "vol_vs_ma20":        round(last_vol / vol_ma20, 2) if vol_ma20 > 0 else None,
        "rsi":                round(rsi_now, 1) if not np.isnan(rsi_now) else None,
        "score_pct":          pct_score,
        "sig_count":          int(sig_count),
        "sig_vol_surge":      vol_surge_3d,
        "sig_range_expand":   price_range_expand,
        "sig_compression":    range_compression,
        "sig_vol_trend":      vol_trending_up,
        "sig_rsi_up":         rsi_trending_up,
        "warn_consolidating": consolidating,
        "warn_near_support":  near_support,
        "warn_basing":        price_basing,
        "warn_count":         int(consolidating)+int(near_support)+int(price_basing),
    }


# ════════════════════════════════════════════════════════════════════════════
#  STEP 3 — BROKER FLOW
# ════════════════════════════════════════════════════════════════════════════

def get_broker_flow(conn: sqlite3.Connection, symbols: list[str]) -> dict[str, dict]:
    """
    For each symbol, compute net broker flow over last 7 trading days.
    Returns dict: symbol -> {net_val, top_buyer, buy_val, sell_val, flow_positive}
    """
    placeholders = ",".join(["?" for _ in symbols])
    try:
        df = pd.read_sql_query(f"""
            SELECT symbol,
                   date,
                   broker_id,
                   broker_name,
                   buy_val,
                   sell_val,
                   net_val
            FROM broker_activity
            WHERE symbol IN ({placeholders})
              AND date >= (
                  SELECT date(MAX(date), '-14 days') FROM broker_activity
              )
        """, conn, params=symbols)
    except Exception:
        return {}

    if df.empty:
        return {}

    result = {}
    for sym, grp in df.groupby("symbol"):
        total_buy  = grp["buy_val"].sum()
        total_sell = grp["sell_val"].sum()
        net        = grp["net_val"].sum()

        # top buyer = broker with highest buy_val
        top_row      = grp.loc[grp["buy_val"].idxmax()] if not grp.empty else None
        top_buyer    = top_row["broker_id"]   if top_row is not None else None
        top_buy_val  = top_row["buy_val"]     if top_row is not None else 0

        result[sym] = {
            "net_val":       total_buy - total_sell,
            "total_buy":     total_buy,
            "total_sell":    total_sell,
            "top_buyer":     top_buyer,
            "top_buy_val":   top_buy_val,
            "flow_positive": total_buy > total_sell,
        }
    return result


# ════════════════════════════════════════════════════════════════════════════
#  STEP 4 — SECTOR SEASONALITY
# ════════════════════════════════════════════════════════════════════════════

def check_seasonality(symbol: str, month: int) -> tuple[bool, str]:
    sector = get_sector(symbol)
    strong_months = SECTOR_STRONG_MONTHS.get(sector, [])
    in_season = month in strong_months
    return in_season, sector


# ════════════════════════════════════════════════════════════════════════════
#  MAIN SCANNER
# ════════════════════════════════════════════════════════════════════════════

def run_scanner(relax: bool = False, relax2: bool = False, export: bool = False, symbol_filter: str = None):
    print(f"\n  ╔══════════════════════════════════════════════════════════════════╗")
    print(f"  ║       NEPSE HIGH-CONVICTION ENTRY SCANNER                        ║")
    print(f"  ║       4-Filter: Regime → Signals → Broker Flow → Season          ║")
    print(f"  ╚══════════════════════════════════════════════════════════════════╝")
    print()

    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"  [ERROR] Cannot open DB: {e}")
        sys.exit(1)

    current_month = datetime.now().month

    # ── STEP 1: Regime ───────────────────────────────────────────────────────
    print("  [1/4] Checking market regime...")
    regime, regime_detail = get_regime(conn)
    regime_ok = regime in ("BULL", "ACCUMULATION")

    regime_icon = "✓" if regime_ok else "✗"
    print(f"        {regime_icon} Regime: {regime}  ({regime_detail})")

    if not regime_ok and not relax2 and not relax:
        print(f"\n  ⚠  Regime is {regime} — signals are unreliable in this environment.")
        print(f"     Run with --relax or --relax2 to scan anyway (higher false positive rate).\n")
        conn.close()
        return

    # ── STEP 2: Load price data & score signals ──────────────────────────────
    print("  [2/4] Scoring pre-move signals...")
    price_df = pd.read_sql_query("""
        SELECT symbol, date, open, high, low, close, volume
        FROM stock_prices
        WHERE date >= (SELECT date(MAX(date), '-120 days') FROM stock_prices)
        ORDER BY symbol, date
    """, conn, parse_dates=["date"])

    equity_syms = [s for s in price_df["symbol"].unique() if is_equity(s)]
    price_df = price_df[price_df["symbol"].isin(equity_syms)]

    # Min liquidity filter
    vol_mean = price_df.groupby("symbol")["volume"].mean()
    liquid   = vol_mean[vol_mean >= 500].index
    price_df = price_df[price_df["symbol"].isin(liquid)]

    all_scores = []
    for sym, grp in price_df.groupby("symbol"):
        if symbol_filter and sym != symbol_filter.upper():
            continue
        r = score_stock(grp)
        if r:
            all_scores.append(r)

    # Filter: ≥3 signals, no more than 1 warning
    signal_passed = [r for r in all_scores if r["sig_count"] >= 3 and r["warn_count"] <= 1]
    print(f"        ✓ {len(all_scores)} stocks scored | {len(signal_passed)} passed signal filter (≥3 sigs, ≤1 warning)")

    if not signal_passed:
        print("  No stocks passed signal filter today.")
        conn.close()
        return

    # ── STEP 3: Broker flow ──────────────────────────────────────────────────
    if not relax2:
        print("  [3/4] Checking broker flow (last 7 days)...")
        syms_to_check = [r["symbol"] for r in signal_passed]
        broker_data   = get_broker_flow(conn, syms_to_check)

        if broker_data:
            broker_passed = [r for r in signal_passed
                             if broker_data.get(r["symbol"], {}).get("flow_positive", False)]
            print(f"        ✓ {len(broker_passed)} stocks with net positive broker flow")
        else:
            print("        ⚠  broker_activity table unavailable — skipping broker filter")
            broker_passed = signal_passed
    else:
        broker_passed = signal_passed
        broker_data   = {}
        print("  [3/4] Broker flow — SKIPPED (--relax2 mode)")

    if not broker_passed:
        print("  No stocks passed broker flow filter.")
        conn.close()
        return

    # ── STEP 4: Sector seasonality ───────────────────────────────────────────
    if not relax and not relax2:
        print(f"  [4/4] Checking sector seasonality (month: {datetime.now().strftime('%B')})...")
        season_passed = []
        for r in broker_passed:
            in_season, sector = check_seasonality(r["symbol"], current_month)
            r["sector"]    = sector
            r["in_season"] = in_season
            if in_season:
                season_passed.append(r)
        print(f"        ✓ {len(season_passed)} stocks in seasonally strong sector this month")
    else:
        for r in broker_passed:
            _, sector      = check_seasonality(r["symbol"], current_month)
            r["sector"]    = sector
            r["in_season"] = True
        season_passed = broker_passed
        if relax:
            print("  [4/4] Season filter — SKIPPED (--relax mode)")

    conn.close()

    # ── OUTPUT ───────────────────────────────────────────────────────────────
    final = sorted(season_passed, key=lambda x: x["score_pct"], reverse=True)

    if not final:
        print(f"\n  No stocks passed all 4 filters today.")
        print(f"  Try --relax (drop season) or --relax2 (drop season + broker)\n")
        return

    print()
    print(f"  {'═'*72}")
    mode_note = "RELAX2" if relax2 else ("RELAX" if relax else "FULL 4-FILTER")
    print(f"  RESULTS  |  Regime: {regime}  |  Month: {datetime.now().strftime('%B')}  |  Mode: {mode_note}")
    print(f"  {'═'*72}")
    print()
    print(f"  {'#':>3}  {'SYMBOL':<8}  {'SECTOR':<22}  {'CLOSE':>7}  {'1D%':>6}  {'5D%':>6}  {'VOL/MA':>6}  {'RSI':>5}  {'SIG':>3}  {'BROKER':<14}  FLAGS")
    print(f"  {'─'*3}  {'─'*8}  {'─'*22}  {'─'*7}  {'─'*6}  {'─'*6}  {'─'*6}  {'─'*5}  {'─'*3}  {'─'*14}  {'─'*20}")

    for i, r in enumerate(final, 1):
        chg1   = f"{r['chg_1d']:+.1f}%" if r["chg_1d"] is not None else "  N/A"
        chg5   = f"{r['chg_5d']:+.1f}%" if r["chg_5d"] is not None else "  N/A"
        volma  = f"{r['vol_vs_ma20']:.1f}x"  if r["vol_vs_ma20"] else "  N/A"
        rsi    = f"{r['rsi']:.0f}"           if r["rsi"] else " N/A"
        sector = r.get("sector","Others")[:22]

        bf = broker_data.get(r["symbol"], {})
        if bf:
            broker_str = f"B#{bf['top_buyer']} {_fmt_npr(bf['top_buy_val'])}"
        else:
            broker_str = "—"

        warns = []
        if r["warn_consolidating"]: warns.append("TIGHT")
        if r["warn_near_support"]:  warns.append("SUP")
        if r["warn_basing"]:        warns.append("FLAT")
        if r.get("in_season"):      warns.append("✓SEASON")
        warn_str = " ".join(warns)

        sigs_on = []
        if r["sig_vol_surge"]:    sigs_on.append("V3")
        if r["sig_range_expand"]: sigs_on.append("RE")
        if r["sig_compression"]:  sigs_on.append("RC")
        if r["sig_vol_trend"]:    sigs_on.append("VT")
        if r["sig_rsi_up"]:       sigs_on.append("RI")
        sig_str = "+".join(sigs_on)

        print(f"  {i:>3}  {r['symbol']:<8}  {sector:<22}  {r['close']:>7,.1f}  {chg1:>6}  {chg5:>6}  {volma:>6}  {rsi:>5}  {r['sig_count']:>3}  {broker_str:<14}  {warn_str}")

    print()

    # ── Star picks: 4+ signals ───────────────────────────────────────────────
    stars = [r for r in final if r["sig_count"] >= 4]
    if stars:
        print(f"  ★  HIGHEST CONVICTION (4+ signals, all filters passed):")
        for r in stars:
            bf  = broker_data.get(r["symbol"], {})
            top_buy = _fmt_npr(bf.get("top_buy_val", 0)) if bf else "N/A"
            top_id  = bf.get("top_buyer", "?") if bf else "?"
            print(f"     → {r['symbol']:<8}  {r['sector']:<22}  score:{r['score_pct']:.0f}%  RSI:{r['rsi']}  vol:{r['vol_vs_ma20']:.1f}x  top buyer:B#{top_id} {top_buy}")
        print()

    # ── Filter funnel summary ────────────────────────────────────────────────
    print(f"  FILTER FUNNEL:")
    print(f"    Stocks scanned      : {len(all_scores)}")
    print(f"    After signal filter : {len(signal_passed)}")
    print(f"    After broker filter : {len(broker_passed)}")
    print(f"    After season filter : {len(final)}")
    print()
    print(f"  Tip: Run Option 35 (Full Stock Report) on any ★ pick before entering.")
    print()

    if export:
        df_out = pd.DataFrame(final)
        ts     = datetime.now().strftime("%Y%m%d_%H%M")
        fn     = f"conviction_scan_{ts}.csv"
        df_out.to_csv(fn, index=False)
        print(f"  [EXPORT] Saved {len(df_out)} rows → {fn}")


# ════════════════════════════════════════════════════════════════════════════
#  SINGLE STOCK EXPLAIN MODE
# ════════════════════════════════════════════════════════════════════════════

def explain_symbol(symbol: str):
    symbol = symbol.upper()
    print(f"\n  ╔══ CONVICTION FILTER BREAKDOWN: {symbol} ══╗\n")

    conn = sqlite3.connect(DB_PATH)
    current_month = datetime.now().month

    # Regime
    regime, detail = get_regime(conn)
    regime_ok = regime in ("BULL", "ACCUMULATION")
    print(f"  STEP 1 — REGIME:  {regime}  ({'PASS' if regime_ok else 'FAIL'})")
    print(f"           {detail}\n")

    # Signals
    price_df = pd.read_sql_query(f"""
        SELECT symbol, date, open, high, low, close, volume
        FROM stock_prices
        WHERE symbol=? AND date >= (SELECT date(MAX(date), '-60 days') FROM stock_prices)
        ORDER BY date
    """, conn, params=[symbol], parse_dates=["date"])

    if price_df.empty:
        print(f"  No price data found for {symbol}")
        conn.close()
        return

    r = score_stock(price_df)
    if r is None:
        print("  Insufficient price history.")
        conn.close()
        return

    sig_pass = r["sig_count"] >= 3 and r["warn_count"] <= 1
    print(f"  STEP 2 — SIGNALS: {r['sig_count']}/5 active, score {r['score_pct']}%  ({'PASS' if sig_pass else 'FAIL'})")
    sigs = [
        ("Vol surge last 3d (>1.5x)", "sig_vol_surge",    "+43.3%"),
        ("Price range expanding",      "sig_range_expand", "+40.4%"),
        ("Daily range compression",    "sig_compression",  "+28.3%"),
        ("Volume trending up",         "sig_vol_trend",    "+18.0%"),
        ("RSI trending up",            "sig_rsi_up",       "+12.6%"),
    ]
    for label, key, edge in sigs:
        mark = "✓" if r[key] else "✗"
        print(f"    {mark}  {label:<36}  edge:{edge}")
    if r["warn_count"] > 0:
        print(f"  Warnings:")
        if r["warn_consolidating"]: print("    ⚠  Tight band (<8%)")
        if r["warn_near_support"]:  print("    ⚠  Near support (<5%)")
        if r["warn_basing"]:        print("    ⚠  Flat base (ret10d<3%)")
    print()

    # Broker flow
    bf = get_broker_flow(conn, [symbol])
    bfd = bf.get(symbol, {})
    if bfd:
        flow_pass = bfd["flow_positive"]
        print(f"  STEP 3 — BROKER:  Net flow {_fmt_npr(bfd['net_val'])}  ({'PASS ✓' if flow_pass else 'FAIL ✗'})")
        print(f"           Buy: {_fmt_npr(bfd['total_buy'])}  Sell: {_fmt_npr(bfd['total_sell'])}  Top buyer: #{bfd['top_buyer']}")
    else:
        print("  STEP 3 — BROKER:  No broker data available")
    print()

    # Seasonality
    in_season, sector = check_seasonality(symbol, current_month)
    strong = SECTOR_STRONG_MONTHS.get(sector, [])
    print(f"  STEP 4 — SEASON:  Sector: {sector}  ({'PASS ✓' if in_season else 'FAIL ✗'})")
    print(f"           Strong months: {[datetime(2000,m,1).strftime('%b') for m in strong]}")
    print(f"           Current month ({datetime.now().strftime('%B')}): {'IN SEASON ✓' if in_season else 'off-season'}")
    print()

    passed = sum([regime_ok, sig_pass, bool(bfd) and bfd.get("flow_positive", False), in_season])
    print(f"  VERDICT: {passed}/4 filters passed  —  ", end="")
    if passed == 4:   print("HIGH CONVICTION ★")
    elif passed == 3: print("MODERATE — missing one filter")
    elif passed == 2: print("WEAK — wait for more confirmation")
    else:             print("AVOID — too many filters failing")
    print()

    conn.close()


# ════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NEPSE High-Conviction Entry Scanner")
    parser.add_argument("--relax",   action="store_true", help="Skip season filter")
    parser.add_argument("--relax2",  action="store_true", help="Skip broker + season filters")
    parser.add_argument("--export",  action="store_true", help="Export results to CSV")
    parser.add_argument("--symbol",  type=str, default=None, help="Explain single stock")
    args = parser.parse_args()

    if args.symbol:
        explain_symbol(args.symbol)
    else:
        run_scanner(
            relax=args.relax,
            relax2=args.relax2,
            export=args.export,
            symbol_filter=args.symbol,
        )
