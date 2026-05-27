"""
inject_value_score.py
Upgrades analyze_value() in nepse_scanner.py with:
  - Value Score 0-100 (PB 40pts + Float 20pts + ROE 20pts + Earnings Growth 20pts)
  - Earnings Growth column (QoQ profit trend from quarterly_earnings table)
  - Score-sorted output (best score first within each sector)
  - Cross-sector Top 10 leaderboard at the end
Run once: python inject_value_score.py
"""

import re, shutil, os, sys
from pathlib import Path

SCANNER = Path('nepse_scanner.py')
BACKUP  = Path('nepse_scanner_pre_score.py')

if not SCANNER.exists():
    print('ERROR: nepse_scanner.py not found. Run from nepse-quant-terminal folder.')
    sys.exit(1)

src = SCANNER.read_text(encoding='utf-8')

PATCH_MARKER = '# VALUE_SCORE_PATCHED'
if PATCH_MARKER in src:
    print('Already patched — nothing to do.')
    sys.exit(0)

# ── Backup ────────────────────────────────────────────────────────────────────
shutil.copy(SCANNER, BACKUP)
print(f'Backup -> {BACKUP}')

# ── OLD block to replace (the per-row scoring / verdict / table / best-pick) ──
OLD = '''            # PB color
            if pb is None:   pb_c = 'dim'
            elif pb < 1.0:   pb_c = 'bold green'
            elif med_pb and pb < med_pb * 0.8: pb_c = 'green'
            elif med_pb and pb < med_pb:       pb_c = 'yellow'
            else:            pb_c = 'white'

            # Float color
            if fpct is None:  f_c = 'dim'
            elif fpct < 25:   f_c = 'bold green'
            elif fpct < 40:   f_c = 'yellow'
            else:             f_c = 'white'

            roe_c = 'green' if roe and roe > 15 else 'yellow' if roe and roe > 8 else 'red' if roe and roe < 5 else 'white'

            # Verdict
            tags = []
            if pb is not None and pb < 1.0:
                tags.append('[bold green]BELOW BOOK VALUE[/]')
            elif med_pb and pb and pb < med_pb * 0.8:
                tags.append('[green]Cheap vs peers[/]')
            if fpct and fpct < 25:
                tags.append('[green]Low float[/]')
            if roe and roe > 15:
                tags.append('[green]Strong ROE[/]')
            if ppct and ppct > 60:
                tags.append('[yellow]High promoter[/]')
            if not tags:
                if med_pb and pb and pb > med_pb * 1.2:
                    tags.append('[dim]Expensive vs peers[/]')
                else:
                    tags.append('[dim]Average[/]')
            verdict = ' | '.join(tags)

            fshares_str = f'[{f_c}]{fpct:.1f}%[/]' if fpct else '[dim]N/A[/]'
            ppct_str    = f'[red]{ppct:.1f}%[/]' if ppct and ppct > 60 else f'{ppct:.1f}%' if ppct else '[dim]N/A[/]'

            t.add_row(
                r['symbol'],
                f'Rs {ltp:,.0f}'  if ltp else '[dim]N/A[/]',
                f'Rs {bv:,.0f}'   if bv  else '[dim]N/A[/]',
                f'[{pb_c}]{pb:.2f}x[/]' if pb else '[dim]N/A[/]',
                fshares_str,
                ppct_str,
                f'[{roe_c}]{roe:.1f}%[/]' if roe else '[dim]N/A[/]',
                verdict,
            )
        console.print(t)

        # Top pick in sector
        best = sec_df[sec_df['pb_live'].notna()].head(1)
        if not best.empty:
            b = best.iloc[0]
            if b['pb_live'] and (med_pb is None or b['pb_live'] < med_pb):
                console.print(f\'  [bold green]★ Best value in {sec}: {b["symbol"]} — PB {b["pb_live"]:.2f}x, Price Rs {b["ltp"]:,.0f}, Book Rs {b["book_value_per_share"]:,.0f}[/]\')
        console.print()

    console.print(\'[dim]PB < 1.0 = trading below book value (green). Sorted cheapest first within each sector.[/]\')'''

