#!/usr/bin/env python3
"""
inject_portfolio.py
Adds --portfolio, --corr, and --size commands to nepse_scanner.py
"""
import re, shutil, os

TARGET = 'nepse_scanner.py'
BACKUP = 'nepse_scanner_pre_portfolio.py'

shutil.copy(TARGET, BACKUP)
print(f'Backed up → {BACKUP}')

with open(TARGET, encoding='utf-8') as f:
    src = f.read()

# ── 1. FUNCTIONS ────────────────────────────────────────────────────────────

FUNCTIONS = '''

# ════════════════════════════════════════════════════════════════════════════
#  PHASE 5 — PORTFOLIO INTELLIGENCE
# ════════════════════════════════════════════════════════════════════════════

def _get_returns(symbols, days=60):
    """Return a dict {symbol: pd.Series of daily pct returns} for the last N days."""
    import sqlite3, pandas as pd
    conn = sqlite3.connect('nepse_market_data.db')
    placeholders = ','.join('?' * len(symbols))
    df = pd.read_sql_query(f"""
        SELECT symbol, date, close FROM stock_prices
        WHERE symbol IN ({placeholders})
          AND date >= date('now', '-{days} days')
        ORDER BY symbol, date
    """, conn, params=symbols)
    conn.close()
    if df.empty:
        return {}
    pivot = df.pivot(index='date', columns='symbol', values='close')
    returns = pivot.pct_change().dropna()
    return {col: returns[col].dropna() for col in returns.columns}


def analyze_portfolio(symbols):
    """--portfolio SYM1 SYM2 ... — position sizing + correlation + diversification."""
    import sqlite3, math
    import pandas as pd
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()
    console.print()
    console.print(f"[bold cyan]{'─'*30} Portfolio Intelligence {'─'*30}[/bold cyan]")

    if not symbols:
        console.print("[yellow]Usage: --portfolio AKJCL BUNGAL BHCL[/yellow]")
        return

    symbols = [s.upper() for s in symbols]

    # ── Price data ──────────────────────────────────────────────────────────
    returns_map = _get_returns(symbols, days=90)
    missing = [s for s in symbols if s not in returns_map]
    if missing:
        console.print(f"[yellow]No price data for: {', '.join(missing)}[/yellow]")
        symbols = [s for s in symbols if s in returns_map]
    if not symbols:
        console.print("[red]No valid symbols.[/red]")
        return

    # ── Volatility & stats per symbol ───────────────────────────────────────
    import numpy as np
    stats = {}
    for sym in symbols:
        r = returns_map[sym]
        vol   = r.std() * math.sqrt(252) * 100          # annualised vol %
        ret5  = ((1 + r.tail(5)).prod() - 1) * 100      # 5d return
        ret20 = ((1 + r.tail(20)).prod() - 1) * 100     # 20d return
        sharpe = (r.mean() / r.std() * math.sqrt(252)) if r.std() > 0 else 0
        stats[sym] = dict(vol=vol, ret5=ret5, ret20=ret20, sharpe=sharpe)

    # ── Inverse-volatility weights ───────────────────────────────────────────
    inv_vols = {s: 1 / max(stats[s]['vol'], 0.1) for s in symbols}
    total_inv = sum(inv_vols.values())
    weights = {s: inv_vols[s] / total_inv * 100 for s in symbols}

    # ── Correlation matrix ───────────────────────────────────────────────────
    df_ret = pd.DataFrame({s: returns_map[s] for s in symbols}).dropna()
    corr = df_ret.corr() if len(symbols) > 1 else None

    # Average pairwise correlation → diversification score
    if corr is not None and len(symbols) > 1:
        pairs = []
        for i, a in enumerate(symbols):
            for j, b in enumerate(symbols):
                if j > i:
                    pairs.append(corr.loc[a, b])
        avg_corr = np.mean(pairs)
        div_score = max(0, int((1 - avg_corr) * 100))
    else:
        avg_corr = 0
        div_score = 100

    # ── Table 1: Per-stock stats + suggested weight ──────────────────────────
    t1 = Table(title="Position Sizing (Inverse-Volatility Weighted)",
               box=box.SIMPLE_HEAD, show_lines=False)
    t1.add_column("Symbol",   style="bold white")
    t1.add_column("Ann.Vol%", justify="right")
    t1.add_column("5D Ret%",  justify="right")
    t1.add_column("20D Ret%", justify="right")
    t1.add_column("Sharpe",   justify="right")
    t1.add_column("Weight%",  justify="right", style="bold cyan")
    t1.add_column("Rs 1L →",  justify="right", style="bold green")

    for sym in sorted(symbols, key=lambda s: -weights[s]):
        s = stats[sym]
        w = weights[sym]
        color_5d  = "green" if s['ret5']  >= 0 else "red"
        color_20d = "green" if s['ret20'] >= 0 else "red"
        t1.add_row(
            sym,
            f"{s['vol']:.1f}%",
            f"[{color_5d}]{s['ret5']:+.1f}%[/{color_5d}]",
            f"[{color_20d}]{s['ret20']:+.1f}%[/{color_20d}]",
            f"{s['sharpe']:.2f}",
            f"{w:.1f}%",
            f"Rs {w*1000:.0f}",
        )
    console.print(t1)

    # ── Table 2: Correlation matrix ──────────────────────────────────────────
    if corr is not None and len(symbols) > 1:
        t2 = Table(title="Correlation Matrix (60-day returns)",
                   box=box.SIMPLE_HEAD, show_lines=False)
        t2.add_column("", style="bold white")
        for sym in symbols:
            t2.add_column(sym, justify="right")

        for a in symbols:
            row = [a]
            for b in symbols:
                v = corr.loc[a, b]
                if a == b:
                    row.append("[dim]  1.00[/dim]")
                elif v >= 0.8:
                    row.append(f"[red]{v:.2f}[/red]")
                elif v >= 0.5:
                    row.append(f"[yellow]{v:.2f}[/yellow]")
                else:
                    row.append(f"[green]{v:.2f}[/green]")
            t2.add_row(*row)
        console.print(t2)

    # ── Diversification score ────────────────────────────────────────────────
    if div_score >= 70:
        div_color = "green"
        div_label = "Well diversified"
    elif div_score >= 40:
        div_color = "yellow"
        div_label = "Moderate overlap"
    else:
        div_color = "red"
        div_label = "High overlap — consider swapping one stock"

    console.print(
        f"  Diversification Score: [{div_color}]{div_score}/100[/{div_color}]  "
        f"[dim]{div_label}  (avg pairwise corr: {avg_corr:.2f})[/dim]"
    )
    console.print()


def analyze_corr():
    """--corr — sector-level correlation heatmap across all stocks."""
    import sqlite3, math
    import pandas as pd, numpy as np
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()
    console.print()
    console.print(f"[bold cyan]{'─'*28} Sector Correlation Heatmap {'─'*28}[/bold cyan]")
    console.print("[dim]  How correlated are sectors? Red = move together, Green = independent[/dim]")
    console.print()

    conn = sqlite3.connect('nepse_market_data.db')

    # Get sector for each symbol
    sectors_df = pd.read_sql_query(
        "SELECT symbol, sector FROM companies WHERE sector IS NOT NULL", conn)
    sector_map = dict(zip(sectors_df.symbol, sectors_df.sector))

    # Get 60d returns for all symbols
    df = pd.read_sql_query("""
        SELECT symbol, date, close FROM stock_prices
        WHERE date >= date('now', '-75 days')
        ORDER BY symbol, date
    """, conn)
    conn.close()

    if df.empty:
        console.print("[red]No price data.[/red]")
        return

    pivot = df.pivot(index='date', columns='symbol', values='close')
    returns = pivot.pct_change().dropna()

    # Build sector returns as mean of member stocks
    sectors = sorted(set(sector_map.values()))
    sector_returns = {}
    for sec in sectors:
        members = [s for s in returns.columns if sector_map.get(s) == sec]
        if len(members) >= 3:
            sector_returns[sec] = returns[members].mean(axis=1)

    if len(sector_returns) < 2:
        console.print("[yellow]Not enough sector data.[/yellow]")
        return

    sec_df = pd.DataFrame(sector_returns).dropna()
    corr = sec_df.corr()
    sec_list = list(corr.columns)

    t = Table(box=box.SIMPLE_HEAD, show_lines=False)
    t.add_column("Sector", style="bold white", min_width=22)
    for s in sec_list:
        short = s[:10]
        t.add_column(short, justify="right", min_width=7)

    for a in sec_list:
        row = [a]
        for b in sec_list:
            v = corr.loc[a, b]
            if a == b:
                row.append("[dim] 1.00[/dim]")
            elif v >= 0.85:
                row.append(f"[red]{v:.2f}[/red]")
            elif v >= 0.60:
                row.append(f"[yellow]{v:.2f}[/yellow]")
            else:
                row.append(f"[green]{v:.2f}[/green]")
        t.add_row(*row)

    console.print(t)
    console.print(
        "  [green]Green < 0.60[/green]  [yellow]Yellow 0.60–0.85[/yellow]  "
        "[red]Red > 0.85 (highly correlated)[/red]"
    )
    console.print()


def analyze_size(symbol, capital):
    """--size SYM AMOUNT — volatility-adjusted position sizing."""
    import sqlite3, math
    import pandas as pd
    from rich.console import Console
    from rich import box
    from rich.table import Table

    console = Console()
    symbol = symbol.upper()
    console.print()
    console.print(f"[bold cyan]{'─'*30} Position Sizer: {symbol} {'─'*30}[/bold cyan]")

    conn = sqlite3.connect('nepse_market_data.db')
    df = pd.read_sql_query("""
        SELECT date, close, high, low FROM stock_prices
        WHERE symbol = ? AND date >= date('now', '-90 days')
        ORDER BY date
    """, conn, params=[symbol])
    conn.close()

    if df.empty or len(df) < 10:
        console.print(f"[red]No price data for {symbol}.[/red]")
        return

    ltp = df['close'].iloc[-1]
    returns = df['close'].pct_change().dropna()
    daily_vol = returns.std()
    ann_vol   = daily_vol * math.sqrt(252) * 100

    # ATR (14-day)
    df['tr'] = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift()).abs(),
        (df['low']  - df['close'].shift()).abs(),
    ], axis=1).max(axis=1)
    atr = df['tr'].tail(14).mean()

    # Risk-based sizing (1% account risk per trade, 2xATR stop)
    stop_distance = atr * 2
    risk_amt_1pct = capital * 0.01
    risk_amt_2pct = capital * 0.02
    shares_1pct = int(risk_amt_1pct / stop_distance) if stop_distance > 0 else 0
    shares_2pct = int(risk_amt_2pct / stop_distance) if stop_distance > 0 else 0
    cost_1pct = shares_1pct * ltp
    cost_2pct = shares_2pct * ltp

    # Kelly fraction (simplified)
    win_rate = (returns > 0).mean()
    avg_win  = returns[returns > 0].mean() if (returns > 0).any() else 0
    avg_loss = abs(returns[returns < 0].mean()) if (returns < 0).any() else 0.001
    kelly = win_rate - (1 - win_rate) / (avg_win / avg_loss) if avg_loss > 0 else 0
    kelly_pct = max(0, min(kelly * 100, 25))  # cap at 25%
    kelly_amt = capital * kelly_pct / 100
    kelly_shares = int(kelly_amt / ltp)

    t = Table(box=box.SIMPLE_HEAD, show_lines=False)
    t.add_column("Method",        style="bold white", min_width=28)
    t.add_column("Shares",        justify="right", style="bold cyan")
    t.add_column("Capital Used",  justify="right", style="bold green")
    t.add_column("% of Capital",  justify="right")

    t.add_row("1% Risk / 2×ATR stop",
              str(shares_1pct), f"Rs {cost_1pct:,.0f}", f"{cost_1pct/capital*100:.1f}%")
    t.add_row("2% Risk / 2×ATR stop",
              str(shares_2pct), f"Rs {cost_2pct:,.0f}", f"{cost_2pct/capital*100:.1f}%")
    t.add_row(f"Half-Kelly ({kelly_pct/2:.1f}%)",
              str(kelly_shares//2), f"Rs {kelly_shares//2*ltp:,.0f}",
              f"{kelly_shares//2*ltp/capital*100:.1f}%")

    console.print(t)
    console.print(
        f"  LTP: Rs {ltp:.1f}  |  ATR(14): Rs {atr:.1f}  |  "
        f"Ann.Vol: {ann_vol:.1f}%  |  Stop level: Rs {ltp - stop_distance:.1f}"
    )
    console.print(
        f"  [dim]Capital: Rs {capital:,.0f}  |  "
        f"Win rate(60d): {win_rate*100:.0f}%[/dim]"
    )
    console.print()
'''

