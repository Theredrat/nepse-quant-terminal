"""
build_why_engine.py
Run this ONCE from your nepse-quant-terminal folder:
    python build_why_engine.py

What it does:
  1. Backs up nepse_scanner.py
  2. Adds 5 new functions (logger + story + why block)
  3. Patches main() to auto-log + adds --why flag
  4. Updates launch_nepse.bat with new menu option
  5. Syntax-checks everything — auto-restores if broken
"""

import shutil, ast, re, os

# ── SAFETY ────────────────────────────────────────────────────────────────────
shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_why.py')
print('✓ Backup saved: nepse_scanner_pre_why.py')

content = open('nepse_scanner.py', encoding='utf-8').read()

# ── NEW FUNCTIONS ─────────────────────────────────────────────────────────────
NEW_CODE = '''

# ══════════════════════════════════════════════════════════════════════════════
# WHY ENGINE — Broker Activity Logger + Story Generator + Why Block
# ══════════════════════════════════════════════════════════════════════════════

def _init_broker_activity_table(db_path="nepse_market_data.db"):
    """Create broker_activity table if it does not exist."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broker_activity (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol       TEXT    NOT NULL,
            date         TEXT    NOT NULL,
            broker_id    TEXT    NOT NULL,
            broker_name  TEXT,
            buy_qty      REAL    DEFAULT 0,
            sell_qty     REAL    DEFAULT 0,
            net_qty      REAL    DEFAULT 0,
            buy_val      REAL    DEFAULT 0,
            sell_val     REAL    DEFAULT 0,
            net_val      REAL    DEFAULT 0,
            UNIQUE(symbol, date, broker_id)
        )
    """)
    conn.commit()
    conn.close()


def log_broker_activity(full_fs, db_path="nepse_market_data.db"):
    """
    Save today's broker-level summary per stock to broker_activity table.
    Called silently after every floorsheet fetch. Takes ~0.5 seconds.
    """
    if full_fs is None or full_fs.empty:
        return 0

    import sqlite3
    _init_broker_activity_table(db_path)

    df = full_fs.copy()
    df['buyer_broker']  = df['buyer_broker'].astype(str).str.strip()
    df['seller_broker'] = df['seller_broker'].astype(str).str.strip()

    date = str(df['businessDate'].iloc[0]) if 'businessDate' in df.columns else pd.Timestamp.today().strftime('%Y-%m-%d')

    buys = df.groupby(['symbol', 'buyer_broker', 'buyerBrokerName']).agg(
        buy_qty=('quantity', 'sum'),
        buy_val=('amount', 'sum')
    ).reset_index().rename(columns={'buyer_broker': 'broker_id', 'buyerBrokerName': 'broker_name'})

    sells = df.groupby(['symbol', 'seller_broker', 'sellerBrokerName']).agg(
        sell_qty=('quantity', 'sum'),
        sell_val=('amount', 'sum')
    ).reset_index().rename(columns={'seller_broker': 'broker_id', 'sellerBrokerName': 'broker_name'})

    merged = pd.merge(buys, sells, on=['symbol', 'broker_id'], how='outer', suffixes=('_b', '_s'))
    merged['broker_name'] = merged['broker_name_b'].fillna(merged['broker_name_s']).fillna('')
    merged['buy_qty']  = merged['buy_qty'].fillna(0)
    merged['buy_val']  = merged['buy_val'].fillna(0)
    merged['sell_qty'] = merged['sell_qty'].fillna(0)
    merged['sell_val'] = merged['sell_val'].fillna(0)
    merged['net_qty']  = merged['buy_qty'] - merged['sell_qty']
    merged['net_val']  = merged['buy_val'] - merged['sell_val']
    merged['date']     = date

    conn = sqlite3.connect(db_path)
    saved = 0
    for _, row in merged.iterrows():
        try:
            conn.execute("""
                INSERT OR IGNORE INTO broker_activity
                (symbol, date, broker_id, broker_name,
                 buy_qty, sell_qty, net_qty, buy_val, sell_val, net_val)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                row['symbol'], row['date'], row['broker_id'], str(row.get('broker_name', '')),
                float(row['buy_qty']), float(row['sell_qty']), float(row['net_qty']),
                float(row['buy_val']), float(row['sell_val']), float(row['net_val'])
            ))
            saved += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return saved


def get_broker_story(symbol, today_fs, db_path="nepse_market_data.db"):
    """
    Returns a dict describing broker behavior for a stock today + history.
    """
    result = {
        'dominant_broker_id':   None,
        'dominant_broker_name': '',
        'dominant_action':      'neutral',
        'dominant_pct':         0.0,
        'dominant_net_val':     0.0,
        'history_days':         0,
        'history_action':       None,
        'history_summary':      '',
        'total_brokers':        0,
        'buy_brokers':          0,
        'sell_brokers':         0,
        'concentration':        'low',
    }

    if today_fs is None or today_fs.empty:
        return result

    sym_fs = today_fs[today_fs['symbol'] == symbol].copy()
    if sym_fs.empty:
        return result

    total_vol = sym_fs['quantity'].sum()
    if total_vol == 0:
        return result

    buys  = sym_fs.groupby(['buyer_broker',  'buyerBrokerName'])['quantity'].sum().reset_index()
    sells = sym_fs.groupby(['seller_broker', 'sellerBrokerName'])['quantity'].sum().reset_index()
    buys.columns  = ['broker_id', 'broker_name', 'buy_qty']
    sells.columns = ['broker_id', 'broker_name', 'sell_qty']

    brokers = pd.merge(buys, sells, on='broker_id', how='outer', suffixes=('_b', '_s'))
    brokers['broker_name'] = brokers['broker_name_b'].fillna(brokers['broker_name_s']).fillna('')
    brokers['buy_qty']  = brokers['buy_qty'].fillna(0)
    brokers['sell_qty'] = brokers['sell_qty'].fillna(0)
    brokers['net_qty']  = brokers['buy_qty'] - brokers['sell_qty']
    brokers['total']    = brokers['buy_qty'] + brokers['sell_qty']

    # Net value per broker
    def _broker_net_val(bid):
        bv = sym_fs[sym_fs['buyer_broker'].astype(str) == str(bid)]['amount'].sum()
        sv = sym_fs[sym_fs['seller_broker'].astype(str) == str(bid)]['amount'].sum()
        return float(bv) - float(sv)

    brokers['net_val'] = brokers['broker_id'].apply(_broker_net_val)

    result['total_brokers'] = len(brokers)
    result['buy_brokers']   = int((brokers['net_qty'] > 0).sum())
    result['sell_brokers']  = int((brokers['net_qty'] < 0).sum())

    dom     = brokers.loc[brokers['total'].idxmax()]
    dom_pct = float(dom['total']) / total_vol * 100

    result['dominant_broker_id']   = str(dom['broker_id'])
    result['dominant_broker_name'] = str(dom['broker_name']).split('.')[0].strip()
    result['dominant_pct']         = round(dom_pct, 1)
    result['dominant_net_val']     = round(float(dom['net_val']), 0)
    result['concentration']        = 'high' if dom_pct > 40 else 'medium' if dom_pct > 25 else 'low'

    net_threshold = total_vol * 0.05
    if dom['net_qty'] > net_threshold:
        result['dominant_action'] = 'buying'
    elif dom['net_qty'] < -net_threshold:
        result['dominant_action'] = 'selling'
    else:
        result['dominant_action'] = 'neutral'

    # Historical pattern
    try:
        _init_broker_activity_table(db_path)
        import sqlite3
        conn = sqlite3.connect(db_path)
        hist = pd.read_sql("""
            SELECT date, net_qty, net_val
            FROM broker_activity
            WHERE symbol = ? AND broker_id = ?
            ORDER BY date DESC LIMIT 10
        """, conn, params=(symbol, str(dom['broker_id'])))
        conn.close()

        if not hist.empty:
            result['history_days'] = len(hist)
            buy_days  = int((hist['net_qty'] > 0).sum())
            sell_days = int((hist['net_qty'] < 0).sum())
            if buy_days >= sell_days * 2:
                result['history_action']  = 'accumulating'
                result['history_summary'] = f"bought {buy_days} of last {len(hist)} days"
            elif sell_days >= buy_days * 2:
                result['history_action']  = 'distributing'
                result['history_summary'] = f"sold {sell_days} of last {len(hist)} days"
            else:
                result['history_action']  = 'mixed'
                result['history_summary'] = f"mixed — {buy_days} buy / {sell_days} sell days"
    except Exception:
        pass

    return result


def _fmt_rs_val(val):
    """Format Rs value compactly."""
    if val is None:
        return ''
    a = abs(val)
    if a >= 1_000_000:
        return f"Rs {val/1_000_000:.1f}M"
    if a >= 1_000:
        return f"Rs {val/1_000:.0f}K"
    return f"Rs {val:.0f}"


def analyze_why(live_df, full_fs, rs_data=None, db_path="nepse_market_data.db"):
    """
    Print Why blocks for top bullish + bearish + neutral stocks.
    Add --why flag to any scan to trigger this.
    """
    from rich.rule import Rule

    console.print()
    console.rule("[bold yellow]Why These Stocks Were Flagged[/bold yellow]", style="yellow")
    console.print("[dim]Broker behavior + RS vs sector + 52W position + unlock dates[/dim]\\n")

    # RS data
    if rs_data is None:
        rs_data = _calc_relative_strength(db_path)
    if not rs_data:
        console.print("[red]No RS data available.[/red]")
        return

    rdf = pd.DataFrame(rs_data)

    # Select stocks to explain
    bullish = rdf[rdf['rs5'] > 2].head(3).to_dict('records')
    bearish = rdf[rdf['rs5'] < -2].sort_values('rs5' if 'rs5' in rdf.columns else 'rs_score').head(3).to_dict('records')

    # Neutral = high turnover stocks with -2 < rs5 < 2
    neutral_syms = []
    if live_df is not None and not live_df.empty:
        try:
            vcols = [c for c in live_df.columns if any(x in c.lower() for x in ['turnover','volume','amount'])]
            if vcols:
                top_syms = live_df.nlargest(20, vcols[0])['symbol'].tolist()
                neutral_syms = [r for r in rs_data if r['symbol'] in top_syms and -2 <= r.get('rs5', 0) <= 2][:2]
        except Exception:
            pass

    # Unlock map
    unlock_map = {}
    try:
        import sqlite3
        _init_broker_activity_table(db_path)
        conn = sqlite3.connect(db_path)
        udf = pd.read_sql("""
            SELECT symbol, MIN(unlock_date) as next_unlock
            FROM unlock_dates WHERE unlock_date >= date('now')
            GROUP BY symbol
        """, conn)
        conn.close()
        unlock_map = dict(zip(udf['symbol'], udf['next_unlock']))
    except Exception:
        pass

    # ── WHY BLOCK ─────────────────────────────────────────────────────────────
    def _print_why(stock, tag):
        symbol = stock['symbol']
        sector = stock.get('sector', '')
        rs5    = stock.get('rs5', 0) or 0
        sec5   = stock.get('sec5', 0) or 0
        ret5   = stock.get('ret5', 0) or 0

        rs_rank  = sorted(rs_data, key=lambda x: x.get('rs_score', 0), reverse=True)
        rank     = next((i+1 for i, r in enumerate(rs_rank) if r['symbol'] == symbol), '?')
        total    = len(rs_rank)

        bstory   = get_broker_story(symbol, full_fs, db_path)
        unlock   = unlock_map.get(symbol)

        # 52W note from live_df
        w52_note = ''
        if live_df is not None and not live_df.empty:
            try:
                row = live_df[live_df['symbol'] == symbol]
                if not row.empty:
                    r    = row.iloc[0]
                    hcol = next((c for c in live_df.columns if '52' in c and 'high' in c.lower()), None)
                    lcol = next((c for c in live_df.columns if '52' in c and 'low'  in c.lower()), None)
                    pcol = next((c for c in live_df.columns if c.lower() in ('ltp','last_traded_price','close','lastTradedPrice')), None)
                    if hcol and pcol:
                        ltp  = float(r[pcol])
                        high = float(r[hcol])
                        pct_from_high = (ltp - high) / high * 100
                        if pct_from_high >= -5:
                            w52_note = f"Only {abs(pct_from_high):.1f}% from 52W high — breakout zone"
                        elif lcol:
                            low = float(r[lcol])
                            if low > 0:
                                pct_from_low = (ltp - low) / low * 100
                                if pct_from_low <= 5:
                                    w52_note = f"Only {pct_from_low:.1f}% above 52W low — danger zone"
                        if not w52_note:
                            w52_note = f"{abs(pct_from_high):.1f}% below 52W high"
            except Exception:
                pass

        # ── Build bullets ──────────────────────────────────────────────────
        # Bullet 1 — Broker
        bid   = bstory['dominant_broker_id']
        bname = bstory['dominant_broker_name'] or (f"Broker {bid}" if bid else None)
        if bid:
            conc  = {'high': f"dominant — {bstory['dominant_pct']:.0f}% of today's volume",
                     'medium': f"active — {bstory['dominant_pct']:.0f}% of today's volume",
                     'low':  f"present — {bstory['dominant_pct']:.0f}% of today's volume"}.get(bstory['concentration'], '')
            act   = {'buying': 'net BUYING', 'selling': 'net SELLING', 'neutral': 'market making'}.get(bstory['dominant_action'], '')
            nval  = _fmt_rs_val(abs(bstory['dominant_net_val'])) if bstory['dominant_net_val'] else ''
            nval_str = f" ({nval})" if nval else ""

            hist_note = ''
            if bstory['history_days'] > 1:
                hist_note = f"  [{bstory['history_summary']}]"
                if bstory['history_action'] == 'accumulating' and bstory['dominant_action'] == 'selling':
                    hist_note += " ← FIRST SELL after accumulation (exit alert)"
                elif bstory['history_action'] == 'distributing' and bstory['dominant_action'] == 'buying':
                    hist_note += " ← FIRST BUY after distribution (reversal alert)"

            broad = ''
            if bstory['total_brokers'] > 0:
                bp = bstory['buy_brokers'] / bstory['total_brokers'] * 100
                if bp > 65:
                    broad = f"  |  {bstory['buy_brokers']}/{bstory['total_brokers']} brokers net buying (broad accumulation)"
                elif bp < 35:
                    broad = f"  |  {bstory['sell_brokers']}/{bstory['total_brokers']} brokers net selling (broad distribution)"

            b1 = f"Broker {bid} ({bname}) — {conc}, {act}{nval_str}{hist_note}{broad}"
        else:
            b1 = "Floorsheet not available (run with a scan that fetches floorsheet)"

        # Bullet 2 — Sector context
        if sec5 != 0:
            if rs5 > 0 and sec5 > 0:
                b2 = f"Sector ({sector}) also rising +{sec5:.1f}% 5D — stock outperforming by +{rs5:.1f}% (momentum confirmed)"
            elif rs5 < 0 and sec5 > 0:
                b2 = f"Sector ({sector}) up +{sec5:.1f}% but stock {ret5:+.1f}% — STOCK-SPECIFIC weakness, not sector"
            elif rs5 < 0 and sec5 < 0:
                b2 = f"Sector ({sector}) also weak {sec5:.1f}% — broad sector selling, not just this stock"
            else:
                b2 = f"Sector ({sector}) {sec5:+.1f}% / Stock {ret5:+.1f}% — RS {rs5:+.1f}%"
        else:
            b2 = f"Sector ({sector}) data unavailable for comparison"

        # Bullet 3 — RS rank
        if rs5 > 5:
            b3 = f"RS +{rs5:.2f}% vs sector — Rank #{rank}/{total} (top performer in market)"
        elif rs5 > 2:
            b3 = f"RS +{rs5:.2f}% vs sector — Rank #{rank}/{total} (outperforming sector)"
        elif rs5 >= -2:
            b3 = f"RS {rs5:+.2f}% vs sector — Rank #{rank}/{total} (inline with sector)"
        elif rs5 > -5:
            b3 = f"RS {rs5:.2f}% vs sector — Rank #{rank}/{total} (underperforming sector)"
        else:
            b3 = f"RS {rs5:.2f}% vs sector — Rank #{rank}/{total} (worst performers in market)"

        # Bullet 4 — 52W + unlock
        parts = []
        if w52_note:
            parts.append(w52_note)
        if unlock:
            parts.append(f"Lock-in expiry: {unlock} — supply overhang risk")
        else:
            parts.append("No lock-in expiry found")
        b4 = "  |  ".join(parts)

        # Verdict
        ha = bstory.get('history_action')
        da = bstory.get('dominant_action')
        if tag == 'bull':
            if ha == 'accumulating' and rs5 > 5:
                verdict = "Sustained institutional accumulation + top RS. High conviction — buy on dips."
            elif da == 'buying' and bstory['concentration'] == 'high' and rs5 > 3:
                verdict = "Whale accumulating aggressively + strong RS. Watch for 52W high breakout."
            elif rs5 > 5:
                verdict = "Strongest momentum in market. Sector tailwind confirmed. Buy pullbacks."
            else:
                verdict = "Outperforming sector. Positive momentum — monitor for continuation."

        elif tag == 'bear':
            if ha == 'distributing' and rs5 < -5:
                verdict = "Sustained distribution + worst RS. No floor visible. Avoid entirely."
            elif da == 'selling' and sec5 > 0:
                verdict = "Promoter/whale exit while sector rises. Stock-specific. Avoid until selling stops."
            elif unlock:
                verdict = f"Lock-in expiry {unlock} creating supply. Wait for expiry to pass before entry."
            elif sec5 < 0:
                verdict = "Sector-wide weakness — not stock-specific. Wait for sector to stabilize first."
            else:
                verdict = "Underperforming sector. No catalyst visible. Avoid or cut losses."

        else:  # neutral
            if da == 'buying' and rs5 < 0:
                verdict = "Broker accumulating but RS still negative — early/risky entry. Wait for RS to turn positive."
            elif da == 'selling' and rs5 > 0:
                verdict = "RS positive but broker distributing — topping risk. Tighten stops if holding."
            elif unlock:
                verdict = f"Mixed signals + unlock on {unlock}. Wait for post-expiry clarity."
            else:
                verdict = "No strong signal. High turnover stock — monitor for breakout direction."

        # Print
        colors = {'bull': 'green', 'bear': 'red', 'neutral': 'yellow'}
        labels = {'bull': 'BULLISH', 'bear': 'BEARISH', 'neutral': 'NEUTRAL'}
        c = colors.get(tag, 'white')
        l = labels.get(tag, '')

        console.print(f"  [bold {c}]📌 {symbol}[/bold {c}] [{c}]— {l}[/{c}]")
        console.print(f"    [cyan]•[/cyan] {b1}")
        console.print(f"    [cyan]•[/cyan] {b2}")
        console.print(f"    [cyan]•[/cyan] {b3}")
        console.print(f"    [cyan]•[/cyan] {b4}")
        console.print(f"    [bold white]→ Verdict:[/bold white] {verdict}")
        console.print()

    # Print all sections
    if bullish:
        console.print("[bold green]── BULLISH — Accumulation Signals ──────────────────────────────[/bold green]")
        for s in bullish:
            _print_why(s, 'bull')

    if bearish:
        console.print("[bold red]── BEARISH — Distribution Signals ──────────────────────────────[/bold red]")
        for s in bearish:
            _print_why(s, 'bear')

    if neutral_syms:
        console.print("[bold yellow]── NEUTRAL — Watch for Direction ────────────────────────────────[/bold yellow]")
        for s in neutral_syms:
            _print_why(s, 'neutral')

    console.print(Rule(style="dim"))
'''