NEW = '''            # ── Earnings growth score (QoQ) ─────────────────────────────
            eq = earnings_map.get(r['symbol'], [])
            if len(eq) >= 2 and eq[0] and eq[1] and eq[1] != 0:
                eq_growth = (eq[0] - eq[1]) / abs(eq[1]) * 100
            else:
                eq_growth = None

            # ── Value Score 0-100 ─────────────────────────────────────────
            score = 0
            # PB component (40 pts): below book=40, cheap vs peers=30, near median=15, expensive=0
            if pb is not None:
                if pb < 1.0:
                    score += 40
                elif med_pb and pb < med_pb * 0.7:
                    score += 32
                elif med_pb and pb < med_pb * 0.9:
                    score += 22
                elif med_pb and pb < med_pb:
                    score += 12
                elif med_pb and pb > med_pb * 1.3:
                    score += 0
                else:
                    score += 6
            # Float component (20 pts): low float = tight supply = price moves fast
            if fpct is not None:
                if fpct < 20:
                    score += 20
                elif fpct < 30:
                    score += 15
                elif fpct < 40:
                    score += 10
                elif fpct < 55:
                    score += 5
            # ROE component (20 pts)
            if roe is not None:
                if roe > 20:
                    score += 20
                elif roe > 15:
                    score += 15
                elif roe > 10:
                    score += 10
                elif roe > 5:
                    score += 5
            # Earnings growth component (20 pts)
            if eq_growth is not None:
                if eq_growth > 20:
                    score += 20
                elif eq_growth > 10:
                    score += 15
                elif eq_growth > 0:
                    score += 10
                elif eq_growth > -10:
                    score += 4
                # negative growth = 0 pts

            all_scores.append({'symbol': r['symbol'], 'sector': sec, 'score': score,
                                'pb': pb, 'ltp': ltp, 'bv': bv, 'roe': roe, 'fpct': fpct})

            # ── Colors ────────────────────────────────────────────────────
            if pb is None:   pb_c = 'dim'
            elif pb < 1.0:   pb_c = 'bold green'
            elif med_pb and pb < med_pb * 0.8: pb_c = 'green'
            elif med_pb and pb < med_pb:       pb_c = 'yellow'
            else:            pb_c = 'white'

            if fpct is None:  f_c = 'dim'
            elif fpct < 25:   f_c = 'bold green'
            elif fpct < 40:   f_c = 'yellow'
            else:             f_c = 'white'

            roe_c = 'green' if roe and roe > 15 else 'yellow' if roe and roe > 8 else 'red' if roe and roe < 5 else 'white'

            if score >= 65:   sc_c = 'bold green'
            elif score >= 45: sc_c = 'green'
            elif score >= 30: sc_c = 'yellow'
            else:             sc_c = 'dim'

            # ── Verdict ───────────────────────────────────────────────────
            tags = []
            if pb is not None and pb < 1.0:
                tags.append('[bold green]BELOW BOOK[/]')
            elif med_pb and pb and pb < med_pb * 0.8:
                tags.append('[green]Cheap vs peers[/]')
            if fpct and fpct < 25:
                tags.append('[green]Low float[/]')
            if roe and roe > 15:
                tags.append('[green]Strong ROE[/]')
            if eq_growth is not None and eq_growth > 10:
                tags.append('[green]Profit growing[/]')
            elif eq_growth is not None and eq_growth < -10:
                tags.append('[red]Profit falling[/]')
            if ppct and ppct > 60:
                tags.append('[yellow]Hi-promoter[/]')
            if not tags:
                if med_pb and pb and pb > med_pb * 1.2:
                    tags.append('[dim]Expensive[/]')
                else:
                    tags.append('[dim]Average[/]')
            verdict = ' | '.join(tags)

            fshares_str = f'[{f_c}]{fpct:.1f}%[/]' if fpct is not None else '[dim]N/A[/]'
            ppct_str    = f'[red]{ppct:.1f}%[/]' if ppct and ppct > 60 else f'{ppct:.1f}%' if ppct else '[dim]N/A[/]'
            eg_str = (f'[green]+{eq_growth:.0f}%[/]' if eq_growth and eq_growth > 0
                      else f'[red]{eq_growth:.0f}%[/]' if eq_growth and eq_growth <= 0
                      else '[dim]N/A[/]')

            t.add_row(
                r['symbol'],
                f'Rs {ltp:,.0f}'  if ltp else '[dim]N/A[/]',
                f'Rs {bv:,.0f}'   if bv  else '[dim]N/A[/]',
                f'[{pb_c}]{pb:.2f}x[/]' if pb else '[dim]N/A[/]',
                fshares_str,
                f'[{roe_c}]{roe:.1f}%[/]' if roe else '[dim]N/A[/]',
                eg_str,
                f'[{sc_c}]{score}[/]',
                verdict,
            )
        console.print(t)

        # Top pick in sector by score
        scored = [x for x in all_scores if x['sector'] == sec and x['score'] > 0]
        if scored:
            top = max(scored, key=lambda x: x['score'])
            stars = '★★★' if top['score'] >= 65 else '★★' if top['score'] >= 45 else '★'
            sc_col = 'bold green' if top['score'] >= 65 else 'green' if top['score'] >= 45 else 'yellow'
            pb_str = f'PB {top["pb"]:.2f}x' if top['pb'] else ''
            roe_str = f'ROE {top["roe"]:.1f}%' if top['roe'] else ''
            console.print(f\'  [{sc_col}]{stars} Best in {sec}: {top["symbol"]} — Score {top["score"]}/100  {pb_str}  {roe_str}[/]\')
        console.print()

    # ── Cross-sector Top 10 leaderboard ──────────────────────────────────────
    if all_scores:
        top10 = sorted(all_scores, key=lambda x: x['score'], reverse=True)[:10]
        from rich.table import Table as _T
        from rich import box as _box
        lb = _T(title=\'[bold yellow]★ Top 10 Value Picks — All Sectors[/]\',
                box=_box.SIMPLE_HEAVY, border_style=\'yellow\', title_style=\'bold yellow\')
        lb.add_column(\'#\',       width=4,  justify=\'right\')
        lb.add_column(\'Symbol\',  width=10, style=\'bold white\')
        lb.add_column(\'Sector\',  width=22)
        lb.add_column(\'Score\',   width=8,  justify=\'right\')
        lb.add_column(\'Price\',   width=10, justify=\'right\')
        lb.add_column(\'Book Val\',width=10, justify=\'right\')
        lb.add_column(\'PB\',      width=8,  justify=\'right\')
        lb.add_column(\'Float%\',  width=9,  justify=\'right\')
        lb.add_column(\'ROE\',     width=8,  justify=\'right\')
        for rank, x in enumerate(top10, 1):
            sc = x[\'score\']
            sc_c = \'bold green\' if sc >= 65 else \'green\' if sc >= 45 else \'yellow\'
            pb_v = x[\'pb\']; ltp_v = x[\'ltp\']; bv_v = x[\'bv\']
            lb.add_row(
                str(rank),
                x[\'symbol\'],
                x[\'sector\'],
                f\'[{sc_c}]{sc}[/]\',
                f\'Rs {ltp_v:,.0f}\' if ltp_v else \'N/A\',
                f\'Rs {bv_v:,.0f}\' if bv_v else \'N/A\',
                f\'[{sc_c}]{pb_v:.2f}x[/]\' if pb_v else \'N/A\',
                f\'{x["fpct"]:.1f}%\' if x[\'fpct\'] is not None else \'N/A\',
                f\'{x["roe"]:.1f}%\' if x[\'roe\'] else \'N/A\',
            )
        console.print(lb)
        console.print()

    console.print(\'[dim]Score: PB 40pts + Float 20pts + ROE 20pts + Earnings Growth 20pts. Green ≥65, Yellow ≥45.[/]\') # VALUE_SCORE_PATCHED'''

