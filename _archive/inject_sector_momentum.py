"""
Injects sector momentum and heatmap features into nepse_scanner.py.
Run from project root:  python inject_sector_momentum.py
"""

import re
import shutil

SCANNER = "nepse_scanner.py"
BACKUP  = "nepse_scanner_pre_momentum.py"

# ── The two new functions ─────────────────────────────────────────────────────
NEW_FUNCTIONS = '''
# ── SECTOR MOMENTUM ───────────────────────────────────────────────────────────

def _load_sector_prices(db_path="nepse_market_data.db", days=35):
    """Load recent closing prices for all equity symbols."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"""
        SELECT sp.symbol, sp.date, sp.close
        FROM stock_prices sp
        JOIN companies c ON sp.symbol = c.symbol
        WHERE sp.date >= date('now', '-{days} days')
        ORDER BY sp.symbol, sp.date
    """, conn)
    conn.close()
    return df


def _sector_returns(prices_df, periods=(5, 10, 20)):
    """Compute equal-weighted sector returns over multiple periods."""
    if prices_df.empty:
        return {}

    import sqlite3
    conn = sqlite3.connect("nepse_market_data.db")
    cur = conn.cursor()
    cur.execute("SELECT symbol, sector FROM companies")
    sym_sector = {r[0]: r[1] for r in cur.fetchall()}
    conn.close()

    NAME_MAP = {
        "Hydro Power":                  "Hydropower",
        "Commercial Banks":             "Commercial Banks",
        "Development Banks":            "Development Banks",
        "Finance":                      "Finance",
        "Microfinance":                 "Microfinance",
        "Life Insurance":               "Life Insurance",
        "Non Life Insurance":           "Non-Life Insurance",
        "Manufacturing And Processing": "Manufacturing",
        "Hotels And Tourism":           "Hotels",
        "Investment":                   "Investment",
        "Tradings":                     "Trading",
        "Others":                       "Others",
    }

    prices_df = prices_df.copy()
    prices_df["sector"] = prices_df["symbol"].map(
        lambda s: NAME_MAP.get(sym_sector.get(s, ""), "Others")
    )
    prices_df = prices_df[prices_df["sector"] != ""]

    pivot = prices_df.pivot_table(
        index="date", columns="symbol", values="close", aggfunc="last"
    ).sort_index()

    if pivot.empty or len(pivot) < 2:
        return {}

    results = {}
    for sector in prices_df["sector"].unique():
        syms     = prices_df[prices_df["sector"] == sector]["symbol"].unique()
        sec_piv  = pivot[[s for s in syms if s in pivot.columns]].dropna(how="all")
        if sec_piv.empty:
            continue

        sector_results = {"stocks": len(sec_piv.columns)}
        for period in periods:
            if len(sec_piv) < period + 1:
                sector_results[period] = None
                continue
            window      = sec_piv.iloc[-(period + 1):]
            start       = window.iloc[0]
            end         = window.iloc[-1]
            valid       = (start > 0) & (end > 0)
            if valid.sum() < 2:
                sector_results[period] = None
                continue
            returns = (end[valid] - start[valid]) / start[valid] * 100
            sector_results[period] = float(returns.mean())

        results[sector] = sector_results

    return results


def _momentum_label(r5, r10, r20):
    """Classify momentum from multi-period returns."""
    valid = [r for r in (r5, r10, r20) if r is not None]
    if not valid:
        return "No data       -", "dim"
    avg         = sum(valid) / len(valid)
    accelerating = (r5 is not None and r10 is not None and r5 > r10 / 2)
    if avg > 2.0 and accelerating:
        return "Strong uptrend  ↑↑", "bold green"
    elif avg > 0.5:
        return "Heating up      ↑",  "green"
    elif avg > -0.5:
        return "Neutral         →",  "dim white"
    elif avg > -2.0:
        return "Cooling down    ↓",  "red"
    else:
        return "Strong downtrend ↓↓","bold red"


def analyze_sector_trend(db_path="nepse_market_data.db"):
    """--sector-trend: 5/10/20 day sector momentum table."""
    console.print(Rule("[bold cyan]Sector Momentum[/bold cyan]", style="cyan"))
    console.print("[dim]Multi-period sector performance — spot rotation early[/dim]\\n")

    with console.status("[cyan]Loading price history...[/cyan]"):
        prices_df = _load_sector_prices(db_path)

    if prices_df.empty:
        console.print("[red]No price data found.[/red]")
        return

    with console.status("[cyan]Computing sector returns...[/cyan]"):
        sector_data = _sector_returns(prices_df)

    if not sector_data:
        console.print("[red]Could not compute sector returns.[/red]")
        return

    sorted_sectors = sorted(
        sector_data.items(),
        key=lambda x: x[1].get(5) or -999,
        reverse=True
    )

    t = Table(
        title="Sector Momentum (Equal-Weighted)",
        box=box.ROUNDED, border_style="cyan", header_style="bold cyan",
    )
    t.add_column("Sector",   min_width=22, style="bold white")
    t.add_column("5D",       width=10, justify="right")
    t.add_column("10D",      width=10, justify="right")
    t.add_column("20D",      width=10, justify="right")
    t.add_column("Stocks",   width=8,  justify="center", style="dim")
    t.add_column("Momentum", width=26)

    def fmt_ret(v):
        if v is None:
            return Text("N/A", style="dim")
        return Text(f"{v:+.2f}%", style="green" if v > 0 else "red" if v < 0 else "dim")

    for sector, d in sorted_sectors:
        r5, r10, r20 = d.get(5), d.get(10), d.get(20)
        label, style = _momentum_label(r5, r10, r20)
        t.add_row(sector, fmt_ret(r5), fmt_ret(r10), fmt_ret(r20),
                  str(d.get("stocks", 0)), Text(label, style=style))

    console.print(t)
    console.print()

    top = sorted_sectors[0]
    bot = sorted_sectors[-1]
    if top[1].get(5) is not None:
        console.print(f"  [green]Strongest:[/green] {top[0]}  ({top[1].get(5):+.2f}% / 5d)")
    if bot[1].get(5) is not None:
        console.print(f"  [red]Weakest:  [/red] {bot[0]}  ({bot[1].get(5):+.2f}% / 5d)")
    console.print()


def analyze_sector_heatmap(db_path="nepse_market_data.db"):
    """--heatmap: color-coded sector heatmap."""
    console.print(Rule("[bold cyan]Sector Heatmap[/bold cyan]", style="cyan"))
    console.print("[dim]Where heat is building across timeframes[/dim]\\n")

    with console.status("[cyan]Loading data...[/cyan]"):
        prices_df = _load_sector_prices(db_path)

    if prices_df.empty:
        console.print("[red]No price data.[/red]")
        return

    with console.status("[cyan]Computing returns...[/cyan]"):
        sector_data = _sector_returns(prices_df)

    if not sector_data:
        console.print("[red]Could not compute returns.[/red]")
        return

    def heat(v):
        if v is None:
            return "dim", "  N/A "
        s = f"{v:+.1f}%"
        if v >= 2.0:   return "bold green", s
        elif v >= 0.5: return "green",      s
        elif v >= -0.5:return "dim white",  s
        elif v >= -2.0:return "red",        s
        else:          return "bold red",   s

    sorted_sectors = sorted(
        sector_data.items(),
        key=lambda x: x[1].get(5) or -999,
        reverse=True
    )

    t = Table(
        title="Sector Heatmap",
        box=box.SIMPLE_HEAVY, border_style="cyan",
        header_style="bold cyan", show_lines=True,
    )
    t.add_column("Sector", min_width=22, style="bold white")
    t.add_column("5D",     width=10, justify="center")
    t.add_column("10D",    width=10, justify="center")
    t.add_column("20D",    width=10, justify="center")
    t.add_column("Heat Bar (20D avg)", width=22)

    for sector, d in sorted_sectors:
        r5, r10, r20 = d.get(5), d.get(10), d.get(20)
        c5,  v5  = heat(r5)
        c10, v10 = heat(r10)
        c20, v20 = heat(r20)

        valid = [r for r in (r5, r10, r20) if r is not None]
        avg   = sum(valid) / len(valid) if valid else 0
        filled = int(min(max(round((avg + 5) / 10 * 12), 0), 12))
        bar    = "█" * filled + "░" * (12 - filled)
        bar_style = "bold green" if avg > 1 else "bold red" if avg < -1 else "dim"

        t.add_row(
            sector,
            Text(v5,  style=c5),
            Text(v10, style=c10),
            Text(v20, style=c20),
            Text(bar, style=bar_style),
        )

    console.print(t)
    console.print()

'''

