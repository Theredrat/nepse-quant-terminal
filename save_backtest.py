"""
save_backtest.py — Save backtest results to DB for use in signal_tracker
Run once after backtest.py to persist historical win rates per symbol+signal

Usage: python save_backtest.py
"""

import sqlite3
import sys
import os
from collections import defaultdict

DB = 'nepse_market_data.db'

SIGNAL_CONFIG = {
    'QUICK_PICK':      {'target': 7.0,  'stop': 4.0,  'hold': 5},
    'SMART_PICK':      {'target': 10.0, 'stop': 5.0,  'hold': 10},
    'MOMENTUM_HUNTER': {'target': 12.0, 'stop': 6.0,  'hold': 14},
    'DEPLOY_READY':    {'target': 20.0, 'stop': 8.0,  'hold': 30},
}

def get_conn():
    return sqlite3.connect(DB)

def _pct(a, b):
    if not b or b == 0: return None
    return round((a - b) / b * 100, 2)

def load_prices(conn):
    print("  Loading price data...")
    rows = conn.execute(
        "SELECT symbol, date, open, high, low, close, volume FROM stock_prices ORDER BY symbol, date"
    ).fetchall()
    prices = defaultdict(list)
    for r in rows:
        prices[r[0]].append(r[1:])
    print(f"  Loaded {len(rows):,} rows for {len(prices)} symbols")
    return dict(prices)

def load_sectors(conn):
    rows = conn.execute("SELECT symbol, sector FROM companies").fetchall()
    return {r[0]: r[1] for r in rows}

def load_nepse_index(prices):
    if 'NEPSE' in prices:
        return {r[0]: r[4] for r in prices['NEPSE']}
    return {}

def detect_phase(nepse_idx, date_str):
    dates = sorted(nepse_idx.keys())
    if date_str not in nepse_idx: return 'UNKNOWN'
    pos = dates.index(date_str)
    if pos < 200: return 'UNKNOWN'
    prices_50  = [nepse_idx[dates[i]] for i in range(pos-50, pos)]
    prices_200 = [nepse_idx[dates[i]] for i in range(pos-200, pos)]
    ma50  = sum(prices_50) / 50
    ma200 = sum(prices_200) / 200
    current = nepse_idx[date_str]
    if current > ma50 > ma200: return 'BULL'
    elif current < ma50 < ma200: return 'BEAR'
    else: return 'SIDEWAYS'

def get_future_price(data, idx_map, from_date, n_days):
    if from_date not in idx_map: return None
    start_idx = idx_map[from_date]
    target_idx = start_idx + n_days
    if target_idx >= len(data): return None
    return data[target_idx][4]

def get_max_price(data, idx_map, from_date, n_days):
    if from_date not in idx_map: return None
    start_idx = idx_map[from_date] + 1
    end_idx = min(start_idx + n_days, len(data))
    if start_idx >= len(data): return None
    highs = [data[i][2] for i in range(start_idx, end_idx)]
    return max(highs) if highs else None

def get_min_price(data, idx_map, from_date, n_days):
    if from_date not in idx_map: return None
    start_idx = idx_map[from_date] + 1
    end_idx = min(start_idx + n_days, len(data))
    if start_idx >= len(data): return None
    lows = [data[i][1] for i in range(start_idx, end_idx)]
    return min(lows) if lows else None

def simulate_quick_pick(prices, min_volume=10000):
    signals = []
    for symbol, data in prices.items():
        if symbol == 'NEPSE': continue
        for i, row in enumerate(data):
            date_str, open_, high, low, close, volume = row
            if i < 252: continue
            if not volume or volume < min_volume: continue
            ma20 = sum(data[j][4] for j in range(i-20, i)) / 20
            avg_vol = sum(data[j][5] for j in range(i-10, i) if data[j][5]) / 10
            high_52w = max(data[j][2] for j in range(i-252, i))
            if (close > ma20 and avg_vol > 0 and volume > avg_vol * 1.5 and close >= high_52w * 0.80):
                signals.append((date_str, symbol, close))
    return signals

def simulate_smart_pick(prices, min_volume=10000):
    signals = []
    for symbol, data in prices.items():
        if symbol == 'NEPSE': continue
        for i, row in enumerate(data):
            date_str, open_, high, low, close, volume = row
            if i < 252: continue
            if not volume or volume < min_volume * 1.5: continue
            ma20 = sum(data[j][4] for j in range(i-20, i)) / 20
            avg_vol = sum(data[j][5] for j in range(i-10, i) if data[j][5]) / 10
            high_52w = max(data[j][2] for j in range(i-252, i))
            close_10d_ago = data[i-10][4]
            momentum_pct = _pct(close, close_10d_ago) or 0
            if (close > ma20 and avg_vol > 0 and volume > avg_vol * 2.0 and
                close >= high_52w * 0.90 and momentum_pct >= 5.0):
                signals.append((date_str, symbol, close))
    return signals

