"""
backtest.py — NEPSE Signal Backtester
Tests how well each scanner signal type would have performed historically
using actual stock_prices data (2021-2026)

Usage:
  python backtest.py              # full backtest all signals
  python backtest.py --quick      # QUICK_PICK only
  python backtest.py --smart      # SMART_PICK only
  python backtest.py --momentum   # MOMENTUM_HUNTER only
  python backtest.py --sector     # breakdown by sector
  python backtest.py --phase      # breakdown by market phase
  python backtest.py --top        # show top performing stocks
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

DB = 'nepse_market_data.db'

# ── Signal configs (same as signal_tracker.py) ────────────────────────────────
SIGNAL_CONFIG = {
    'QUICK_PICK':      {'target': 7.0,  'stop': 4.0,  'hold': 5},
    'SMART_PICK':      {'target': 10.0, 'stop': 5.0,  'hold': 10},
    'MOMENTUM_HUNTER': {'target': 12.0, 'stop': 6.0,  'hold': 14},
    'DEPLOY_READY':    {'target': 20.0, 'stop': 8.0,  'hold': 30},
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_conn():
    return sqlite3.connect(DB)

def _pct(a, b):
    if not b or b == 0:
        return None
    return round((a - b) / b * 100, 2)

def _pad(s, n):
    s = str(s)
    return s[:n].ljust(n)

def _bar(pct, width=20):
    """Simple ASCII bar chart."""
    if pct is None:
        return ' ' * width
    filled = int(min(abs(pct) / 100 * width, width))
    if pct >= 0:
        return ('█' * filled).ljust(width)
    else:
        return ('░' * filled).ljust(width)

# ── Load all prices into memory (fast lookup) ─────────────────────────────────
def load_prices(conn):
    """Returns dict: {symbol: [(date, open, high, low, close, volume), ...]} sorted by date"""
    print("  Loading price data...")
    rows = conn.execute(
        "SELECT symbol, date, open, high, low, close, volume FROM stock_prices ORDER BY symbol, date"
    ).fetchall()
    prices = defaultdict(list)
    for r in rows:
        prices[r[0]].append(r[1:])  # (date, open, high, low, close, volume)
    print(f"  Loaded {len(rows):,} rows for {len(prices)} symbols")
    return dict(prices)

def load_sectors(conn):
    """Returns dict: {symbol: sector}"""
    rows = conn.execute("SELECT symbol, sector FROM companies").fetchall()
    return {r[0]: r[1] for r in rows}

def load_nepse_index(prices):
    """Get NEPSE index prices as {date: close}"""
    if 'NEPSE' in prices:
        return {r[0]: r[4] for r in prices['NEPSE']}
    return {}

# ── Price lookup helpers ──────────────────────────────────────────────────────
def get_price_index(prices, symbol):
    """Build date->index map for fast lookup."""
    if symbol not in prices:
        return {}, []
    data = prices[symbol]
    idx = {r[0]: i for i, r in enumerate(data)}
    return idx, data

def get_future_price(data, idx_map, from_date, n_days):
    """Get close price N trading days after from_date."""
    if from_date not in idx_map:
        return None
    start_idx = idx_map[from_date]
    target_idx = start_idx + n_days
    if target_idx >= len(data):
        return None
    return data[target_idx][4]  # close

def get_max_price(data, idx_map, from_date, n_days):
    """Get max high price within N trading days after from_date."""
    if from_date not in idx_map:
        return None
    start_idx = idx_map[from_date] + 1
    end_idx = min(start_idx + n_days, len(data))
    if start_idx >= len(data):
        return None
    highs = [data[i][2] for i in range(start_idx, end_idx)]  # high
    return max(highs) if highs else None

def get_min_price(data, idx_map, from_date, n_days):
    """Get min low price within N trading days after from_date."""
    if from_date not in idx_map:
        return None
    start_idx = idx_map[from_date] + 1
    end_idx = min(start_idx + n_days, len(data))
    if start_idx >= len(data):
        return None
    lows = [data[i][1] for i in range(start_idx, end_idx)]  # low
    return min(lows) if lows else None

# ── Market phase detection ────────────────────────────────────────────────────
def detect_phase(nepse_idx, date_str):
    """Simple phase detection using NEPSE 50d vs 200d MA."""
    dates = sorted(nepse_idx.keys())
    if date_str not in nepse_idx:
        return 'UNKNOWN'
    pos = dates.index(date_str)
    if pos < 200:
        return 'UNKNOWN'
    prices_50  = [nepse_idx[dates[i]] for i in range(pos-50, pos)]
    prices_200 = [nepse_idx[dates[i]] for i in range(pos-200, pos)]
    ma50  = sum(prices_50) / 50
    ma200 = sum(prices_200) / 200
    current = nepse_idx[date_str]
    if current > ma50 > ma200:
        return 'BULL'
    elif current < ma50 < ma200:
        return 'BEAR'
    else:
        return 'SIDEWAYS'

# ── QUICK_PICK signal simulation ──────────────────────────────────────────────
def simulate_quick_pick(prices, min_volume=10000, top_n=10):
    """
    Simulate QUICK_PICK: on each trading day, find stocks with:
    - Close > 20d MA (momentum)
    - Volume spike > 1.5x 10d avg volume
    - Close near 52w high (within 20%)
    Returns list of (date, symbol, entry_price) signals
    """
    print("\n  Simulating QUICK_PICK signals...")
    signals = []
    all_dates = set()
    for sym, data in prices.items():
        for r in data:
            all_dates.add(r[0])
    all_dates = sorted(all_dates)

    for symbol, data in prices.items():
        if symbol == 'NEPSE':
            continue
        idx_map = {r[0]: i for i, r in enumerate(data)}

        for i, row in enumerate(data):
            date_str, open_, high, low, close, volume = row
            if i < 252:  # need 52w history
                continue
            if not volume or volume < min_volume:
                continue

            # 20d MA
            ma20 = sum(data[j][4] for j in range(i-20, i)) / 20
            # 10d avg volume
            avg_vol = sum(data[j][5] for j in range(i-10, i) if data[j][5]) / 10
            # 52w high
            high_52w = max(data[j][2] for j in range(i-252, i))

            # Signal conditions
            if (close > ma20 and
                avg_vol > 0 and volume > avg_vol * 1.5 and
                close >= high_52w * 0.80):
                signals.append((date_str, symbol, close))

    print(f"  Generated {len(signals):,} QUICK_PICK signals")
    return signals

# ── SMART_PICK signal simulation ──────────────────────────────────────────────
def simulate_smart_pick(prices, min_volume=10000, top_n=10):
    """
    Simulate SMART_PICK: QUICK_PICK conditions + stronger momentum
    - RSI-like: close > 10d ago close by 5%+
    - Higher volume requirement
    - Closer to 52w high (within 10%)
    """
    print("\n  Simulating SMART_PICK signals...")
    signals = []

    for symbol, data in prices.items():
        if symbol == 'NEPSE':
            continue
        for i, row in enumerate(data):
            date_str, open_, high, low, close, volume = row
            if i < 252:
                continue
            if not volume or volume < min_volume * 1.5:
                continue

            ma20    = sum(data[j][4] for j in range(i-20, i)) / 20
            avg_vol = sum(data[j][5] for j in range(i-10, i) if data[j][5]) / 10
            high_52w = max(data[j][2] for j in range(i-252, i))
            close_10d_ago = data[i-10][4]

            momentum_pct = _pct(close, close_10d_ago) or 0

            if (close > ma20 and
                avg_vol > 0 and volume > avg_vol * 2.0 and
                close >= high_52w * 0.90 and
                momentum_pct >= 5.0):
                signals.append((date_str, symbol, close))

    print(f"  Generated {len(signals):,} SMART_PICK signals")
    return signals

# ── MOMENTUM_HUNTER simulation (simplified — no broker data pre-May 2026) ─────
def simulate_momentum_hunter(prices, min_volume=10000):
    """
    Simulate MOMENTUM_HUNTER without broker data:
    - 5+ consecutive up days
    - Each day volume above average
    - Price trending up consistently
    Note: Real signal uses broker data. This is price-only proxy.
    """
    print("\n  Simulating MOMENTUM_HUNTER signals (price-proxy, no broker history)...")
    signals = []

    for symbol, data in prices.items():
        if symbol == 'NEPSE':
            continue
        for i, row in enumerate(data):
            date_str, open_, high, low, close, volume = row
            if i < 20:
                continue
            if not volume or volume < min_volume:
                continue

            # Check 5 consecutive up days
            consec_up = 0
            for j in range(i-1, max(i-6, -1), -1):
                if data[j][4] > data[j-1][4]:  # close > prev close
                    consec_up += 1
                else:
                    break

            avg_vol = sum(data[j][5] for j in range(i-10, i) if data[j][5]) / 10

            if consec_up >= 4 and avg_vol > 0 and volume > avg_vol * 1.3:
                signals.append((date_str, symbol, close))

    print(f"  Generated {len(signals):,} MOMENTUM_HUNTER signals")
    return signals

# ── DEPLOY_READY simulation ───────────────────────────────────────────────────
def simulate_deploy_ready(prices, nepse_idx, min_volume=5000):
    """
    Simulate DEPLOY_READY signals using:
    - Seasonal filter: only signal in months before historically good months
      (July is best → signal in June; Jan is good → signal in Dec)
    - Stock near 52w low (beaten down, ready to recover)
    - Volume starting to pick up (accumulation)
    - NEPSE index in non-BEAR phase (or just turning)
    - Hold 30 trading days, target +20%

    Good entry months (month before a strong month):
      June  → July  is best (+0.263%)
      Dec   → Jan   is second (+0.090%)
      Sep   → Oct   near flat but after worst months
    """
    print("\n  Simulating DEPLOY_READY signals (seasonal + price proxy)...")

    # Best signal months based on real NEPSE seasonal data
    SIGNAL_MONTHS = {'06', '12', '09'}  # June, Dec, Sep

    signals = []

    for symbol, data in prices.items():
        if symbol == 'NEPSE':
            continue
        for i, row in enumerate(data):
            date_str, open_, high, low, close, volume = row
            if i < 252:
                continue
            if not volume or volume < min_volume:
                continue

            month = date_str[5:7]
            if month not in SIGNAL_MONTHS:
                continue

            # 52w low and high
            low_52w  = min(data[j][3] for j in range(i-252, i))  # low
            high_52w = max(data[j][2] for j in range(i-252, i))  # high

            # Stock must be beaten down — within 30% of 52w low
            if close > low_52w * 1.30:
                continue

            # Volume picking up — current vol > 20d avg
            avg_vol = sum(data[j][5] for j in range(i-20, i) if data[j][5]) / 20
            if avg_vol <= 0 or volume < avg_vol * 1.1:
                continue

            # Not in extreme bear (NEPSE phase check)
            phase = detect_phase(nepse_idx, date_str)
            if phase == 'BEAR':
                continue

            # R/R check — must have at least 2x upside to 52w high vs downside to 52w low
            upside   = (high_52w - close) / close * 100
            downside = (close - low_52w) / close * 100
            if downside <= 0 or upside / max(downside, 0.1) < 1.5:
                continue

            signals.append((date_str, symbol, close))

    print(f"  Generated {len(signals):,} DEPLOY_READY signals")
    return signals

# ── Evaluate signals ──────────────────────────────────────────────────────────
def evaluate_signals(signals, prices, signal_type, sectors=None, nepse_idx=None):
    """
    For each signal, check outcome at hold period end.
    Returns list of result dicts.
    """
    cfg    = SIGNAL_CONFIG[signal_type]
    target = cfg['target']
    stop   = cfg['stop']
    hold   = cfg['hold']

    results = []
    symbol_cache = {}

    for date_str, symbol, entry in signals:
        if symbol not in symbol_cache:
            idx_map = {r[0]: i for i, r in enumerate(prices[symbol])}
            symbol_cache[symbol] = (idx_map, prices[symbol])
        idx_map, data = symbol_cache[symbol]

        exit_price = get_future_price(data, idx_map, date_str, hold)
        if exit_price is None:
            continue

        max_price = get_max_price(data, idx_map, date_str, hold)
        min_price = get_min_price(data, idx_map, date_str, hold)

        pct       = _pct(exit_price, entry)
        max_pct   = _pct(max_price, entry) if max_price else None
        min_pct   = _pct(min_price, entry) if min_price else None

        hit_target = max_pct is not None and max_pct >= target
        hit_stop   = min_pct is not None and min_pct <= -stop

        # Outcome
        if hit_target and hit_stop:
            # Both hit — which came first? Approximate: if exit positive, target first
            outcome = 'WIN' if (pct or 0) >= 0 else 'STOP'
        elif hit_target:
            outcome = 'WIN'
        elif hit_stop:
            outcome = 'STOP'
        elif (pct or 0) > 0:
            outcome = 'PROFIT'  # positive but under target
        else:
            outcome = 'LOSS'

        # NEPSE index return over same period
        nepse_ret = None
        if nepse_idx:
            nepse_dates = sorted(nepse_idx.keys())
            if date_str in nepse_idx:
                pos = nepse_dates.index(date_str)
                end_pos = min(pos + hold, len(nepse_dates) - 1)
                nepse_ret = _pct(nepse_idx[nepse_dates[end_pos]], nepse_idx[date_str])

        # Market phase
        phase = detect_phase(nepse_idx, date_str) if nepse_idx else 'UNKNOWN'

        results.append({
            'date':      date_str,
            'symbol':    symbol,
            'sector':    sectors.get(symbol, 'Unknown') if sectors else 'Unknown',
            'entry':     entry,
            'exit':      exit_price,
            'pct':       pct,
            'max_pct':   max_pct,
            'min_pct':   min_pct,
            'outcome':   outcome,
            'nepse_ret': nepse_ret,
            'phase':     phase,
            'signal':    signal_type,
        })

    return results

# ── Report ────────────────────────────────────────────────────────────────────
def print_summary(results, signal_type):
    cfg    = SIGNAL_CONFIG[signal_type]
    target = cfg['target']
    stop   = cfg['stop']
    hold   = cfg['hold']

    if not results:
        print(f"  No results for {signal_type}")
        return

    total   = len(results)
    wins    = sum(1 for r in results if r['outcome'] == 'WIN')
    stops   = sum(1 for r in results if r['outcome'] == 'STOP')
    profits = sum(1 for r in results if r['outcome'] == 'PROFIT')
    losses  = sum(1 for r in results if r['outcome'] == 'LOSS')

    win_rate   = wins / total * 100
    avg_ret    = sum(r['pct'] for r in results if r['pct'] is not None) / total
    avg_win    = sum(r['pct'] for r in results if r['outcome'] in ('WIN','PROFIT') and r['pct']) / max(wins+profits, 1)
    avg_loss   = sum(r['pct'] for r in results if r['outcome'] in ('STOP','LOSS') and r['pct']) / max(stops+losses, 1)
    expectancy = (win_rate/100 * avg_win) + ((1-win_rate/100) * avg_loss)

    # vs NEPSE
    nepse_rets = [r['nepse_ret'] for r in results if r['nepse_ret'] is not None]
    avg_nepse  = sum(nepse_rets) / len(nepse_rets) if nepse_rets else None
    alpha      = avg_ret - avg_nepse if avg_nepse is not None else None

    print(f"\n  {'='*60}")
    print(f"  {signal_type}  —  target +{target}%  stop -{stop}%  hold {hold}d")
    print(f"  {'='*60}")
    print(f"  Total signals tested : {total:,}")
    print(f"  WIN  (hit +{target}%)    : {wins:,}  ({win_rate:.1f}%)")
    print(f"  PROFIT (positive<target): {profits:,}  ({profits/total*100:.1f}%)")
    print(f"  STOP (hit -{stop}%)    : {stops:,}  ({stops/total*100:.1f}%)")
    print(f"  LOSS (negative<stop)  : {losses:,}  ({losses/total*100:.1f}%)")
    print(f"  ---")
    print(f"  Avg return           : {avg_ret:+.2f}%")
    print(f"  Avg win              : {avg_win:+.2f}%")
    print(f"  Avg loss             : {avg_loss:+.2f}%")
    print(f"  Expectancy per trade : {expectancy:+.2f}%")
    if avg_nepse is not None:
        print(f"  Avg NEPSE return     : {avg_nepse:+.2f}%")
        print(f"  Alpha vs NEPSE       : {alpha:+.2f}%")
    verdict = "PROFITABLE" if expectancy > 0 else "UNPROFITABLE"
    edge    = "BEATS MARKET" if (alpha or 0) > 0 else "LAGS MARKET"
    print(f"  Verdict              : {verdict} | {edge}")

def print_sector_breakdown(results, signal_type):
    cfg    = SIGNAL_CONFIG[signal_type]
    target = cfg['target']

    by_sector = defaultdict(list)
    for r in results:
        by_sector[r['sector']].append(r)

    print(f"\n  SECTOR BREAKDOWN — {signal_type}")
    print(f"  {'Sector':<30} {'Signals':>8} {'Win%':>6} {'AvgRet':>8} {'Expectancy':>11}")
    print("  " + "-" * 65)

    sector_stats = []
    for sector, rows in by_sector.items():
        total  = len(rows)
        if total < 5:
            continue
        wins   = sum(1 for r in rows if r['outcome'] == 'WIN')
        wr     = wins / total * 100
        avg_r  = sum(r['pct'] for r in rows if r['pct']) / total
        avg_w  = sum(r['pct'] for r in rows if r['outcome'] in ('WIN','PROFIT') and r['pct']) / max(1, sum(1 for r in rows if r['outcome'] in ('WIN','PROFIT')))
        avg_l  = sum(r['pct'] for r in rows if r['outcome'] in ('STOP','LOSS') and r['pct']) / max(1, sum(1 for r in rows if r['outcome'] in ('STOP','LOSS')))
        exp    = (wr/100 * avg_w) + ((1-wr/100) * avg_l)
        sector_stats.append((sector, total, wr, avg_r, exp))

    for s in sorted(sector_stats, key=lambda x: -x[4]):
        sector, total, wr, avg_r, exp = s
        marker = ' *' if exp > 1 else ''
        print(f"  {_pad(sector,30)} {total:>8} {wr:>5.1f}% {avg_r:>+7.2f}% {exp:>+10.2f}%{marker}")

def print_phase_breakdown(results, signal_type):
    by_phase = defaultdict(list)
    for r in results:
        by_phase[r['phase']].append(r)

    print(f"\n  MARKET PHASE BREAKDOWN — {signal_type}")
    print(f"  {'Phase':<12} {'Signals':>8} {'Win%':>6} {'AvgRet':>8} {'Verdict':>10}")
    print("  " + "-" * 46)

    for phase in ['BULL', 'SIDEWAYS', 'BEAR', 'UNKNOWN']:
        rows = by_phase.get(phase, [])
        if not rows:
            continue
        total = len(rows)
        wins  = sum(1 for r in rows if r['outcome'] == 'WIN')
        wr    = wins / total * 100
        avg_r = sum(r['pct'] for r in rows if r['pct']) / total
        verdict = 'GOOD' if avg_r > 0 else 'POOR'
        print(f"  {_pad(phase,12)} {total:>8} {wr:>5.1f}% {avg_r:>+7.2f}% {verdict:>10}")

def print_top_stocks(results, signal_type, n=15):
    by_sym = defaultdict(list)
    for r in results:
        by_sym[r['symbol']].append(r)

    stats = []
    for sym, rows in by_sym.items():
        total = len(rows)
        if total < 3:
            continue
        wins  = sum(1 for r in rows if r['outcome'] == 'WIN')
        avg_r = sum(r['pct'] for r in rows if r['pct']) / total
        stats.append((sym, total, wins/total*100, avg_r))

    print(f"\n  TOP PERFORMING STOCKS — {signal_type} (min 3 signals)")
    print(f"  {'Symbol':<12} {'Signals':>8} {'Win%':>6} {'AvgRet':>8}")
    print("  " + "-" * 36)
    for sym, total, wr, avg_r in sorted(stats, key=lambda x: -x[3])[:n]:
        print(f"  {_pad(sym,12)} {total:>8} {wr:>5.1f}% {avg_r:>+7.2f}%")

def print_yearly_breakdown(results, signal_type):
    by_year = defaultdict(list)
    for r in results:
        year = r['date'][:4]
        by_year[year].append(r)

    print(f"\n  YEARLY BREAKDOWN — {signal_type}")
    print(f"  {'Year':<8} {'Signals':>8} {'Win%':>6} {'AvgRet':>8} {'Phase':>10}")
    print("  " + "-" * 42)

    for year in sorted(by_year.keys()):
        rows  = by_year[year]
        total = len(rows)
        wins  = sum(1 for r in rows if r['outcome'] == 'WIN')
        avg_r = sum(r['pct'] for r in rows if r['pct']) / total
        phases = [r['phase'] for r in rows]
        dominant = max(set(phases), key=phases.count)
        print(f"  {year:<8} {total:>8} {wins/total*100:>5.1f}% {avg_r:>+7.2f}% {dominant:>10}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]
    do_quick    = '--quick'    in args or not args
    do_smart    = '--smart'    in args or not args
    do_momentum = '--momentum' in args or not args
    do_deploy   = '--deploy'   in args or not args
    do_sector   = '--sector'   in args or not args
    do_phase    = '--phase'    in args or not args
    do_top      = '--top'      in args or not args

    print()
    print("=" * 60)
    print("  NEPSE SIGNAL BACKTESTER")
    print(f"  Using data: 2021-05-24 to 2026-06-05")
    print("=" * 60)
    print("  NOTE: MOMENTUM_HUNTER uses price-proxy (no broker history)")
    print("  NOTE: Results are simulated — real signals may differ")
    print()

    conn    = get_conn()
    prices  = load_prices(conn)
    sectors = load_sectors(conn)
    nepse_idx = load_nepse_index(prices)
    conn.close()

    all_results = {}

    if do_quick:
        sigs = simulate_quick_pick(prices)
        results = evaluate_signals(sigs, prices, 'QUICK_PICK', sectors, nepse_idx)
        all_results['QUICK_PICK'] = results
        print_summary(results, 'QUICK_PICK')
        if do_yearly := True:
            print_yearly_breakdown(results, 'QUICK_PICK')
        if do_sector:
            print_sector_breakdown(results, 'QUICK_PICK')
        if do_phase:
            print_phase_breakdown(results, 'QUICK_PICK')
        if do_top:
            print_top_stocks(results, 'QUICK_PICK')

    if do_smart:
        sigs = simulate_smart_pick(prices)
        results = evaluate_signals(sigs, prices, 'SMART_PICK', sectors, nepse_idx)
        all_results['SMART_PICK'] = results
        print_summary(results, 'SMART_PICK')
        if do_yearly := True:
            print_yearly_breakdown(results, 'SMART_PICK')
        if do_sector:
            print_sector_breakdown(results, 'SMART_PICK')
        if do_phase:
            print_phase_breakdown(results, 'SMART_PICK')
        if do_top:
            print_top_stocks(results, 'SMART_PICK')

    if do_momentum:
        sigs = simulate_momentum_hunter(prices)
        results = evaluate_signals(sigs, prices, 'MOMENTUM_HUNTER', sectors, nepse_idx)
        all_results['MOMENTUM_HUNTER'] = results
        print_summary(results, 'MOMENTUM_HUNTER')
        if do_yearly := True:
            print_yearly_breakdown(results, 'MOMENTUM_HUNTER')
        if do_sector:
            print_sector_breakdown(results, 'MOMENTUM_HUNTER')
        if do_phase:
            print_phase_breakdown(results, 'MOMENTUM_HUNTER')
        if do_top:
            print_top_stocks(results, 'MOMENTUM_HUNTER')

    if do_deploy:
        sigs = simulate_deploy_ready(prices, nepse_idx)
        results = evaluate_signals(sigs, prices, 'DEPLOY_READY', sectors, nepse_idx)
        all_results['DEPLOY_READY'] = results
        print_summary(results, 'DEPLOY_READY')
        if do_yearly := True:
            print_yearly_breakdown(results, 'DEPLOY_READY')
        if do_sector:
            print_sector_breakdown(results, 'DEPLOY_READY')
        if do_phase:
            print_phase_breakdown(results, 'DEPLOY_READY')
        if do_top:
            print_top_stocks(results, 'DEPLOY_READY')

    # ── Cross-signal comparison ───────────────────────────────────────────────
    if len(all_results) > 1:
        print(f"\n  {'='*60}")
        print(f"  CROSS-SIGNAL COMPARISON")
        print(f"  {'='*60}")
        print(f"  {'Signal':<20} {'Signals':>8} {'Win%':>6} {'AvgRet':>8} {'Expectancy':>11} {'Alpha':>8}")
        print("  " + "-" * 63)
        for sig, results in all_results.items():
            cfg    = SIGNAL_CONFIG[sig]
            target = cfg['target']
            total  = len(results)
            if total == 0:
                continue
            wins   = sum(1 for r in results if r['outcome'] == 'WIN')
            wr     = wins / total * 100
            avg_r  = sum(r['pct'] for r in results if r['pct']) / total
            avg_w  = sum(r['pct'] for r in results if r['outcome'] in ('WIN','PROFIT') and r['pct']) / max(1, sum(1 for r in results if r['outcome'] in ('WIN','PROFIT')))
            avg_l  = sum(r['pct'] for r in results if r['outcome'] in ('STOP','LOSS') and r['pct']) / max(1, sum(1 for r in results if r['outcome'] in ('STOP','LOSS')))
            exp    = (wr/100 * avg_w) + ((1-wr/100) * avg_l)
            nepse_rets = [r['nepse_ret'] for r in results if r['nepse_ret'] is not None]
            alpha  = avg_r - (sum(nepse_rets)/len(nepse_rets)) if nepse_rets else None
            alpha_str = f"{alpha:+.2f}%" if alpha is not None else "  n/a"
            print(f"  {_pad(sig,20)} {total:>8} {wr:>5.1f}% {avg_r:>+7.2f}% {exp:>+10.2f}% {alpha_str:>8}")

        print()
        best = max(all_results.items(), key=lambda x: sum(r['pct'] for r in x[1] if r['pct']) / max(len(x[1]),1))
        print(f"  >> Best performing signal: {best[0]}")
        print()

if __name__ == '__main__':
    main()
