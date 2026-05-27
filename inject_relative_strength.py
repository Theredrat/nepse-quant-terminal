"""
inject_relative_strength.py
Adds --rs (Relative Strength) command to nepse_scanner.py
Finds stocks outperforming their sector over 5D/10D/20D
"""

import re, shutil, os

SCANNER = "nepse_scanner.py"
BACKUP  = "nepse_scanner_pre_rs.py"

# ── 1. THE NEW FUNCTIONS ──────────────────────────────────────────────────────

RS_FUNCTIONS = '''
# ── RELATIVE STRENGTH ─────────────────────────────────────────────────────────

def _calc_relative_strength(db_path="nepse_market_data.db"):
    """
    For every equity stock, compute 5D/10D/20D return and compare
    to its sector average return over the same window.
    Returns a list of dicts sorted by 5D RS score descending.
    """
    import sqlite3, pandas as pd

    conn = sqlite3.connect(db_path)

    # Pull last 25 trading days for all equity stocks
    df = pd.read_sql_query("""
        SELECT sp.symbol, c.sector, sp.date, sp.close
        FROM stock_prices sp
        JOIN companies c ON sp.symbol = c.symbol
        WHERE sp.date >= date('now', '-35 days')
        ORDER BY sp.symbol, sp.date
    """, conn)
    conn.close()

    if df.empty:
        return []

    df["date"] = pd.to_datetime(df["date"])
    results = []

    for symbol, grp in df.groupby("symbol"):
        grp = grp.sort_values("date").drop_duplicates("date")
        if len(grp) < 6:
            continue
        sector = grp["sector"].iloc[0]
        closes = grp["close"].values

        def pct(n):
            if len(closes) <= n:
                return None
            return (closes[-1] / closes[-n-1] - 1) * 100

        results.append({
            "symbol": symbol,
            "sector": sector,
            "ret5":  pct(5),
            "ret10": pct(10),
            "ret20": pct(20),
        })

    if not results:
        return []

    import pandas as pd
    rdf = pd.DataFrame(results).dropna(subset=["ret5"])

    # Sector averages
    savg = rdf.groupby("sector")[["ret5","ret10","ret20"]].mean().rename(
        columns={"ret5":"sec5","ret10":"sec10","ret20":"sec20"})
    rdf = rdf.join(savg, on="sector")

    rdf["rs5"]  = rdf["ret5"]  - rdf["sec5"]
    rdf["rs10"] = rdf["ret10"] - rdf["sec10"]
    rdf["rs20"] = rdf["ret20"] - rdf["sec20"]

    # Composite RS score: weighted 50/30/20
    rdf["rs_score"] = rdf["rs5"]*0.50 + rdf["rs10"].fillna(0)*0.30 + rdf["rs20"].fillna(0)*0.20

    return rdf.sort_values("rs_score", ascending=False).to_dict("records")


def analyze_relative_strength():
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    console.rule("[bold cyan]Relative Strength — Stocks vs Their Sector[/]")
    console.print("[dim]Stocks gaining MORE than their sector = early movers[/]\\n")

    data = _calc_relative_strength()
    if not data:
        console.print("[red]No data available.[/]")
        return

    # ── TOP OUTPERFORMERS ────────────────────────────────────────────────────
    top = [r for r in data if r["rs5"] > 0][:20]
    bot = [r for r in reversed(data) if r["rs5"] < 0][:10]

    def _fmt(v, show_sign=True):
        if v is None: return "[dim]n/a[/]"
        color = "green" if v >= 0 else "red"
        sign  = "+" if v >= 0 else ""
        return f"[{color}]{sign}{v:.2f}%[/]"

    def _star(rs5):
        if rs5 >= 5:   return "[bold green]★★★ Strong[/]"
        if rs5 >= 2:   return "[green]★★  Leading[/]"
        if rs5 >= 0.5: return "[cyan]★   Outperform[/]"
        if rs5 >= -1:  return "[dim]–   Inline[/]"
        return "[red]▼   Lagging[/]"

    tbl = Table(
        title="Top Outperformers (Stock Return − Sector Avg)",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    tbl.add_column("#",         style="dim", width=4)
    tbl.add_column("Symbol",    style="bold cyan", width=10)
    tbl.add_column("Sector",    style="white", width=22)
    tbl.add_column("5D Stock",  justify="right", width=10)
    tbl.add_column("5D Sector", justify="right", width=10)
    tbl.add_column("RS (5D)",   justify="right", width=10)
    tbl.add_column("RS (10D)",  justify="right", width=10)
    tbl.add_column("RS (20D)",  justify="right", width=10)
    tbl.add_column("Signal",    width=20)

    for i, r in enumerate(top, 1):
        tbl.add_row(
            str(i),
            r["symbol"],
            r["sector"],
            _fmt(r["ret5"]),
            _fmt(r.get("sec5")),
            _fmt(r["rs5"]),
            _fmt(r.get("rs10")),
            _fmt(r.get("rs20")),
            _star(r["rs5"]),
        )

    console.print(tbl)

    # ── SECTOR SUMMARY ───────────────────────────────────────────────────────
    import pandas as pd
    df = pd.DataFrame(data)
    sec_summary = (
        df.groupby("sector")
        .apply(lambda g: pd.Series({
            "total":  len(g),
            "above":  (g["rs5"] > 0).sum(),
            "below":  (g["rs5"] < 0).sum(),
            "best_symbol": g.loc[g["rs5"].idxmax(), "symbol"] if len(g) > 0 else "",
            "best_rs5":    g["rs5"].max(),
        }))
        .reset_index()
        .sort_values("best_rs5", ascending=False)
    )

    stbl = Table(
        title="Sector Breadth — How Many Stocks Are Outperforming?",
        box=box.SIMPLE_HEAVY, show_lines=False,
        title_style="bold white"
    )
    stbl.add_column("Sector",       style="white", width=24)
    stbl.add_column("Above Sector", justify="right", width=14)
    stbl.add_column("Below Sector", justify="right", width=14)
    stbl.add_column("Best Stock",   style="cyan",  width=12)
    stbl.add_column("Best RS",      justify="right", width=10)

    for _, row in sec_summary.iterrows():
        above_pct = int(row["above"] / max(row["total"],1) * 100)
        stbl.add_row(
            str(row["sector"]),
            f'[green]{int(row["above"])}/{int(row["total"])}  ({above_pct}%)[/]',
            f'[red]{int(row["below"])}/{int(row["total"])}[/]',
            str(row["best_symbol"]),
            _fmt(row["best_rs5"]),
        )

    console.print(stbl)

    # ── BOTTOM LAGGARDS ──────────────────────────────────────────────────────
    if bot:
        btbl = Table(
            title="Bottom Laggards (Underperforming their sector most)",
            box=box.SIMPLE_HEAVY, show_lines=False,
            title_style="bold white"
        )
        btbl.add_column("Symbol",   style="bold red", width=10)
        btbl.add_column("Sector",   style="white",    width=22)
        btbl.add_column("5D Stock", justify="right",  width=10)
        btbl.add_column("RS (5D)",  justify="right",  width=10)
        for r in bot:
            btbl.add_row(
                r["symbol"], r["sector"],
                _fmt(r["ret5"]), _fmt(r["rs5"])
            )
        console.print(btbl)

    console.print(
        f"\\n  [bold green]Best RS stock:[/] {data[0]['symbol']} "
        f"(+{data[0]['rs5']:.2f}% vs sector)"
    )
    console.print(
        f"  [bold red]Worst RS stock:[/] {data[-1]['symbol']} "
        f"({data[-1]['rs5']:.2f}% vs sector)"
    )
'''