# ── INSERT NEW CODE BEFORE if __name__ ────────────────────────────────────────
insert_at = content.rfind('\nif __name__')
if insert_at == -1:
    insert_at = len(content)
content = content[:insert_at] + NEW_CODE + content[insert_at:]
print('✓ New functions appended')

# ── PATCH 1: log_broker_activity after floorsheet fetch ───────────────────────
old1 = '    full_fs = None\n    if need_floor:\n        full_fs = get_full_floorsheet(n)'
new1 = '''    full_fs = None
    if need_floor:
        full_fs = get_full_floorsheet(n)
        try:
            log_broker_activity(full_fs)
        except Exception:
            pass'''

if old1 in content:
    content = content.replace(old1, new1)
    print('✓ Patch 1: log_broker_activity() auto-call added')
else:
    print('⚠ Patch 1 not applied — add log_broker_activity(full_fs) manually after floorsheet fetch')

# ── PATCH 2: add --why to parse_args ──────────────────────────────────────────
old2 = "    p.add_argument('--rs',          action='store_true')"
new2 = "    p.add_argument('--rs',          action='store_true')\n    p.add_argument('--why',         action='store_true', help='Show Why block — broker+RS+52W+unlock reasoning')"

if old2 in content:
    content = content.replace(old2, new2)
    print('✓ Patch 2: --why argument added')