# ── 2. INSERT FUNCTIONS before the last def main() ──────────────────────────
main_match = list(re.finditer(r'^def main\(\)', src, re.MULTILINE))
if not main_match:
    print('ERROR: could not find def main()')
    exit(1)

insert_pos = main_match[-1].start()
src = src[:insert_pos] + FUNCTIONS + '\n' + src[insert_pos:]
print('✓ Inserted analyze_portfolio, analyze_corr, analyze_size')

# ── 3. ADD argparse arguments ────────────────────────────────────────────────
old_legend = "    p.add_argument('--legend',      action='store_true')"
new_legend = (
    "    p.add_argument('--legend',      action='store_true')\n"
    "    p.add_argument('--portfolio',   nargs='+', metavar='SYMBOL', help='Position sizing + correlation for a set of stocks')\n"
    "    p.add_argument('--corr',        action='store_true', help='Sector correlation heatmap')\n"
    "    p.add_argument('--size',        nargs=2, metavar=('SYMBOL','AMOUNT'), help='Volatility-adjusted sizing e.g. --size AKJCL 100000')"
)
if old_legend in src:
    src = src.replace(old_legend, new_legend)
    print('✓ Added --portfolio, --corr, --size CLI args')
else:
    print('WARNING: --legend line not found, args not added — add manually')

