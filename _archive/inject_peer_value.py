"""
inject_peer_value.py
Run once: python inject_peer_value.py

Replaces --value with a new peer comparison screen:
  python nepse_scanner.py --value
  python nepse_scanner.py --value Hydropower
  python nepse_scanner.py --value "Commercial Bank"

Shows all stocks per sector with:
  Float%  Book Value  Last Price  PB  Upside  Verdict
Sorted by PB ratio so cheapest shows first.
"""
import os, sys

SCANNER = "nepse_scanner.py"

NEW_VALUE_FUNC = [
    "",
    "# ── --value  (peer comparison by sector) ─────────────────────────────────────",
    "def analyze_value(filter_sector=None):",
    "    import sqlite3, pandas as pd",
    "    from rich.table import Table",
    "    from rich import box",
    "    from nepse import Nepse",
    "    import warnings; warnings.filterwarnings('ignore')",
    "",
    "    console.rule('[bold cyan]Sector Peer Value Screen[/]')",
    "    console.print('[dim]Comparing Float%, Book Value, Market Price within each sector[/]')",
    "    console.print('[dim]Lower PB vs peers = relatively undervalued[/]')",
    "    console.print()",
    "",
    "    conn = sqlite3.connect('nepse_market_data.db')",
    "",
    "    # Get fundamentals",
    "    df = pd.read_sql_query(",
    "        'SELECT f.symbol, f.sector, f.book_value_per_share, f.pe_ratio, f.pb_ratio, f.roe, f.eps'",
    "        ' FROM fundamentals f WHERE f.book_value_per_share > 0 ORDER BY f.sector, f.symbol',",
    "        conn",
    "    )",
    "",
    "    # Get latest price from stock_prices",
    "    prices = pd.read_sql_query(",
    "        'SELECT sp.symbol, sp.close as ltp, sp.date'",
    "        ' FROM stock_prices sp'",
    "        ' INNER JOIN (SELECT symbol, MAX(date) as maxd FROM stock_prices GROUP BY symbol) mx'",
    "        ' ON sp.symbol=mx.symbol AND sp.date=mx.maxd',",
    "        conn",
    "    )",
    "    conn.close()",
    "",
    "    if df.empty:",
    "        console.print('[yellow]No fundamental data found.[/]')",
    "        return",
    "",
    "    # Merge price into fundamentals",
    "    df = df.merge(prices[['symbol','ltp','date']], on='symbol', how='left')",
    "    df['sector'] = df['sector'].apply(_norm_sector)",
    "",
    "    # Recalculate PB from live price / book value",
    "    df['pb_live'] = df.apply(lambda r: r['ltp']/r['book_value_per_share'] if r['ltp'] and r['book_value_per_share'] and r['book_value_per_share'] > 0 else None, axis=1)",
    "",
    "    # Fetch float data from NEPSE API for all symbols (cached in session)",
    "    console.print('[dim]Fetching float data from NEPSE API...[/]')",
    "    n = Nepse(); n.setTLSVerification(False)",
    "    float_cache = {}",
    "    symbols = df['symbol'].tolist()",
    "    for i, sym in enumerate(symbols):",
    "        try:",
    "            d = n.getCompanyDetails(sym)",
    "            if isinstance(d, dict):",
    "                float_cache[sym] = {",
    "                    'pub_pct':    d.get('publicPercentage', 0),",
    "                    'pub_shares': d.get('publicShares', 0),",
    "                    'promo_pct':  d.get('promoterPercentage', 0),",
    "                }",
    "        except Exception:",
    "            float_cache[sym] = {'pub_pct': None, 'pub_shares': None, 'promo_pct': None}",
    "        if (i+1) % 20 == 0:",
    "            console.print(f'[dim]  Fetched {i+1}/{len(symbols)}...[/]')",
    "",
    "    df['pub_pct']    = df['symbol'].map(lambda s: float_cache.get(s, {}).get('pub_pct'))",
    "    df['pub_shares'] = df['symbol'].map(lambda s: float_cache.get(s, {}).get('pub_shares'))",
    "    df['promo_pct']  = df['symbol'].map(lambda s: float_cache.get(s, {}).get('promo_pct'))",
    "",
    "    # Filter sector if requested",
    "    sectors = df['sector'].unique()",
    "    if filter_sector:",
    "        fs = filter_sector.lower()",
    "        sectors = [s for s in sectors if fs in s.lower()]",
    "        if not sectors:",
    "            console.print(f'[yellow]Sector \"{filter_sector}\" not found.[/]')",
    "            console.print(f'[dim]Available: {list(df[\"sector\"].unique())}[/]')",
    "            return",
    "",
    "    for sec in sorted(sectors):",
    "        sec_df = df[df['sector'] == sec].copy()",
    "        if len(sec_df) < 2:",
    "            continue",
    "",
    "        # Sort by pb_live ascending (cheapest first)",
    "        sec_df = sec_df.sort_values('pb_live', ascending=True, na_position='last')",
    "",
    "        # Sector stats",
    "        med_pb  = sec_df['pb_live'].median()",
    "        med_bv  = sec_df['book_value_per_share'].median()",
    "        med_ltp = sec_df['ltp'].median()",
    "",
    "        title = f'[bold white]{sec}[/]  [dim]({len(sec_df)} stocks  |  median PB:{med_pb:.1f}x  BV:Rs{med_bv:.0f}  Price:Rs{med_ltp:.0f})[/]' if med_pb else f'[bold white]{sec}[/]'",
    "",
    "        t = Table(title=title, box=box.SIMPLE_HEAVY, border_style='cyan',",
    "                  title_style='bold cyan', show_lines=False)",
    "        t.add_column('Symbol',    width=10, style='bold white')",
    "        t.add_column('Price',     width=10, justify='right')",
    "        t.add_column('Book Val',  width=10, justify='right')",
    "        t.add_column('PB',        width=8,  justify='right')",
    "        t.add_column('Float%',    width=9,  justify='right')",
    "        t.add_column('Promoter%', width=11, justify='right')",
    "        t.add_column('ROE',       width=8,  justify='right')",
    "        t.add_column('Verdict',   width=32)",
    "",
    "        for _, r in sec_df.iterrows():",
    "            ltp    = r['ltp']",
    "            bv     = r['book_value_per_share']",
    "            pb     = r['pb_live']",
    "            roe    = r['roe']",
    "            fpct   = r['pub_pct']",
    "            ppct   = r['promo_pct']",
    "            fshares= r['pub_shares']",
    "",
    "            # PB color",
    "            if pb is None:   pb_c = 'dim'",
    "            elif pb < 1.0:   pb_c = 'bold green'",
    "            elif med_pb and pb < med_pb * 0.8: pb_c = 'green'",
    "            elif med_pb and pb < med_pb:       pb_c = 'yellow'",
    "            else:            pb_c = 'white'",
    "",
    "            # Float color",
    "            if fpct is None:  f_c = 'dim'",
    "            elif fpct < 25:   f_c = 'bold green'",
    "            elif fpct < 40:   f_c = 'yellow'",
    "            else:             f_c = 'white'",
    "",
    "            roe_c = 'green' if roe and roe > 15 else 'yellow' if roe and roe > 8 else 'red' if roe and roe < 5 else 'white'",
    "",
    "            # Verdict",
    "            tags = []",
    "            if pb is not None and pb < 1.0:",
    "                tags.append('[bold green]BELOW BOOK VALUE[/]')",
    "            elif med_pb and pb and pb < med_pb * 0.8:",
    "                tags.append('[green]Cheap vs peers[/]')",
    "            if fpct and fpct < 25:",
    "                tags.append('[green]Low float[/]')",
    "            if roe and roe > 15:",
    "                tags.append('[green]Strong ROE[/]')",
    "            if ppct and ppct > 60:",
    "                tags.append('[yellow]High promoter[/]')",
    "            if not tags:",
    "                if med_pb and pb and pb > med_pb * 1.2:",
    "                    tags.append('[dim]Expensive vs peers[/]')",
    "                else:",
    "                    tags.append('[dim]Average[/]')",
    "            verdict = ' | '.join(tags)",
    "",
    "            fshares_str = f'[{f_c}]{fpct:.1f}%[/]' if fpct else '[dim]N/A[/]'",
    "            ppct_str    = f'[red]{ppct:.1f}%[/]' if ppct and ppct > 60 else f'{ppct:.1f}%' if ppct else '[dim]N/A[/]'",
    "",
    "            t.add_row(",
    "                r['symbol'],",
    "                f'Rs {ltp:,.0f}'  if ltp else '[dim]N/A[/]',",
    "                f'Rs {bv:,.0f}'   if bv  else '[dim]N/A[/]',",
    "                f'[{pb_c}]{pb:.2f}x[/]' if pb else '[dim]N/A[/]',",
    "                fshares_str,",
    "                ppct_str,",
    "                f'[{roe_c}]{roe:.1f}%[/]' if roe else '[dim]N/A[/]',",
    "                verdict,",
    "            )",
    "        console.print(t)",
    "",
    "        # Top pick in sector",
    "        best = sec_df[sec_df['pb_live'].notna()].head(1)",
    "        if not best.empty:",
    "            b = best.iloc[0]",
    "            if b['pb_live'] and (med_pb is None or b['pb_live'] < med_pb):",
    "                console.print(f'  [bold green]★ Best value in {sec}: {b[\"symbol\"]} — PB {b[\"pb_live\"]:.2f}x, Price Rs {b[\"ltp\"]:,.0f}, Book Rs {b[\"book_value_per_share\"]:,.0f}[/]')",
    "        console.print()",
    "",
    "    console.print('[dim]PB < 1.0 = trading below book value (green). Sorted cheapest first within each sector.[/]')",
    "",
]