# ── 2. PATCH ─────────────────────────────────────────────────────────────────

def patch():
    if not os.path.exists(SCANNER):
        print(f"ERROR: {SCANNER} not found — run from project root.")
        return

    shutil.copy(SCANNER, BACKUP)
    print(f"Backed up → {BACKUP}")

    with open(SCANNER, encoding="utf-8") as f:
        src = f.read()

    # Insert functions before the main() guard
    anchor = 'if __name__ == "__main__":'
    if anchor not in src:
        print("ERROR: could not find main() anchor.")
        return
    src = src.replace(anchor, RS_FUNCTIONS + "\n\n" + anchor, 1)

    # Add --rs CLI arg (insert after last add_argument line)
    arg_anchor = "parser.add_argument('--heatmap'"
    if arg_anchor in src:
        src = src.replace(
            arg_anchor,
            "parser.add_argument('--rs',          action='store_true', help='Relative strength vs sector')\n    " + arg_anchor
        )
    else:
        # fallback: find any add_argument line
        src = re.sub(
            r"(parser\.add_argument\('--sector-trend'[^\n]*\n)",
            r"\1    parser.add_argument('--rs', action='store_true', help='Relative strength vs sector')\n",
            src
        )

    # Add dispatch in main() — after heatmap call
    heatmap_call = "analyze_sector_heatmap()"
    if heatmap_call in src:
        src = src.replace(
            heatmap_call,
            heatmap_call + "\n    elif args.rs:\n        analyze_relative_strength()"
        )
    else:
        # fallback after sector_trend
        src = src.replace(
            "analyze_sector_trend()",
            "analyze_sector_trend()\n    elif args.rs:\n        analyze_relative_strength()"
        )

    with open(SCANNER, "w", encoding="utf-8") as f:
        f.write(src)
    print("✓ Inserted _calc_relative_strength, analyze_relative_strength")
    print("✓ Added --rs CLI arg")
    print("✓ Added analyze_relative_strength() call in main()")

    # Update launch_nepse.bat
    bat = "launch_nepse.bat"
    if os.path.exists(bat):
        with open(bat, encoding="utf-8") as f:
            bc = f.read()
        if "--rs" not in bc:
            bc = bc.replace(
                'if "%choice%"=="7"  python nepse_scanner.py --sector & goto AGAIN',
                'if "%choice%"=="7"  python nepse_scanner.py --sector & goto AGAIN\nif "%choice%"=="7r" python nepse_scanner.py --rs & goto AGAIN'
            )
            with open(bat, "w", encoding="utf-8") as f:
                f.write(bc)
            print("✓ launch_nepse.bat: added 7r for --rs")

    print()
    print("✓ nepse_scanner.py patched successfully!")
    print()
    print("Test with:")
    print("  python nepse_scanner.py --rs")

if __name__ == "__main__":
    patch()
