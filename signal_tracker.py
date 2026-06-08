"""
signal_tracker.py  —  NEPSE Signal Performance Tracker  v3
Option 32 in nepse_scanner.py menu

Features:
  - Per-signal win targets
  - Streak tracking (consecutive days + reappearance after gap)
  - Times picked in last 14 days
  - Move% from first logged price
  - Entry status: OK / STRONG / RE-ENTRY / PULLBACK-BUY / CAUTION / LATE / AVOID
  - Historical backtest score per symbol (from backtest_scores table)
  - 3d/7d/14d accuracy (all signals)
  - 30d accuracy (DEPLOY_READY / DEPLOY_HOT only)
"""

import sqlite3
import sys
from datetime import datetime, timedelta

DB = 'nepse_market_data.db'

# ── Per-signal configuration ──────────────────────────────────────────────────
SIGNAL_CONFIG = {
    'QUICK_PICK':       {'target': 7.0,  'stop': 4.0,  'hold': 5,  'periods': [3, 7, 14]},
    'SMART_PICK':       {'target': 10.0, 'stop': 5.0,  'hold': 10, 'periods': [3, 7, 14]},
    'MOMENTUM_HUNTER':  {'target': 12.0, 'stop': 6.0,  'hold': 14, 'periods': [3, 7, 14]},
    'DEPLOY_READY':     {'target': 20.0, 'stop': 8.0,  'hold': 30, 'periods': [7, 14, 30]},
    'DEPLOY_HOT':       {'target': 15.0, 'stop': 6.0,  'hold': 14, 'periods': [3, 7, 14]},
}

DEFAULT_CONFIG = {'target': 10.0, 'stop': 5.0, 'hold': 14, 'periods': [3, 7, 14]}