def patch():
    if not os.path.exists(SCANNER):
        print(f"ERROR: {SCANNER} not found"); sys.exit(1)

    with open(SCANNER, encoding='utf-8') as f:
        lines = f.readlines()

    src = ''.join(lines)

    # Check already patched with new version
    if 'Sector Peer Value Screen' in src:
        print("Already patched with peer value screen.")
        return

    # Backup
    backup = SCANNER.replace('.py', '_pre_peervalue.py')
    with open(backup, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"Backup -> {backup}")

    # Find and replace old analyze_value function
    # Find start
    start_marker = "# ── --value"
    end_marker   = "# ── --float SYMBOL"

    start_idx = next((i for i, l in enumerate(lines) if start_marker in l and 'peer' not in l), None)
    end_idx   = next((i for i, l in enumerate(lines) if end_marker in l), None)

    if start_idx is None or end_idx is None:
        print(f"Could not find old --value function (start:{start_idx} end:{end_idx})")
        print("Injecting new function before --float instead...")
        # Just inject before --float
        end_idx = next((i for i, l in enumerate(lines) if end_marker in l), None)
        if end_idx is None:
            print("ERROR: cannot find injection point"); sys.exit(1)
        new_lines = [l + '\n' for l in NEW_VALUE_FUNC]
        lines = lines[:end_idx] + new_lines + lines[end_idx:]
    else:
        # Replace old function with new
        new_lines = [l + '\n' for l in NEW_VALUE_FUNC]
        lines = lines[:start_idx] + new_lines + lines[end_idx:]
        print("Old --value replaced with peer comparison version")

    # Update argparse: --value needs nargs='?' to accept optional sector name
    new_lines_out = []
    for line in lines:
        if "--value" in line and "action='store_true'" in line:
            line = line.replace(
                "action='store_true', help='Undervalued stocks by sector'",
                "nargs='?', const='ALL', metavar='SECTOR', help='Peer value screen e.g. --value or --value Hydropower'"
            )
        new_lines_out.append(line)
    lines = new_lines_out
    print("Argparse updated")

    # Update dispatch: --value now passes sector arg
    new_lines_out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'elif args.value:' in line:
            new_lines_out.append('    elif args.value:\n')
            new_lines_out.append('        sector_filter = None if args.value == "ALL" else args.value\n')
            new_lines_out.append('        analyze_value(sector_filter)\n')
            new_lines_out.append('        console.print()\n')
            # skip old dispatch lines for value
            i += 1
            while i < len(lines) and (lines[i].startswith('        ') or lines[i].strip() == ''):
                if 'analyze_value' in lines[i] or lines[i].strip() == '':
                    i += 1
                else:
                    break
            continue
        new_lines_out.append(line)
        i += 1
    lines = new_lines_out
    print("Dispatch updated")

    with open(SCANNER, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"{SCANNER} saved\n")

    # Update bat: add sector filter option note
    bat = "launch_nepse.bat"
    if os.path.exists(bat):
        with open(bat, encoding='utf-8') as f:
            content = f.read()
        content = content.replace(
            'if "%choice%"=="29" python nepse_scanner.py --value & goto AGAIN',
            'if "%choice%"=="29" goto VALUE_SCREEN'
        )
        if ':CUSTOM_FUNDAMENTAL' in content and 'VALUE_SCREEN' not in content:
            content = content.replace(
                ':CUSTOM_FUNDAMENTAL',
                ':VALUE_SCREEN\n'
                'echo   Enter sector name or press Enter for ALL sectors:\n'
                'set /p vsector=  Sector (e.g. Hydropower, blank=all): \n'
                'if "%vsector%"=="" (python nepse_scanner.py --value) else (python nepse_scanner.py --value "%vsector%")\n'
                'goto AGAIN\n'
                ':CUSTOM_FUNDAMENTAL'
            )
            with open(bat, 'w', encoding='utf-8') as f:
                f.write(content)
            print("launch_nepse.bat updated")

if __name__ == '__main__':
    print("\n=== NEPSE Peer Value Injector ===\n")
    patch()
    print("=== Done! ===")
    print("\nUsage:")
    print("  python nepse_scanner.py --value              (all sectors)")
    print("  python nepse_scanner.py --value Hydropower   (one sector)")
    print("  python nepse_scanner.py --value 'Commercial Bank'\n")