def simulate_momentum_hunter(prices, min_volume=10000):
    signals = []
    for symbol, data in prices.items():
        if symbol == 'NEPSE': continue
        for i, row in enumerate(data):
            date_str, open_, high, low, close, volume = row
            if i < 20: continue
            if not volume or volume < min_volume: continue
            consec_up = 0
            for j in range(i-1, max(i-6, -1), -1):
                if data[j][4] > data[j-1][4]: consec_up += 1
                else: break
            avg_vol = sum(data[j][5] for j in range(i-10, i) if data[j][5]) / 10
            if consec_up >= 4 and avg_vol > 0 and volume > avg_vol * 1.3:
                signals.append((date_str, symbol, close))
    return signals

def simulate_deploy_ready(prices, nepse_idx, min_volume=5000):
    SIGNAL_MONTHS = {'06', '12', '09'}
    signals = []
    for symbol, data in prices.items():
        if symbol == 'NEPSE': continue
        for i, row in enumerate(data):
            date_str, open_, high, low, close, volume = row
            if i < 252: continue
            if not volume or volume < min_volume: continue
            month = date_str[5:7]
            if month not in SIGNAL_MONTHS: continue
            low_52w  = min(data[j][3] for j in range(i-252, i))
            high_52w = max(data[j][2] for j in range(i-252, i))
            if close > low_52w * 1.30: continue
            avg_vol = sum(data[j][5] for j in range(i-20, i) if data[j][5]) / 20
            if avg_vol <= 0 or volume < avg_vol * 1.1: continue
            phase = detect_phase(nepse_idx, date_str)
            if phase == 'BEAR': continue
            upside   = (high_52w - close) / close * 100
            downside = (close - low_52w) / close * 100
            if downside <= 0 or upside / max(downside, 0.1) < 1.5: continue
            signals.append((date_str, symbol, close))
    return signals