else:
    print('⚠ Patch 2 not applied — add --why arg to parse_args manually')

# ── PATCH 3: call analyze_why after --rs ──────────────────────────────────────
old3 = '    if args.rs:\n        analyze_relative_strength()\n        console.print()'
new3 = '    if args.rs:\n        analyze_relative_strength()\n        console.print()\n        if getattr(args, "why", False):\n            analyze_why(live_df, full_fs)'

if old3 in content:
    content = content.replace(old3, new3)
    print('✓ Patch 3: analyze_why() wired to --rs')
else:
    print('⚠ Patch 3 not applied — add analyze_why call after --rs manually')

# ── PATCH 4: call analyze_why after --week52 ──────────────────────────────────
old4 = '    elif args.week52:\n        analyze_week52()'
new4 = '    elif args.week52:\n        analyze_week52()\n        if getattr(args, "why", False):\n            analyze_why(live_df, full_fs)'

if old4 in content:
    content = content.replace(old4, new4)
    print('✓ Patch 4: analyze_why() wired to --week52')
else:
    print('⚠ Patch 4 not applied — add analyze_why call after --week52 manually')

# ── WRITE FILE ────────────────────────────────────────────────────────────────
open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

# ── SYNTAX CHECK ─────────────────────────────────────────────────────────────
try:
    ast.parse(open('nepse_scanner.py', encoding='utf-8').read())
    print('✓ Syntax OK')