# ── DB setup ──────────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signal_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            date      TEXT NOT NULL,
            symbol    TEXT NOT NULL,
            signal    TEXT NOT NULL,
            source    TEXT,
            entry_price REAL,
            score     REAL,
            reason    TEXT,
            result_3d  REAL,
            result_7d  REAL,
            result_14d REAL,
            result_30d REAL,
            UNIQUE(date, symbol, signal)
        )
    """)
    try:
        conn.execute("ALTER TABLE signal_log ADD COLUMN result_30d REAL")
        conn.commit()
    except Exception:
        pass
    conn.commit()
    return conn

# ── Logging API ───────────────────────────────────────────────────────────────
def log_signals_raw(signals, source='?'):
    if not signals:
        return
    conn = get_conn()
    today = datetime.now().strftime('%Y-%m-%d')
    for s in signals:
        sym    = str(s.get('symbol', '')).strip().upper()
        sig    = str(s.get('signal', '')).strip().upper()
        ltp    = float(s.get('ltp', 0) or 0)
        score  = float(s.get('score', 0) or 0)
        reason = str(s.get('reason', ''))
        if not sym or not sig:
            continue
        try:
            conn.execute(
                "INSERT OR IGNORE INTO signal_log (date,symbol,signal,source,entry_price,score,reason) VALUES (?,?,?,?,?,?,?)",
                (today, sym, sig, source, ltp, score, reason)
            )
        except Exception:
            pass
    conn.commit()
    conn.close()

# ── Update results ────────────────────────────────────────────────────────────
def _get_price_after(conn, symbol, from_date, trading_days):
    rows = conn.execute(
        "SELECT date, close FROM stock_prices WHERE symbol=? AND date>? ORDER BY date ASC",
        (symbol, from_date)
    ).fetchall()
    if not rows or len(rows) < trading_days:
        return None
    return rows[trading_days - 1][1]

def _get_latest_price(conn, symbol):
    r = conn.execute(
        "SELECT close FROM stock_prices WHERE symbol=? ORDER BY date DESC LIMIT 1",
        (symbol,)
    ).fetchone()
    return r[0] if r else None

def _get_backtest_score(conn, symbol, signal):
    """Get historical backtest win rate and avg return for this symbol+signal."""
    r = conn.execute(
        "SELECT win_rate, avg_return, expectancy, total FROM backtest_scores WHERE symbol=? AND signal=?",
        (symbol, signal)
    ).fetchone()
    return r if r else None

def update_results():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, date, symbol, signal, entry_price, result_3d, result_7d, result_14d, result_30d FROM signal_log"
    ).fetchall()
    updated = 0
    for row in rows:
        id_, date, symbol, signal, entry, r3, r7, r14, r30 = row
        if not entry or entry <= 0:
            continue
        cfg = SIGNAL_CONFIG.get(signal, DEFAULT_CONFIG)
        periods = cfg['periods']
        changes = {}

        if 3 in periods and r3 is None:
            p = _get_price_after(conn, symbol, date, 3)
            if p:
                changes['result_3d'] = round((p - entry) / entry * 100, 2)

        if 7 in periods and r7 is None:
            p = _get_price_after(conn, symbol, date, 7)
            if p:
                changes['result_7d'] = round((p - entry) / entry * 100, 2)

        if 14 in periods and r14 is None:
            p = _get_price_after(conn, symbol, date, 14)
            if p:
                changes['result_14d'] = round((p - entry) / entry * 100, 2)

        if 30 in periods and r30 is None:
            p = _get_price_after(conn, symbol, date, 30)
            if p:
                changes['result_30d'] = round((p - entry) / entry * 100, 2)

        if changes:
            sets = ', '.join(f"{k}=?" for k in changes)
            conn.execute(f"UPDATE signal_log SET {sets} WHERE id=?", (*changes.values(), id_))
            updated += 1

    conn.commit()
    conn.close()
    print(f"[signal_tracker] Updated {updated} entries.")

# ── Streak logic ──────────────────────────────────────────────────────────────
def _calc_streak(conn, symbol, signal, today_str):
    today   = datetime.strptime(today_str, '%Y-%m-%d')
    cutoff  = (today - timedelta(days=20)).strftime('%Y-%m-%d')
    rows    = conn.execute(
        "SELECT DISTINCT date FROM signal_log WHERE symbol=? AND signal=? AND date>=? ORDER BY date DESC",
        (symbol, signal, cutoff)
    ).fetchall()
    dates = [datetime.strptime(r[0], '%Y-%m-%d') for r in rows]
    if not dates:
        return 1, 1, None, False

    consec = 0
    prev   = today
    for d in sorted(dates, reverse=True):
        gap = (prev - d).days
        if gap <= 1:
            consec += 1
            prev = d
        else:
            break

    cutoff14  = today - timedelta(days=14)
    total_14d = sum(1 for d in dates if d >= cutoff14)

    prev_dates = [d for d in dates if d < today]
    last_gap   = None
    reappeared = False
    if prev_dates:
        most_recent_prev = max(prev_dates)
        last_gap   = (today - most_recent_prev).days
        reappeared = 2 <= last_gap <= 7

    return consec, total_14d, last_gap, reappeared

# ── Entry status ──────────────────────────────────────────────────────────────
def _entry_status(signal, move_pct, consec, reappeared):
    cfg    = SIGNAL_CONFIG.get(signal, DEFAULT_CONFIG)
    target = cfg['target']

    if move_pct >= target:
        return 'HIT TARGET'
    if move_pct >= target * 0.6:
        return 'LATE'
    if move_pct >= target * 0.3:
        return 'CAUTION'
    if -5.0 <= move_pct < -0.5:
        if reappeared or consec >= 2:
            return 'PULLBACK-BUY'
        return 'PULLBACK'
    if move_pct < -5.0:
        return 'AVOID'
    if reappeared:
        return 'RE-ENTRY'
    if consec >= 3:
        return 'STRONG'
    return 'OK'

# ── Format helpers ────────────────────────────────────────────────────────────
def _fmt_result(val, target):
    if val is None:
        return '  --  '
    sign   = '+' if val >= 0 else ''
    marker = ' W' if val >= target else (' L' if val < 0 else '  ')
    return f"{sign}{val:.1f}%{marker}"

def _fmt_move(pct):
    if pct is None:
        return '  --  '
    sign = '+' if pct >= 0 else ''
    return f"{sign}{pct:.1f}%"

def _fmt_hist(score):
    """Format historical backtest score."""
    if score is None:
        return '  --  '
    win_rate, avg_ret, exp, total = score
    grade = 'A' if exp > 3 else 'B' if exp > 1 else 'C' if exp > 0 else 'D'
    return f"{win_rate:.0f}%/{avg_ret:+.1f}%[{grade}]"

def _pad(s, n):
    s = str(s)
    return s[:n].ljust(n)

# ── Main report ───────────────────────────────────────────────────────────────
def show_report():
    conn  = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM signal_log").fetchone()[0]

    # Check if backtest scores exist
    has_backtest = False
    try:
        c = conn.execute("SELECT COUNT(*) FROM backtest_scores").fetchone()[0]
        has_backtest = c > 0
    except Exception:
        pass

    print()
    print("=" * 70)
    print("       SIGNAL PERFORMANCE TRACKER  v3")
    print("=" * 70)
    print(f"  Total signals logged: {total}")
    if has_backtest:
        print(f"  Historical scores: available (from backtest)")
    else:
        print(f"  Historical scores: not yet (run: python save_backtest.py)")
    print()

    # ── Section 1: Accuracy by signal type ───────────────────────────────────
    print(f"  {'Signal Type':<20} {'Target':>7} {'Hold':>6}   {'3d Acc':>8} {'7d Acc':>8} {'14d Acc':>8} {'30d Acc':>8}")
    print("  " + "-" * 68)

    signal_types = conn.execute(
        "SELECT DISTINCT signal FROM signal_log ORDER BY signal"
    ).fetchall()

    for (sig,) in signal_types:
        cfg     = SIGNAL_CONFIG.get(sig, DEFAULT_CONFIG)
        target  = cfg['target']
        hold    = cfg['hold']
        periods = cfg['periods']

        def acc(col, period):
            if period not in periods:
                return '  n/a  '
            rows = conn.execute(
                f"SELECT {col} FROM signal_log WHERE signal=? AND {col} IS NOT NULL",
                (sig,)
            ).fetchall()
            if not rows:
                return '  --  '
            wins = sum(1 for r in rows if r[0] >= target)
            return f"{wins}/{len(rows)} ({int(wins/len(rows)*100)}%)"

        print(f"  {_pad(sig,20)} {target:>6.0f}%  {hold:>3}d   {acc('result_3d',3):>8} {acc('result_7d',7):>8} {acc('result_14d',14):>8} {acc('result_30d',30):>8}")

    print()

    # ── Section 2: Active signals ─────────────────────────────────────────────
    today_str = datetime.now().strftime('%Y-%m-%d')

    has_hist_col = '  Hist(win%/ret)[grade]' if has_backtest else ''
    print(f"  ACTIVE SIGNALS — Streak & Entry Status")
    print(f"  {'Symbol':<10} {'Signal':<18} {'Str':>4} {'x14':>4} {'Entry':>7} {'Now':>7} {'Move%':>7} {'Status':<14} {'Src':<5}{has_hist_col}")
    print("  " + "-" * (90 if has_backtest else 70))

    active = conn.execute("""
        SELECT symbol, signal, source, entry_price,
               MIN(date) as first_date, MAX(date) as last_date
        FROM signal_log
        GROUP BY symbol, signal
        ORDER BY last_date DESC, symbol
    """).fetchall()

    for symbol, signal, source, entry_price, first_date, last_date in active:
        if not entry_price or entry_price <= 0:
            continue

        now_price = _get_latest_price(conn, symbol)
        if now_price:
            move_pct = (now_price - entry_price) / entry_price * 100
        else:
            now_price = entry_price
            move_pct  = 0.0

        consec, total_14d, last_gap, reappeared = _calc_streak(conn, symbol, signal, today_str)
        status = _entry_status(signal, move_pct, consec, reappeared)

        streak_str = f"{consec}d"
        if reappeared and last_gap:
            streak_str = f"{consec}d+{last_gap}g"

        hist_str = ''
        if has_backtest:
            score    = _get_backtest_score(conn, symbol, signal)
            hist_str = f"  {_fmt_hist(score)}"

        print(
            f"  {_pad(symbol,10)} {_pad(signal,18)} {streak_str:>4} "
            f"{total_14d:>4} {entry_price:>7.0f} {now_price:>7.0f} "
            f"{_fmt_move(move_pct):>7} {_pad(status,14)} {str(source):<5}{hist_str}"
        )

    print()

    # ── Section 3: Top historical picks active right now ──────────────────────
    if has_backtest:
        print(f"  TOP HISTORICAL PICKS (currently active, grade A or B):")
        print(f"  {'Symbol':<10} {'Signal':<18} {'Hist Win%':>10} {'Hist Ret':>9} {'Grade':>6} {'Status':<14}")
        print("  " + "-" * 70)

        top_active = []
        for symbol, signal, source, entry_price, first_date, last_date in active:
            if not entry_price or entry_price <= 0:
                continue
            score = _get_backtest_score(conn, symbol, signal)
            if not score:
                continue
            win_rate, avg_ret, exp, total_bt = score
            if total_bt < 3:
                continue
            grade = 'A' if exp > 3 else 'B' if exp > 1 else None
            if not grade:
                continue

            now_price = _get_latest_price(conn, symbol) or entry_price
            move_pct  = (now_price - entry_price) / entry_price * 100
            consec, total_14d, last_gap, reappeared = _calc_streak(conn, symbol, signal, today_str)
            status = _entry_status(signal, move_pct, consec, reappeared)

            if status not in ('LATE', 'HIT TARGET', 'AVOID'):
                top_active.append((symbol, signal, win_rate, avg_ret, exp, grade, status))

        top_active.sort(key=lambda x: -x[4])  # sort by expectancy
        for row in top_active[:15]:
            sym, sig, wr, ar, exp, grade, status = row
            print(f"  {_pad(sym,10)} {_pad(sig,18)} {wr:>9.1f}% {ar:>+8.2f}% {grade:>6}  {status}")

        if not top_active:
            print(f"  None currently active with grade A or B")
        print()

    # ── Section 4: Resolved signals ───────────────────────────────────────────
    resolved = conn.execute("""
        SELECT date, symbol, signal, source, entry_price,
               result_3d, result_7d, result_14d, result_30d
        FROM signal_log
        WHERE result_3d IS NOT NULL OR result_7d IS NOT NULL
              OR result_14d IS NOT NULL OR result_30d IS NOT NULL
        ORDER BY date DESC
        LIMIT 30
    """).fetchall()

    if resolved:
        print(f"  RESOLVED SIGNALS (last 30):")
        print(f"  {'Date':<12} {'Symbol':<10} {'Signal':<18} {'Entry':>7}  {'3d':>8} {'7d':>8} {'14d':>8} {'30d':>8}  Src")
        print("  " + "-" * 80)
        for row in resolved:
            date, sym, sig, src, entry, r3, r7, r14, r30 = row
            cfg = SIGNAL_CONFIG.get(sig, DEFAULT_CONFIG)
            t   = cfg['target']
            print(
                f"  {date:<12} {_pad(sym,10)} {_pad(sig,18)} {entry:>7.0f}  "
                f"{_fmt_result(r3,t):>8} {_fmt_result(r7,t):>8} "
                f"{_fmt_result(r14,t):>8} {_fmt_result(r30,t):>8}  {src}"
            )
        print()

    print("  " + "-" * 70)
    print("  Targets: QP +7% | SP +10% | MH +12% | DEPLOY_HOT +15% | DEPLOY_READY +20%")
    print("  Streak: Xd=consecutive days | +Xg=gap days before reappear | x14=times in 14d")
    print("  Status: STRONG=3d+ | RE-ENTRY=gap reappear | PULLBACK-BUY=dip+confirmed")
    print("  Hist: backtest win%/avg_return[grade] A=exp>3% B=exp>1% C=exp>0% D=poor")
    print("  W=Win L=Loss in result columns")
    print()

    conn.close()

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if '--update' in sys.argv:
        update_results()
    else:
        update_results()
        show_report()
