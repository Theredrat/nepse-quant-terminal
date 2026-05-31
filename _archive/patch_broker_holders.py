import shutil, ast, re

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_holders.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

# ── 1. Add get_top_broker_holders() function ─────────────────────────────────
NEW_FUNC = '''
def get_top_broker_holders(symbol, db_path='nepse_market_data.db', top_n=15):
    """Return top broker holders for a symbol based on cumulative net buying from DB."""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            'SELECT broker_id, broker_name, '
            'SUM(buy_val) as total_buy, SUM(sell_val) as total_sell, '
            'SUM(net_val) as total_net, COUNT(DISTINCT date) as days_active '
            'FROM broker_activity WHERE symbol=? '
            'GROUP BY broker_id, broker_name '
            'ORDER BY total_net DESC',
            (symbol,)
        ).fetchall()
        conn.close()
        results = []
        for bid, bname, tbuy, tsell, tnet, days in rows:
            results.append(dict(
                broker_id=str(bid),
                broker_name=str(bname or ''),
                total_buy=float(tbuy or 0),
                total_sell=float(tsell or 0),
                total_net=float(tnet or 0),
                days_active=int(days or 0),
            ))
        return results[:top_n]
    except Exception as e:
        return []


def analyze_broker_holders(symbol=None, db_path='nepse_market_data.db'):
    """Menu option — show top 15 broker holders for any stock."""
    from rich.table import Table
    from rich.rule import Rule
    if not symbol:
        console.print()
        symbol = input('  Enter stock symbol (e.g. BUNGAL): ').strip().upper()
    if not symbol:
        console.print('  No symbol entered.', style='yellow')
        return
    holders = get_top_broker_holders(symbol, db_path, top_n=15)
    console.print()
    console.print(Rule(f'Top Broker Holders — {symbol}', style='cyan'))
    if not holders:
        console.print(f'  No broker history found for {symbol}.', style='yellow')
        console.print('  History builds automatically each trading day you run any scan.', style='dim')
        return
    t = Table(show_header=True, header_style='bold cyan', box=None, padding=(0, 2))
    t.add_column('#', style='dim', width=4)
    t.add_column('Broker ID', width=10)
    t.add_column('Broker Name', width=35)
    t.add_column('Net Position', width=16, justify='right')
    t.add_column('Total Bought', width=16, justify='right')
    t.add_column('Total Sold', width=16, justify='right')
    t.add_column('Days Active', width=12, justify='right')
    def _fmt(val):
        if abs(val) >= 1e6:
            return ('Rs ' + str(round(abs(val)/1e6, 1)) + 'M')
        return ('Rs ' + str(round(abs(val)/1e3)) + 'K')
    for i, h in enumerate(holders, 1):
        net = h['total_net']
        net_str = ('+' if net >= 0 else '-') + _fmt(net)
        net_style = 'green' if net >= 0 else 'red'
        t.add_row(
            str(i),
            h['broker_id'],
            h['broker_name'],
            f'[{net_style}]{net_str}[/{net_style}]',
            _fmt(h['total_buy']),
            _fmt(h['total_sell']),
            str(h['days_active']) + 'd',
        )
    console.print(t)
    console.print()
    if holders:
        top = holders[0]
        console.print(f"  Top holder: Broker {top['broker_id']} ({top['broker_name']}) — net {'+' if top['total_net']>=0 else ''}{round(top['total_net']/1e6,1)}M over {top['days_active']} days", style='bold')
    console.print()

'''

idx = content.rfind('\nif __name__')
content = content[:idx] + NEW_FUNC + content[idx:]
print('Added get_top_broker_holders() and analyze_broker_holders()')

# ── 2. Wire top 4 holders into Why block (_print_why) ────────────────────────
# Add after the broad brokers line in _print_why
old_wire = "            broad = ''\n            if bstory['total_brokers'] > 0:"
new_wire = """            broad = ''
            if bstory['total_brokers'] > 0:"""

# Find where hist_note is printed in _print_why and add holders before it
old_print = "        if bid:\n            console.print(f\"    \\u2022 {bname}"
# Instead find the bullet print line
bullet_match = re.search(r'console\.print\(f"    • \{bname\}', content)
if not bullet_match:
    bullet_match = re.search(r'console\.print\(.*bname.*today.*volume', content)

# Wire top 4 into Why block — add after the hist_note block prints
old_why_end = "        console.print(f\"    \\u2192 Verdict: {verdict}\")"
if old_why_end not in content:
    old_why_end = '        console.print(f"    → Verdict: {verdict}")'

if old_why_end in content:
    new_why_end = '''        console.print(f"    \\u2192 Verdict: {verdict}")
        # Top 4 broker holders from history
        holders = get_top_broker_holders(symbol, db_path, top_n=4)
        if holders:
            console.print(f"    \\u2022 Top holders (cumulative net position):", style="dim")
            for h in holders:
                net = h['total_net']
                direction = 'NET LONG' if net >= 0 else 'NET SHORT'
                amt = ('Rs ' + str(round(abs(net)/1e6, 1)) + 'M') if abs(net) >= 1e6 else ('Rs ' + str(round(abs(net)/1e3)) + 'K')
                col = 'green' if net >= 0 else 'red'
                console.print(f"      Broker {h['broker_id']} ({h['broker_name']}) [{h['days_active']}d] — [{col}]{direction} {amt}[/{col}]", style="dim")'''
    content = content.replace(old_why_end, new_why_end)
    print('Wired top 4 holders into Why block')
else:
    print('WARNING: Why block verdict line not found — top 4 not wired into Why block')

# ── 3. Wire analyze_broker_holders into menu ─────────────────────────────────
# Find the menu choice handler and add option for broker holders
old_menu = "    elif choice == '17':\n"
if old_menu in content:
    new_menu = """    elif choice == '34' or choice == 'bh':
        symbol = input('  Enter stock symbol: ').strip().upper()
        analyze_broker_holders(symbol)
    elif choice == '17':
"""
    content = content.replace(old_menu, new_menu)
    print('Wired analyze_broker_holders into menu as option 34/bh')
else:
    print('WARNING: menu choice 17 not found — broker holders not added to menu')

# ── 4. Update menu display ────────────────────────────────────────────────────
old_menu_display = "  17. Floorsheet - Any Stock"
if old_menu_display in content:
    new_menu_display = """  17. Floorsheet - Any Stock
  34. Top Broker Holders - Any Stock"""
    content = content.replace(old_menu_display, new_menu_display)
    print('Added option 34 to menu display')

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK — broker holders feature installed')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_holders.py', 'nepse_scanner.py')
    print('Backup restored')