# ── Patch the file ─────────────────────────────────────────────────────────────
shutil.copy(SCANNER, BACKUP)
print(f"Backed up → {BACKUP}")

with open(SCANNER, encoding="utf-8") as f:
    content = f.read()

# 1. Insert new functions before the analyze_sector_rotation function
insert_marker = "def analyze_sector_rotation("
if insert_marker in content:
    content = content.replace(insert_marker, NEW_FUNCTIONS + "\n" + insert_marker, 1)
    print("✓ Inserted _load_sector_prices, _sector_returns, analyze_sector_trend, analyze_sector_heatmap")
else:
    print("⚠ Could not find analyze_sector_rotation — appending functions at end")
    content += "\n" + NEW_FUNCTIONS

# 2. Add CLI arguments
argparse_marker = "p.add_argument('--sector',"
if argparse_marker in content:
    content = content.replace(
        argparse_marker,
        "p.add_argument('--sector-trend', action='store_true', help='Sector momentum 5/10/20d')\n"
        "    p.add_argument('--heatmap',      action='store_true', help='Sector heatmap')\n"
        "    " + argparse_marker,
        1
    )
    print("✓ Added --sector-trend and --heatmap CLI args")
else:
    print("⚠ Could not find --sector argparse — add manually:")
    print("    p.add_argument('--sector-trend', action='store_true')")
    print("    p.add_argument('--heatmap',      action='store_true')")