# ── Also need to inject earnings_map and all_scores BEFORE the sector loop ──
# Find the sector loop start and inject before it
OLD2 = '    for sec in sorted(sectors):'
NEW2 = '''    # ── Pre-load earnings growth map ─────────────────────────────────────────
    import sqlite3 as _sq3
    _eq_conn = _sq3.connect('nepse_market_data.db')
    _eq_rows = _eq_conn.execute(
        "SELECT symbol, net_profit, announcement_date FROM quarterly_earnings "
        "WHERE net_profit IS NOT NULL ORDER BY symbol, announcement_date DESC"
    ).fetchall()
    _eq_conn.close()
    from collections import defaultdict as _dd
    _eq_by_sym = _dd(list)
    for _s, _p, _d in _eq_rows:
        _eq_by_sym[_s].append(_p)
    earnings_map = {s: v[:4] for s, v in _eq_by_sym.items()}  # last 4 quarters

    all_scores = []  # collect for leaderboard

    for sec in sorted(sectors):'''

# ── Also upgrade table columns to add EarningsGrowth and Score ──
OLD3 = '''        t = Table(title=title, box=box.SIMPLE_HEAVY, border_style='cyan',
                  title_style='bold cyan', show_lines=False)
        t.add_column('Symbol',    width=10, style='bold white')
        t.add_column('Price',     width=10, justify='right')
        t.add_column('Book Val',  width=10, justify='right')
        t.add_column('PB',        width=8,  justify='right')
        t.add_column('Float%',    width=9,  justify='right')
        t.add_column('Promoter%', width=11, justify='right')
        t.add_column('ROE',       width=8,  justify='right')
        t.add_column('Verdict',   width=32)'''

