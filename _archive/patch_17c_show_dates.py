import shutil, ast

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_17c_dates.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

old = """    if not symbol or not date_str:
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
        conn.close()"""

new = """    if not symbol:
        console.print('  Missing symbol.', style='yellow')
        return
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        # Show available dates for this symbol
        available = conn.execute(
            'SELECT DISTINCT date FROM broker_activity WHERE symbol=? ORDER BY date DESC LIMIT 30',
            (symbol,)
        ).fetchall()
        if available:
            console.print()
            console.print(f'  Available dates for [bold]{symbol}[/bold] in DB:')
            for idx2, (d,) in enumerate(available, 1):
                console.print(f'    {idx2:>2}. {d}')
            console.print()
        if not date_str:
            date_str = input('  Enter date from above (YYYY-MM-DD): ').strip()
        # Normalize date format
        try:
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts[2]) == 4:
                    date_str = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                else:
                    date_str = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
        except Exception:
            pass
        if not date_str:
            console.print('  No date entered.', style='yellow')
            conn.close()
            return
        rows = conn.execute(
            'SELECT broker_id, broker_name, buy_qty, sell_qty, net_qty, buy_val, sell_val, net_val '
            'FROM broker_activity WHERE symbol=? AND date=? '
            'ORDER BY net_val DESC',
            (symbol, date_str)
        ).fetchall()
        conn.close()"""

if old in content:
    content = content.replace(old, new)
    print('Updated analyze_broker_date to show available dates')
else:
    print('ERROR: target section not found')
    exit()

# Also fix symbol normalization — make sure symbol is uppercased
old2 = "        symbol = input('  Enter stock symbol (e.g. CHCL): ').strip().upper()"
new2 = "        symbol = input('  Enter stock symbol (e.g. CHCL): ').strip().upper()\n    symbol = symbol.upper()"
if old2 in content:
    content = content.replace(old2, new2)

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK — available dates will now show before date entry')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_17c_dates.py', 'nepse_scanner.py')
    print('Backup restored')
