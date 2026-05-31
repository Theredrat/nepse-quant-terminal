import shutil, ast

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_17c.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

# Add analyze_broker_date function
NEW_FUNC = '''
def analyze_broker_date(symbol=None, date_str=None, db_path='nepse_market_data.db'):
    """Show broker activity for a specific stock on a specific date."""
    from rich.table import Table
    from rich.rule import Rule
    if not symbol:
        console.print()
        symbol = input('  Enter stock symbol (e.g. CHCL): ').strip().upper()
    if not date_str:
        date_str = input('  Enter date (YYYY-MM-DD or DD/MM/YYYY): ').strip()
    # Normalize date format
    try:
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts[2]) == 4:  # DD/MM/YYYY
                date_str = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            else:  # MM/DD/YYYY
                date_str = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
    except Exception:
        pass
    if not symbol or not date_str:
        console.print('  Missing symbol or date.', style='yellow')
        return
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            'SELECT broker_id, broker_name, buy_qty, sell_qty, net_qty, buy_val, sell_val, net_val '
            'FROM broker_activity WHERE symbol=? AND date=? '
            'ORDER BY net_val DESC',
            (symbol, date_str)
        ).fetchall()
        conn.close()
    except Exception as e:
        console.print(f'  DB error: {e}', style='red')
        return
    console.print()
    console.print(Rule(f'Broker Activity — {symbol} on {date_str}', style='cyan'))
    if not rows:
        console.print(f'  No data found for {symbol} on {date_str}.', style='yellow')
        console.print('  Note: Only dates after you started running scans will have data.', style='dim')
        return
    def _fmt(val):
        if abs(val) >= 1e6:
            return ('Rs ' + str(round(abs(val)/1e6, 1)) + 'M')
        return ('Rs ' + str(round(abs(val)/1e3)) + 'K')
    t = Table(show_header=True, header_style='bold cyan', box=None, padding=(0, 2))
    t.add_column('#', style='dim', width=4)
    t.add_column('Broker ID', width=10)
    t.add_column('Broker Name', width=35)
    t.add_column('Net Position', width=14, justify='right')
    t.add_column('Net Shares', width=12, justify='right')
    t.add_column('Avg Price', width=12, justify='right')
    t.add_column('Total Bought', width=14, justify='right')
    t.add_column('Total Sold', width=14, justify='right')
    total_buy_val = 0
    total_sell_val = 0
    buyers = 0
    sellers = 0
    for i, (bid, bname, bq, sq, nq, bv, sv, nv) in enumerate(rows, 1):
        net_style = 'green' if nv >= 0 else 'red'
        net_str = ('+' if nv >= 0 else '-') + _fmt(nv)
        nq_str = ('+' if nq >= 0 else '') + f'{nq:,}'
        total_vol = bq + sq
        avg_price = round((bv + sv) / total_vol, 1) if total_vol > 0 else 0
        avg_str = f'Rs {avg_price:,.1f}' if avg_price > 0 else '-'
        t.add_row(str(i), str(bid), str(bname or ''),
            f'[{net_style}]{net_str}[/{net_style}]',
            f'[{net_style}]{nq_str}[/{net_style}]',
            avg_str, _fmt(bv), _fmt(sv))
        total_buy_val += bv
        total_sell_val += sv
        if nv > 0: buyers += 1
        elif nv < 0: sellers += 1
    console.print(t)
    console.print()
    # Summary
    console.print(f'  Total brokers: {len(rows)}  |  Net buyers: [green]{buyers}[/green]  |  Net sellers: [red]{sellers}[/red]')
    console.print(f'  Total volume bought: {_fmt(total_buy_val)}  |  Total volume sold: {_fmt(total_sell_val)}')
    net_flow = total_buy_val - total_sell_val
    flow_col = 'green' if net_flow >= 0 else 'red'
    flow_dir = 'NET INFLOW' if net_flow >= 0 else 'NET OUTFLOW'
    console.print(f'  [{flow_col}]{flow_dir}: {_fmt(abs(net_flow))}[/{flow_col}]')
    console.print()

'''

idx = content.rfind('\nif __name__')
content = content[:idx] + NEW_FUNC + content[idx:]
print('Added analyze_broker_date()')

# Add --broker-date argument to parser
old_arg = "    p.add_argument('--broker-holders'"
new_arg = "    p.add_argument('--broker-date', nargs=2, metavar=('SYMBOL', 'DATE'), default=None, help='Broker activity for a stock on a specific date')\n    p.add_argument('--broker-holders'"
if old_arg in content:
    content = content.replace(old_arg, new_arg)
    print('Added --broker-date to parser')

# Wire into main
old_main = "    if getattr(args, 'broker_holders', None):"
new_main = """    if getattr(args, 'broker_date', None):
        analyze_broker_date(args.broker_date[0], args.broker_date[1])
        return
    if getattr(args, 'broker_holders', None):"""
if old_main in content:
    content = content.replace(old_main, new_main, 1)
    print('Wired --broker-date into main')

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_17c.py', 'nepse_scanner.py')
    print('Backup restored')

# Update bat file
bat = open('launch_nepse.bat', encoding='utf-8').read()
shutil.copy('launch_nepse.bat', 'launch_nepse_pre_17c.bat')

# Add to menu display
old_d = 'echo   17b. Top Broker Holders - Any Stock'
new_d = 'echo   17b. Top Broker Holders - Any Stock\necho   17c. Broker Activity - Specific Date'
if old_d in bat:
    bat = bat.replace(old_d, new_d)
    print('Added 17c to menu display')

# Add handler
old_h = 'if "%choice%"=="17b" goto CUSTOM_HOLDERS'
new_h = 'if "%choice%"=="17b" goto CUSTOM_HOLDERS\nif "%choice%"=="17c" goto CUSTOM_DATE'
if old_h in bat:
    bat = bat.replace(old_h, new_h)
    print('Added 17c handler')

# Add label
old_l = ':CUSTOM_HOLDERS'
new_l = ':CUSTOM_DATE\nset /p dt_sym=  Enter stock symbol (e.g. CHCL):\nset /p dt_date=  Enter date (YYYY-MM-DD):\npython nepse_scanner.py --broker-date %dt_sym% %dt_date%\ngoto AGAIN\n\n:CUSTOM_HOLDERS'
if old_l in bat:
    bat = bat.replace(old_l, new_l, 1)
    print('Added :CUSTOM_DATE label')

open('launch_nepse.bat', 'w', encoding='utf-8').write(bat)
print('Bat file updated')