except SyntaxError as e:
    print(f'✗ SYNTAX ERROR: {e}')
    print('  Restoring backup...')
    shutil.copy('nepse_scanner_pre_why.py', 'nepse_scanner.py')
    print('  Restored. No changes made.')
    exit(1)

# ── UPDATE launch_nepse.bat ───────────────────────────────────────────────────
bat = open('launch_nepse.bat', encoding='utf-8').read()

old_bat1 = 'echo   7r. Relative Strength  (RS vs sector)'
new_bat1 = 'echo   7r. Relative Strength  (RS vs sector)\necho   7rw. RS + Why  (RS with full reasoning)'

old_bat2 = "if \"%choice%\"==\"7r\" python nepse_scanner.py --rs & goto AGAIN"
new_bat2 = "if \"%choice%\"==\"7r\"  python nepse_scanner.py --rs & goto AGAIN\nif \"%choice%\"==\"7rw\" python nepse_scanner.py --rs --why & goto AGAIN"

old_bat3 = 'echo   7w. 52-Week High/Low Alerts'
new_bat3 = 'echo   7w. 52-Week High/Low Alerts\necho   7ww. 52W + Why  (52W with full reasoning)'

old_bat4 = "if \"%choice%\"==\"7w\" python nepse_scanner.py --week52 & goto AGAIN"
new_bat4 = "if \"%choice%\"==\"7w\"  python nepse_scanner.py --week52 & goto AGAIN\nif \"%choice%\"==\"7ww\" python nepse_scanner.py --week52 --why & goto AGAIN"

bat_changed = 0
for old, new in [(old_bat1, new_bat1), (old_bat2, new_bat2), (old_bat3, new_bat3), (old_bat4, new_bat4)]:
    if old in bat:
        bat = bat.replace(old, new)
        bat_changed += 1

if bat_changed > 0:
    open('launch_nepse.bat', 'w', encoding='utf-8').write(bat)
    print(f'✓ launch_nepse.bat updated ({bat_changed} changes) — new options: 7rw and 7ww')
else:
    print('⚠ launch_nepse.bat not updated — add 7rw and 7ww manually')

print()
print('=' * 60)
print('DONE. New menu options:')
print('  7rw  — RS scan + Why reasoning')
print('  7ww  — 52W scan + Why reasoning')
print()
print('Or run directly:')
print('  python nepse_scanner.py --rs --why')
print('  python nepse_scanner.py --week52 --why')
print()
print('History builds automatically every time you run any scan')
print('that fetches the floorsheet (options 5,6,7,8,9,10,13).')
print('After 5 trading days the Why block gets significantly richer.')
print('=' * 60)
