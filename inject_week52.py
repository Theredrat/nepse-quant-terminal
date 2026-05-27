"""
inject_week52.py
Adds --week52 command to nepse_scanner.py
Shows stocks near 52-week highs/lows, cross-referenced with RS leaders
Uses local DB only — no API calls needed
"""

import re, shutil, os

SCANNER = "nepse_scanner.py"
BACKUP  = "nepse_scanner_pre_week52.py"

WEEK52_FUNC = '''
# ── 52-WEEK HIGH/LOW ALERTS ───────────────────────────────────────────────────

def analyze_week52(db_path="nepse_market_data.db"):
    """
    Find stocks near 52-week highs/lows.
    Cross-references with RS leaders for highest conviction setups.
    """
    import sqlite3, pandas as pd
    from rich.table import Table
    from rich import box

    console.rule("[bold cyan]52-Week High / Low Alerts[/]")
    console.print("[dim]Breakout candidates near highs · Recovery plays near lows · Cross-checked with RS[/]\\n")

    conn = sqlite3.connect(db_path)

    # ── Pull 52-week range + current price for all equity stocks ─────────────
    df = pd.read_sql_query("""
        SELECT
            sp.symbol,
            c.sector,
            MAX(CASE WHEN sp.date >= date('now','-365 days') THEN sp.high END) as high52,
            MIN(CASE WHEN sp.date >= date('now','-365 days') THEN sp.low  END) as low52,
            MAX(CASE WHEN sp.date >= date('now','-10 days')  THEN sp.close END) as current,
            MAX(sp.date) as last_date
        FROM stock_prices sp
        JOIN companies c ON sp.symbol = c.symbol
        WHERE sp.date >= date('now','-365 days')
        GROUP BY sp.symbol
    """, conn)
    conn.close()

    if df.empty:
        console.print("[red]No price data available.[/]")
        return

    df = df.dropna(subset=["high52","low52","current"])
    df["range52"] = df["high52"] - df["low52"]
    df["pct_from_high"] = (df["current"] - df["high52"]) / df["high52"] * 100
    df["pct_from_low"]  = (df["current"] - df["low52"])  / df["low52"]  * 100
    df["range_pct"]     = df["range52"] / df["low52"] * 100

    # ── Get RS data for cross-reference ──────────────────────────────────────
    rs_data   = _calc_relative_strength()
    rs_lookup = {r["symbol"]: r["rs5"] for r in rs_data} if rs_data else {}

    df["rs5"] = df["symbol"].map(rs_lookup).fillna(0)

    # ── Near 52-week HIGH (within 5%) ────────────────────────────────────────
    near_high = df[df["pct_from_high"] >= -5].sort_values("pct_from_high", ascending=False)

    def _signal(row):
        at_high  = row["pct_from_high"] >= -1
        rs_good  = row["rs5"] > 1
        if at_high and rs_good:   return "[bold green]★★★ BREAKOUT[/]"
        if at_high:               return "[green]★★  At High[/]"
        if rs_good:               return "[cyan]★   RS+Near High[/]"
        return "[dim]–   Near High[/]"

    tbl_high = Table(
        title="Near 52-Week High — Breakout Watch",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    tbl_high.add_column("#",            style="dim",        width=4)
    tbl_high.add_column("Symbol",       style="bold cyan",  width=10)
    tbl_high.add_column("Sector",       style="white",      width=22)
    tbl_high.add_column("Current",      justify="right",    width=10)
    tbl_high.add_column("52W High",     justify="right",    width=10)
    tbl_high.add_column("From High",    justify="right",    width=10)
    tbl_high.add_column("52W Low",      justify="right",    width=10)
    tbl_high.add_column("RS (5D)",      justify="right",    width=10)
    tbl_high.add_column("Signal",       width=20)

    for i, (_, row) in enumerate(near_high.head(20).iterrows(), 1):
        pfh  = row["pct_from_high"]
        rs5  = row["rs5"]
        rc   = "green" if pfh >= -1 else "yellow"
        rsc  = "green" if rs5 > 0 else "red"
        sign = "+" if rs5 >= 0 else ""
        tbl_high.add_row(
            str(i),
            row["symbol"],
            row["sector"],
            f"Rs {row['current']:,.1f}",
            f"Rs {row['high52']:,.1f}",
            f"[{rc}]{pfh:+.1f}%[/]",
            f"Rs {row['low52']:,.1f}",
            f"[{rsc}]{sign}{rs5:.1f}%[/]",
            _signal(row),
        )
    console.print(tbl_high)

    # ── Near 52-week LOW (within 10%) ─────────────────────────────────────────
    near_low = df[df["pct_from_low"] <= 10].sort_values("pct_from_low")

    tbl_low = Table(
        title="Near 52-Week Low — Avoid or Watch for Recovery",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    tbl_low.add_column("#",           style="dim",       width=4)
    tbl_low.add_column("Symbol",      style="bold red",  width=10)
    tbl_low.add_column("Sector",      style="white",     width=22)
    tbl_low.add_column("Current",     justify="right",   width=10)
    tbl_low.add_column("52W Low",     justify="right",   width=10)
    tbl_low.add_column("From Low",    justify="right",   width=10)
    tbl_low.add_column("52W High",    justify="right",   width=10)
    tbl_low.add_column("RS (5D)",     justify="right",   width=10)
    tbl_low.add_column("Warning",     width=20)

    for i, (_, row) in enumerate(near_low.head(15).iterrows(), 1):
        pfl = row["pct_from_low"]
        rs5 = row["rs5"]
        rc  = "red" if pfl <= 3 else "yellow"
        rsc = "green" if rs5 > 0 else "red"
        sign = "+" if rs5 >= 0 else ""
        warning = "[bold red]AT LOW[/]" if pfl <= 1 else "[red]Danger Zone[/]" if pfl <= 5 else "[yellow]Watch[/]"
        tbl_low.add_row(
            str(i),
            row["symbol"],
            row["sector"],
            f"Rs {row['current']:,.1f}",
            f"Rs {row['low52']:,.1f}",
            f"[{rc}]+{pfl:.1f}%[/]",
            f"Rs {row['high52']:,.1f}",
            f"[{rsc}]{sign}{rs5:.1f}%[/]",
            warning,
        )
    console.print(tbl_low)

    # ── Sector summary ────────────────────────────────────────────────────────
    sec = df.groupby("sector").apply(lambda g: pd.Series({
        "near_high": (g["pct_from_high"] >= -5).sum(),
        "near_low":  (g["pct_from_low"]  <= 10).sum(),
        "total":     len(g),
        "avg_from_high": g["pct_from_high"].mean(),
    })).reset_index().sort_values("avg_from_high", ascending=False)

    stbl = Table(
        title="Sector 52-Week Position Summary",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    stbl.add_column("Sector",        style="white",  width=26)
    stbl.add_column("Near High",     justify="right", width=12)
    stbl.add_column("Near Low",      justify="right", width=12)
    stbl.add_column("Avg From High", justify="right", width=14)
    stbl.add_column("Strength",      width=20)

    for _, row in sec.iterrows():
        afh = row["avg_from_high"]
        color = "green" if afh >= -10 else "yellow" if afh >= -25 else "red"
        bar_n = max(0, min(12, int((afh + 50) / 50 * 12)))
        bar = "█" * bar_n + "░" * (12 - bar_n)
        stbl.add_row(
            str(row["sector"]),
            f"[green]{int(row['near_high'])}/{int(row['total'])}[/]",
            f"[red]{int(row['near_low'])}/{int(row['total'])}[/]",
            f"[{color}]{afh:+.1f}%[/]",
            f"[{color}]{bar}[/]",
        )
    console.print(stbl)

    # ── Top conviction: near high + strong RS ────────────────────────────────
    conviction = df[
        (df["pct_from_high"] >= -5) & (df["rs5"] >= 2)
    ].sort_values(["pct_from_high", "rs5"], ascending=[False, False])

    if not conviction.empty:
        console.print("\\n  [bold green]★★★ Highest conviction setups (Near 52W High + Strong RS):[/]")
        for _, row in conviction.head(5).iterrows():
            console.print(
                f"    [cyan]{row['symbol']}[/] ({row['sector']}) — "
                f"[green]{row['pct_from_high']:+.1f}%[/] from high, "
                f"RS [green]+{row['rs5']:.1f}%[/]"
            )
    else:
        console.print("\\n  [yellow]No stocks currently near 52W high with strong RS — market may be extended or weak[/]")
'''