# ── 4. ADD dispatch in main() ────────────────────────────────────────────────
old_rs_dispatch = "elif args.rs:\n        analyze_relative_strength()"
new_rs_dispatch = (
    "elif args.rs:\n        analyze_relative_strength()\n"
    "    elif args.portfolio:\n        analyze_portfolio(args.portfolio)\n"
    "    elif args.corr:\n        analyze_corr()\n"
    "    elif args.size:\n        analyze_size(args.size[0], float(args.size[1]))"
)
if old_rs_dispatch in src:
    src = src.replace(old_rs_dispatch, new_rs_dispatch)
    print('✓ Added dispatch for --portfolio / --corr / --size')
else:
    print('WARNING: rs dispatch not found — adding after --week52 instead')
    old_w52 = "elif args.week52:\n        analyze_week52()"
    new_w52 = (
        "elif args.week52:\n        analyze_week52()\n"
        "    elif args.portfolio:\n        analyze_portfolio(args.portfolio)\n"
        "    elif args.corr:\n        analyze_corr()\n"
        "    elif args.size:\n        analyze_size(args.size[0], float(args.size[1]))"
    )
    if old_w52 in src:
        src = src.replace(old_w52, new_w52)
        print('✓ Added dispatch (via week52 fallback)')
    else:
        print('ERROR: could not find dispatch insertion point')

# ── 5. ADD launcher menu entries ─────────────────────────────────────────────
try:
    with open('launch_nepse.bat', encoding='utf-8') as f:
        bat = f.read()
    bat = bat.replace(
        'if "%choice%"=="0"  exit',
        (
            'if "%choice%"=="23" python nepse_scanner.py --corr\n'
            'if "%choice%"=="24" python nepse_scanner.py --portfolio %args%\n'
            'if "%choice%"=="0"  exit'
        )
    )
    with open('launch_nepse.bat', 'w', encoding='utf-8') as f:
        f.write(bat)
    print('✓ launch_nepse.bat: added 23=corr, 24=portfolio')
except FileNotFoundError:
    print('⚠ launch_nepse.bat not found — skipped')

# ── 6. WRITE ─────────────────────────────────────────────────────────────────
with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(src)

print()
print('✓ nepse_scanner.py patched successfully!')
print()
print('Test with:')
print('  python nepse_scanner.py --corr')
print('  python nepse_scanner.py --portfolio AKJCL BUNGAL BHCL')
print('  python nepse_scanner.py --size AKJCL 100000')
