import shutil, ast

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_17c_order.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

old = """    symbol = symbol.upper()
    if not date_str:
        date_str = input('  Enter date (YYYY-MM-DD or DD/MM/YYYY): ').strip()
    # Normalize date format"""

new = """    symbol = symbol.upper()
    # Show available dates first, then ask for date
    try:
        import sqlite3 as _sq
        _conn = _sq.connect(db_path)
        _avail = _conn.execute(
            'SELECT DISTINCT date FROM broker_activity WHERE symbol=? ORDER BY date DESC LIMIT 30',
            (symbol,)
        ).fetchall()
        _conn.close()
        if _avail:
            console.print()
            console.print(f'  Available dates for [bold]{symbol}[/bold] in DB:')
            for _i, (_d,) in enumerate(_avail, 1):
                console.print(f'    {_i:>2}. {_d}')
            console.print()
        else:
            console.print(f'  No data found for {symbol} yet — run a scan first on a trading day.', style='yellow')
    except Exception:
        pass
    if not date_str or date_str.lower() == 'prompt':
        date_str = input('  Enter date from above (YYYY-MM-DD): ').strip()
    # Normalize date format"""

if old in content:
    content = content.replace(old, new)
    print('Fixed order — available dates shown before date prompt')
else:
    print('ERROR: target not found')
    exit()

# Remove the old available dates block that was inside the try
old2 = ("        # Show available dates for this symbol\n"
        "        available = conn.execute(\n"
        "            'SELECT DISTINCT date FROM broker_activity WHERE symbol=? ORDER BY date DESC LIMIT 30',\n"
        "            (symbol,)\n"
        "        ).fetchall()\n"
        "        if available:\n"
        "            console.print()\n"
        "            console.print(f'  Available dates for [bold]{symbol}[/bold] in DB:')\n"
        "            for idx2, (d,) in enumerate(available, 1):\n"
        "                console.print(f'    {idx2:>2}. {d}')\n"
        "            console.print()\n"
        "        if not date_str:\n"
        "            date_str = input('  Enter date from above (YYYY-MM-DD): ').strip()\n")

new2 = ""

if old2 in content:
    content = content.replace(old2, new2)
    print('Removed duplicate dates block inside try')

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_17c_order.py', 'nepse_scanner.py')
    print('Backup restored')