def patch():
    if not os.path.exists(SCANNER):
        print(f"ERROR: {SCANNER} not found.")
        return

    shutil.copy(SCANNER, BACKUP)
    print(f"Backed up → {BACKUP}")

    with open(SCANNER, encoding="utf-8") as f:
        src = f.read()

    # Insert function before main guard
    anchor = 'if __name__ == "__main__":'
    if anchor not in src:
        print("ERROR: cannot find main() anchor.")
        return
    src = src.replace(anchor, WEEK52_FUNC + "\n\n" + anchor, 1)

    # Add --week52 CLI arg
    if "--week52" not in src:
        src = src.replace(
            "p.add_argument('--rs',",
            "p.add_argument('--week52',       action='store_true', help='52-week high/low alerts + RS cross-check')\n    p.add_argument('--rs',"
        )
        print("✓ Added --week52 argument")

    # Add dispatch
    if "analyze_week52()" not in src:
        src = src.replace(
            "elif args.rs:\n        analyze_relative_strength()",
            "elif args.week52:\n        analyze_week52()\n    elif args.rs:\n        analyze_relative_strength()"
        )
        print("✓ Added dispatch call")

    with open(SCANNER, "w", encoding="utf-8") as f:
        f.write(src)

    # Update launch_nepse.bat
    bat = "launch_nepse.bat"
    if os.path.exists(bat):
        with open(bat, encoding="utf-8") as f:
            bc = f.read()
        if "--week52" not in bc:
            bc = bc.replace(
                'if "%choice%"=="7r" python nepse_scanner.py --rs & goto AGAIN',
                'if "%choice%"=="7w" python nepse_scanner.py --week52 & goto AGAIN\nif "%choice%"=="7r" python nepse_scanner.py --rs & goto AGAIN'
            )
            with open(bat, "w", encoding="utf-8") as f:
                f.write(bc)
            print("✓ launch_nepse.bat: added 7w for --week52")

    print()
    print("✓ Patched successfully!")
    print()
    print("Test with:")
    print("  python nepse_scanner.py --week52")

if __name__ == "__main__":
    patch()