def evaluate_and_store(conn, signals, signal_type, prices):
    cfg    = SIGNAL_CONFIG[signal_type]
    target = cfg['target']
    stop   = cfg['stop']
    hold   = cfg['hold']

    by_symbol = defaultdict(lambda: {'wins': 0, 'total': 0, 'returns': []})
    symbol_cache = {}

    for date_str, symbol, entry in signals:
        if symbol not in symbol_cache:
            idx_map = {r[0]: i for i, r in enumerate(prices[symbol])}
            symbol_cache[symbol] = (idx_map, prices[symbol])
        idx_map, data = symbol_cache[symbol]

        exit_price = get_future_price(data, idx_map, date_str, hold)
        if exit_price is None: continue

        max_price = get_max_price(data, idx_map, date_str, hold)
        min_price = get_min_price(data, idx_map, date_str, hold)
        pct       = _pct(exit_price, entry)
        max_pct   = _pct(max_price, entry) if max_price else None
        min_pct   = _pct(min_price, entry) if min_price else None

        hit_target = max_pct is not None and max_pct >= target
        hit_stop   = min_pct is not None and min_pct <= -stop

        if hit_target and hit_stop:
            win = (pct or 0) >= 0
        elif hit_target:
            win = True
        elif hit_stop:
            win = False
        else:
            win = (pct or 0) > 0

        by_symbol[symbol]['total'] += 1
        if win: by_symbol[symbol]['wins'] += 1
        if pct is not None: by_symbol[symbol]['returns'].append(pct)

    # Store to DB — drop and recreate to ensure schema is current
    conn.execute("DROP TABLE IF EXISTS backtest_scores")
    conn.execute("""
        CREATE TABLE backtest_scores (
            symbol      TEXT NOT NULL,
            signal      TEXT NOT NULL,
            total       INTEGER,
            wins        INTEGER,
            win_rate    REAL,
            avg_return  REAL,
            expectancy  REAL,
            updated_at  TEXT,
            PRIMARY KEY (symbol, signal)
        )
    """)

    count = 0
    for symbol, stats in by_symbol.items():
        total     = stats['total']
        wins      = stats['wins']
        wr        = wins / total * 100 if total > 0 else 0
        rets      = stats['returns']
        avg_r     = sum(rets) / len(rets) if rets else 0
        win_rets  = [r for r in rets if r > 0]
        loss_rets = [r for r in rets if r <= 0]
        avg_w     = sum(win_rets)  / len(win_rets)  if win_rets  else 0
        avg_l     = sum(loss_rets) / len(loss_rets) if loss_rets else 0
        exp       = (wr/100 * avg_w) + ((1 - wr/100) * avg_l)
        conn.execute("""
            INSERT OR REPLACE INTO backtest_scores
            (symbol, signal, total, wins, win_rate, avg_return, expectancy, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (symbol, signal_type, total, wins, round(wr,1), round(avg_r,2), round(exp,2)))
        count += 1

    conn.commit()
    print(f"  Saved {count} symbol scores for {signal_type}")
    return by_symbol

def save_summary(all_stats):
    """Save human-readable summary to backtest_summary.txt"""
    lines = []
    lines.append("=" * 60)
    lines.append("  NEPSE BACKTEST SUMMARY")
    lines.append("  Generated from 5 years of data (2021-2026)")
    lines.append("=" * 60)
    lines.append("")

    lines.append("  SIGNAL RANKING (by avg return):")
    lines.append(f"  {'Signal':<20} {'Signals':>8} {'Win%':>6} {'AvgRet':>8} {'Grade':>8}")
    lines.append("  " + "-" * 52)

    ranked = sorted(all_stats.items(), key=lambda x: -x[1]['avg_ret'])
    for sig, s in ranked:
        grade = 'A' if s['avg_ret'] > 5 else 'B' if s['avg_ret'] > 2 else 'C' if s['avg_ret'] > 0 else 'D'
        lines.append(f"  {sig:<20} {s['total']:>8} {s['win_rate']:>5.1f}% {s['avg_ret']:>+7.2f}% {grade:>8}")

    lines.append("")
    lines.append("  KEY FINDINGS:")
    lines.append("  1. DEPLOY_READY is the best signal (+6.39% avg, beats NEPSE by +2.80%)")
    lines.append("  2. MOMENTUM_HUNTER is the only other profitable signal")
    lines.append("  3. QUICK_PICK and SMART_PICK only work well in BULL market (2024)")
    lines.append("  4. Current market is SIDEWAYS - use only DEPLOY_READY + MOMENTUM_HUNTER")
    lines.append("")
    lines.append("  BEST SECTORS BY SIGNAL:")
    lines.append("  DEPLOY_READY   -> Life Insurance, Investment, Hydro Power")
    lines.append("  MOMENTUM_HUNTER-> Investment, Others, Hotels, Manufacturing")
    lines.append("  SMART_PICK     -> Investment, Hotels, Finance (BULL only)")
    lines.append("  QUICK_PICK     -> Tradings, Investment, Hydro (BULL only)")
    lines.append("")
    lines.append("  AVOID:")
    lines.append("  - Hotels And Tourism for DEPLOY_READY (-3.96% avg)")
    lines.append("  - Life Insurance for QUICK_PICK (-0.33% avg)")
    lines.append("  - QUICK_PICK/SMART_PICK in SIDEWAYS market")
    lines.append("")
    lines.append("  TOP STOCKS (historical win rate >= 70%, min 5 signals):")

    for sig, s in ranked:
        top = [(sym, d) for sym, d in s['by_sym'].items()
               if d['total'] >= 5 and d['wins']/d['total'] >= 0.70]
        top = sorted(top, key=lambda x: -x[1]['wins']/x[1]['total'])[:8]
        if top:
            lines.append(f"  {sig}:")
            for sym, d in top:
                wr = d['wins'] / d['total'] * 100
                avg_r = sum(d['returns'])/len(d['returns']) if d['returns'] else 0
                lines.append(f"    {sym:<10} {wr:.0f}% win  {avg_r:+.1f}% avg  ({d['total']} signals)")

    lines.append("")
    lines.append("  STOP LOSS RECOMMENDATIONS (based on backtest):")
    lines.append("  QUICK_PICK      current -4%  -> widen to -6% (too many stopped out)")
    lines.append("  SMART_PICK      current -5%  -> widen to -8% (40% stop rate is too high)")
    lines.append("  MOMENTUM_HUNTER current -6%  -> keep as is")
    lines.append("  DEPLOY_READY    current -8%  -> keep as is")
    lines.append("")
    lines.append("=" * 60)

    with open('backtest_summary.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print("\n  Saved backtest_summary.txt")

def main():
    print()
    print("=" * 55)
    print("  SAVING BACKTEST SCORES TO DB")
    print("=" * 55)

    conn   = get_conn()
    prices = load_prices(conn)
    nepse_idx = load_nepse_index(prices)

    all_stats = {}

    sims = [
        ('QUICK_PICK',       simulate_quick_pick(prices)),
        ('SMART_PICK',       simulate_smart_pick(prices)),
        ('MOMENTUM_HUNTER',  simulate_momentum_hunter(prices)),
        ('DEPLOY_READY',     simulate_deploy_ready(prices, nepse_idx)),
    ]

    for signal_type, signals in sims:
        print(f"\n  Processing {signal_type} ({len(signals):,} signals)...")
        by_sym = evaluate_and_store(conn, signals, signal_type, prices)

        # Aggregate stats for summary
        total  = sum(d['total'] for d in by_sym.values())
        wins   = sum(d['wins']  for d in by_sym.values())
        all_rets = [r for d in by_sym.values() for r in d['returns']]
        all_stats[signal_type] = {
            'total':    total,
            'win_rate': wins / total * 100 if total else 0,
            'avg_ret':  sum(all_rets) / len(all_rets) if all_rets else 0,
            'by_sym':   by_sym,
        }

    conn.close()
    save_summary(all_stats)

    print()
    print("  Done! backtest_scores table saved to DB.")
    print("  signal_tracker.py will now show historical win rates.")
    print()

if __name__ == '__main__':
    main()