# 3. Add calls in main()
call_marker = "if args.sector:"
if call_marker in content:
    content = content.replace(
        call_marker,
        "if args.sector_trend:\n        analyze_sector_trend()\n"
        "    if args.heatmap:\n        analyze_sector_heatmap()\n"
        "    " + call_marker,
        1
    )
    print("✓ Added analyze_sector_trend() and analyze_sector_heatmap() calls in main()")
else:
    print("⚠ Could not find 'if args.sector:' — add calls manually in main()")

# 4. Add menu items to launch_nepse.bat
with open(SCANNER, "w", encoding="utf-8") as f:
    f.write(content)

print("\n✓ nepse_scanner.py patched successfully!")
print("\nTest with:")
print("  python nepse_scanner.py --sector-trend")
print("  python nepse_scanner.py --heatmap")

# 5. Patch launch_nepse.bat to add menu options
try:
    with open("launch_nepse.bat", encoding="utf-8") as f:
        bat = f.read()

    if "--sector-trend" not in bat:
        # Add to menu display
        bat = bat.replace(
            "echo   7.  Sector Rotation",
            "echo   7.  Sector Rotation\n"
            "echo   7t. Sector Trend  (5/10/20d momentum)\n"
            "echo   7h. Sector Heatmap"
        )
        # Add to choice handler
        bat = bat.replace(
            'if "%choice%"=="7"  python nepse_scanner.py --sector & goto AGAIN',
            'if "%choice%"=="7"  python nepse_scanner.py --sector & goto AGAIN\n'
            'if "%choice%"=="7t" python nepse_scanner.py --sector-trend & goto AGAIN\n'
            'if "%choice%"=="7h" python nepse_scanner.py --heatmap & goto AGAIN'
        )
        with open("launch_nepse.bat", "w", encoding="utf-8") as f:
            f.write(bat)
        print("✓ launch_nepse.bat updated with 7t and 7h menu options")
    else:
        print("  launch_nepse.bat already has sector-trend")

except Exception as e:
    print(f"  Could not patch launch_nepse.bat: {e}")
