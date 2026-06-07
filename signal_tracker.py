"""
Signal Performance Tracker for NEPSE Scanner
Uses SQLite DB (stock_prices table) for outcome checking — no live API needed.
"""
import sys, os, sqlite3
from datetime import datetime, date, timedelta
from rich.console import Console
from rich.table import Table

DB_PATH = 'nepse_market_data.db'
WIN_TARGET = 5.0  # +5% = win
CONSOLE_WIDTH = 120

def get_conn():
    return sqlite3.connect(DB_PATH)

def ensure_table():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signal_log (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            date     TEXT NOT NULL,
            symbol   TEXT NOT NULL,
            signal   TEXT NOT NULL,
            source   TEXT DEFAULT '',
            entry_price REAL NOT NULL,
            score    REAL DEFAULT 0,
            reason   TEXT DEFAULT '',
            result_3d  REAL,
            result_7d  REAL,
            result_14d REAL,
            UNIQUE(date, symbol, signal)
        )
    """)
    conn.commit()
    conn.close()

def log_signals_raw(signals: list, source: str = ''):
    """Log signals. signals = list of dicts with keys: symbol, signal, ltp/entry_price, score, reason"""
    ensure_table()
    if not signals:
        return
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_conn()
    new_count = 0
    for s in signals:
        sym   = str(s.get('symbol') or '').strip()
        sig   = str(s.get('signal') or '').strip()
        price = float(s.get('ltp') or s.get('entry_price') or 0)
        score = float(s.get('score') or 0)
        reason = str(s.get('reason') or '')
        if not sym or price <= 0:
            continue
        try:
            conn.execute(
                "INSERT OR IGNORE INTO signal_log (date,symbol,signal,source,entry_price,score,reason) VALUES (?,?,?,?,?,?,?)",
                (today, sym, sig, source, price, score, reason)
            )
            if conn.total_changes > 0:
                new_count += 1
        except Exception as e:
            pass
    conn.commit()
    conn.close()
    if new_count:
        print(f"[signal_tracker] Logged {new_count} new signals.")

def log_signals(candidates, source: str = ''):
    """Compatibility wrapper for DataFrame-based callers"""
    if candidates is None:
        return
    try:
        import pandas as pd
        if isinstance(candidates, pd.DataFrame) and candidates.empty:
            return
    except ImportError:
        pass
    rows = []
    if hasattr(candidates, 'iterrows'):
        for _, row in candidates.iterrows():
            rows.append({
                'symbol': row.get('symbol', ''),
                'signal': row.get('signal', ''),
                'ltp': row.get('ltp', 0),
                'score': row.get('score', 0),
                'reason': row.get('reason', ''),
            })
    elif isinstance(candidates, list):
        rows = candidates
    log_signals_raw(rows, source=source)

def _get_price_after(conn, symbol, from_date_str, trading_days):
    """Get close price N trading days after from_date using stock_prices table."""
    rows = conn.execute(
        "SELECT close FROM stock_prices WHERE symbol=? AND date>? ORDER BY date ASC LIMIT ?",
        (symbol, from_date_str, trading_days + 5)
    ).fetchall()
    if len(rows) >= trading_days:
        return rows[trading_days - 1][0]
    if rows:
        return rows[-1][0]
    return None

def update_results():
    """Fill in result_3d/7d/14d for any entries that now have enough price history."""
    ensure_table()
    conn = get_conn()
    pending = conn.execute(
        "SELECT id, date, symbol, entry_price FROM signal_log WHERE result_3d IS NULL OR result_7d IS NULL OR result_14d IS NULL"
    ).fetchall()
    updated = 0
    for row_id, sig_date, symbol, entry_price in pending:
        if not entry_price or entry_price <= 0:
            continue
        updates = {}
        for col, days in [('result_3d', 3), ('result_7d', 7), ('result_14d', 14)]:
            price = _get_price_after(conn, symbol, sig_date, days)
            if price and price > 0:
                updates[col] = round((price - entry_price) / entry_price * 100, 2)
        if updates:
            set_clause = ', '.join(f"{k}=?" for k in updates)
            conn.execute(f"UPDATE signal_log SET {set_clause} WHERE id=?", list(updates.values()) + [row_id])
            updated += 1
    conn.commit()
    conn.close()
    print(f"[signal_tracker] Updated {updated} entries.")

def show_report():
    ensure_table()
    update_results()
    conn = get_conn()
    rows = conn.execute(
        "SELECT date, symbol, signal, source, entry_price, score, reason, result_3d, result_7d, result_14d FROM signal_log ORDER BY date DESC, id DESC"
    ).fetchall()
    conn.close()

    console = Console(width=CONSOLE_WIDTH)
    console.print()
    console.print("[bold cyan]=================================================[/bold cyan]")
    console.print("[bold cyan]       SIGNAL PERFORMANCE TRACKER              [/bold cyan]")
    console.print("[bold cyan]=================================================[/bold cyan]")
    console.print(f"  Win target: +{WIN_TARGET}%  |  Total signals logged: {len(rows)}")
    console.print()

    if not rows:
        console.print("  [yellow]No signals logged yet. Signals are auto-logged when you run options 4, 5, 7b, 17f.[/yellow]")
        console.print()
        return

    # Build stats per signal type
    from collections import defaultdict
    stats = defaultdict(lambda: {'3d': [], '7d': [], '14d': []})
    for r in rows:
        sig = r[2]
        if r[7] is not None: stats[sig]['3d'].append(r[7])
        if r[8] is not None: stats[sig]['7d'].append(r[8])
        if r[9] is not None: stats[sig]['14d'].append(r[9])

    def acc(results):
        if not results: return '[dim]--[/dim]'
        wins = sum(1 for x in results if x >= WIN_TARGET)
        pct = wins / len(results) * 100
        col = 'green' if pct >= 60 else 'yellow' if pct >= 40 else 'red'
        return f'[{col}]{pct:.0f}%[/{col}] ({len(results)})'

    table = Table(show_header=True, header_style='bold white', box=None, padding=(0,1))
    table.add_column('Signal Type',  style='cyan', width=24, no_wrap=True)
    table.add_column('3d Acc',  justify='center', width=12)
    table.add_column('7d Acc',  justify='center', width=12)
    table.add_column('14d Acc', justify='center', width=12)

    all_7d = []
    for sig, d in sorted(stats.items()):
        table.add_row(sig, acc(d['3d']), acc(d['7d']), acc(d['14d']))
        all_7d.extend(d['7d'])

    console.print(table)

    if all_7d:
        overall = sum(1 for x in all_7d if x >= WIN_TARGET) / len(all_7d) * 100
        col = 'green' if overall >= 60 else 'yellow' if overall >= 40 else 'red'
        console.print(f"\n  Overall 7-day accuracy: [{col}]{overall:.0f}%[/{col}] ({len(all_7d)} resolved trades)")

    # Recent 15 signals
    console.print()
    console.print('[bold white]  Recent Signals (last 30):[/bold white]')
    rec = Table(show_header=True, header_style='bold white', box=None, padding=(0,1))
    rec.add_column('Date',   width=12, no_wrap=True)
    rec.add_column('Symbol', width=8,  no_wrap=True)
    rec.add_column('Signal', width=22, no_wrap=True)
    rec.add_column('Entry',  justify='right', width=8, no_wrap=True)
    rec.add_column('3d',     justify='center', width=8, no_wrap=True)
    rec.add_column('7d',     justify='center', width=8, no_wrap=True)
    rec.add_column('14d',    justify='center', width=9, no_wrap=True)
    rec.add_column('Src',    width=8,  no_wrap=True)

    def fmt(r):
        if r is None: return '[dim]--[/dim]'
        col = 'green' if r >= WIN_TARGET else 'red' if r < 0 else 'yellow'
        return f'[{col}]{r:+.1f}%[/{col}]'

    for r in rows[:30]:
        rec.add_row(r[0], r[1], r[2], f'{r[4]:.0f}', fmt(r[7]), fmt(r[8]), fmt(r[9]), r[3] or '')
    console.print(rec)
    console.print()

if __name__ == '__main__':
    if '--update' in sys.argv:
        update_results()
    else:
        show_report()