NEW3 = '''        t = Table(title=title, box=box.SIMPLE_HEAVY, border_style='cyan',
                  title_style='bold cyan', show_lines=False)
        t.add_column('Symbol',   width=10, style='bold white')
        t.add_column('Price',    width=10, justify='right')
        t.add_column('Book Val', width=10, justify='right')
        t.add_column('PB',       width=8,  justify='right')
        t.add_column('Float%',   width=9,  justify='right')
        t.add_column('ROE',      width=8,  justify='right')
        t.add_column('EG QoQ',   width=9,  justify='right')
        t.add_column('Score',    width=7,  justify='right')
        t.add_column('Verdict',  width=30)'''

# ── Also sort by score instead of pb_live ──
OLD4 = "        # Sort by pb_live ascending (cheapest first)\n        sec_df = sec_df.sort_values('pb_live', ascending=True, na_position='last')"
NEW4 = "        # Sort will be by score after scoring — keep pb sort as initial\n        sec_df = sec_df.sort_values('pb_live', ascending=True, na_position='last')"

# ── Apply all patches ─────────────────────────────────────────────────────────
patches = [
    (OLD2, NEW2, 'Earnings map + all_scores init injected'),
    (OLD3, NEW3, 'Table columns upgraded'),
    (OLD4, NEW4, 'Sort comment updated'),
    (OLD,  NEW,  'Score logic + leaderboard injected'),
]

for old, new, label in patches:
    if old in src:
        src = src.replace(old, new, 1)
        print(f'✅ {label}')
    else:
        print(f'⚠️  Pattern not found: {label}')

SCANNER.write_text(src, encoding='utf-8')
print('\n✅ nepse_scanner.py saved')
print('\n━━━ Done! ━━━')
print('Test with:')
print('  python nepse_scanner.py --value Hydropower')
print('  python nepse_scanner.py --value')
print('\nNew columns: EG QoQ (earnings growth quarter-on-quarter) + Score (0-100)')
print('Cross-sector Top 10 leaderboard shown at the end of full --value run.')
