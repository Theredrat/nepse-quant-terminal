"""
Signal Performance Tracker for NEPSE Scanner
Logs signals and checks if they hit +5% in 3/5/10 days
"""
import json, os, sys
from datetime import datetime, timedelta
import requests
from rich.console import Console
from rich.table import Table

console = Console()
LOG_FILE = "signal_log.json"
WIN_TARGET = 5.0  # +5% = win

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def save_log(data):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_current_price(symbol):
    try:
        url = f'https://nepalstock.com.np/api/nots/security/{symbol}'
        r = requests.get(url, timeout=10)
        data = r.json()
        price = float(data.get('securityDailyTradeDto', {}).get('closingPrice', 0))
        if price > 0:
            return price
    except:
        pass
    try:
        import sqlite3
        conn = sqlite3.connect('nepse_market_data')
        for table in ['daily_prices', 'ohlcv', 'prices']:
            try:
                row = conn.execute(f'SELECT close FROM {table} WHERE symbol=? ORDER BY date DESC LIMIT 1', (symbol,)).fetchone()
                if row and row[0]:
                    conn.close()
                    return float(row[0])
            except:
                continue
        conn.close()
    except:
        pass
    return None

def get_entry_price(symbol, live_prices):
    price = live_prices.get(symbol, 0)
    if price > 0:
        return price
    return get_current_price(symbol) or 0

def log_signals(candidates):
    """Call this after run_signals() to record signals"""
    if candidates is None or candidates.empty:
        return
    log = load_log()
    today = datetime.now().strftime("%Y-%m-%d")
    new_count = 0
    for _, row in candidates.iterrows():
        sym = row.get("symbol", "")
        sig = row.get("signal", "")
        ltp = float(row.get("ltp", 0))
        if not sym or not ltp:
            continue
        # Avoid duplicate logging same symbol+signal on same day
        already = any(
            e["symbol"] == sym and e["signal"] == sig and e["date"] == today
            for e in log
        )
        if not already:
            log.append({
                "symbol": sym,
                "signal": sig,
                "date": today,
                "entry_price": ltp,
                "score": float(row.get("score", 0)),
                "reason": row.get("reason", ""),
                "result_3d": None,
                "result_5d": None,
                "result_10d": None,
                "checked_3d": False,
                "checked_5d": False,
                "checked_10d": False,
            })
            new_count += 1
    save_log(log)
    if new_count:
        console.print(f"  [dim]📝 Logged {new_count} new signals to signal_log.json[/dim]")

def update_results():
    """Check pending signals and update results"""
    log = load_log()
    today = datetime.now()
    updated = 0
    for entry in log:
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")
        days_passed = (today - entry_date).days
        sym = entry["symbol"]
        price = None

        for days, key_checked, key_result in [
            (3, "checked_3d", "result_3d"),
            (5, "checked_5d", "result_5d"),
            (10, "checked_10d", "result_10d"),
        ]:
            if days_passed >= days and not entry[key_checked]:
                if price is None:
                    price = get_current_price(sym)
                if price and entry["entry_price"] > 0:
                    pct = ((price - entry["entry_price"]) / entry["entry_price"]) * 100
                    entry[key_result] = round(pct, 2)
                    entry[key_checked] = True
                    updated += 1

    if updated:
        save_log(log)
        console.print(f"  [green]✅ Updated {updated} signal results[/green]")
    return updated

def show_report():
    """Display signal accuracy report"""
    update_results()
    log = load_log()

    if not log:
        console.print("[yellow]No signals logged yet. Run option 1, 4, or 5 first.[/yellow]")
        return

    console.print()
    console.print("[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║       SIGNAL PERFORMANCE TRACKER                ║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]")
    console.print(f"  Win target: +{WIN_TARGET}%  |  Total signals logged: {len(log)}")
    console.print()

    # Group by signal type
    from collections import defaultdict
    stats = defaultdict(lambda: {"3d": [], "5d": [], "10d": []})
    for e in log:
        sig = e["signal"]
        if e["result_3d"] is not None:
            stats[sig]["3d"].append(e["result_3d"])
        if e["result_5d"] is not None:
            stats[sig]["5d"].append(e["result_5d"])
        if e["result_10d"] is not None:
            stats[sig]["10d"].append(e["result_10d"])

    table = Table(show_header=True, header_style="bold white")
    table.add_column("Signal Type", style="cyan", width=22)
    table.add_column("3d Acc", justify="center", width=10)
    table.add_column("5d Acc", justify="center", width=10)
    table.add_column("10d Acc", justify="center", width=10)
    table.add_column("Trades", justify="center", width=8)

    all_results_5d = []
    for sig, data in sorted(stats.items()):
        def acc(results):
            if not results: return "[dim]--[/dim]"
            wins = sum(1 for r in results if r >= WIN_TARGET)
            pct = (wins / len(results)) * 100
            color = "green" if pct >= 60 else "yellow" if pct >= 40 else "red"
            return f"[{color}]{pct:.0f}%[/{color}]"

        trades = max(len(data["3d"]), len(data["5d"]), len(data["10d"]))
        table.add_row(sig, acc(data["3d"]), acc(data["5d"]), acc(data["10d"]), str(trades))
        all_results_5d.extend(data["5d"])

    console.print(table)

    if all_results_5d:
        overall = sum(1 for r in all_results_5d if r >= WIN_TARGET) / len(all_results_5d) * 100
        color = "green" if overall >= 60 else "yellow" if overall >= 40 else "red"
        console.print(f"\n  Overall 5-day accuracy: [{color}]{overall:.0f}%[/{color}] ({len(all_results_5d)} resolved trades)")

    # Recent signals
    console.print()
    console.print("[bold white]  Recent Signals (last 10):[/bold white]")
    recent = Table(show_header=True, header_style="bold white", box=None)
    recent.add_column("Date", width=12)
    recent.add_column("Symbol", width=10)
    recent.add_column("Signal", width=22)
    recent.add_column("Entry", justify="right", width=10)
    recent.add_column("3d", justify="center", width=8)
    recent.add_column("5d", justify="center", width=8)
    recent.add_column("10d", justify="center", width=8)

    def fmt_result(r):
        if r is None: return "[dim]--[/dim]"
        color = "green" if r >= WIN_TARGET else "red" if r < 0 else "yellow"
        return f"[{color}]{r:+.1f}%[/{color}]"

    for e in reversed(log[-10:]):
        recent.add_row(
            e["date"], e["symbol"], e["signal"],
            f"Rs {e['entry_price']:.2f}",
            fmt_result(e["result_3d"]),
            fmt_result(e["result_5d"]),
            fmt_result(e["result_10d"]),
        )
    console.print(recent)
    console.print()

if __name__ == "__main__":
    if "--report" in sys.argv:
        show_report()
    elif "--update" in sys.argv:
        update_results()
    else:
        show_report()
