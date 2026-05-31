import shutil, ast, re

shutil.copy('nepse_scanner.py', 'nepse_scanner_pre_holders_wire.py')
print('Backup created')

content = open('nepse_scanner.py', encoding='utf-8').read()

# ── 1. Wire top 4 into Why block ─────────────────────────────────────────────
old1 = 'Verdict:[/bold white] {verdict}")\n        console.print()\n\n '
new1 = '''Verdict:[/bold white] {verdict}")
        # Top 4 broker holders from history
        holders = get_top_broker_holders(symbol, db_path, top_n=4)
        if holders:
            console.print(f"    \\u2022 Top holders (cumulative net position):", style="dim")
            for h in holders:
                net = h['total_net']
                direction = 'NET LONG' if net >= 0 else 'NET SHORT'
                amt = ('Rs ' + str(round(abs(net)/1e6, 1)) + 'M') if abs(net) >= 1e6 else ('Rs ' + str(round(abs(net)/1e3)) + 'K')
                col = 'green' if net >= 0 else 'red'
                console.print(f"      Broker {h['broker_id']} ({h['broker_name']}) [{h['days_active']}d] — [{col}]{direction} {amt}[/{col}]", style="dim")
        console.print()

 '''

if old1 in content:
    content = content.replace(old1, new1)
    print('Wired top 4 holders into Why block')
else:
    print('ERROR: Why block wire point not found')

# ── 2. Find menu choice handler pattern ──────────────────────────────────────
# Find what pattern the menu uses
idx = content.find('choice ==')
print('Menu pattern sample:', repr(content[idx:idx+30]))

# Try different quote styles
for q in ['"17"', "'17'", '17']:
    pattern = f'choice == {q}'
    if pattern in content:
        print(f'Found menu pattern: {pattern}')
        old2 = f'choice == {q}:'
        new2 = f'choice == "34" or choice == "bh":\n        symbol_input = input("  Enter stock symbol: ").strip().upper()\n        analyze_broker_holders(symbol_input)\n    elif choice == {q}:'
        content = content.replace(old2, new2, 1)
        print('Wired analyze_broker_holders into menu as option 34/bh')
        break

# ── 3. Add to menu display ───────────────────────────────────────────────────
old3 = '17. Floorsheet - Any Stock'
if old3 in content:
    content = content.replace(old3, '17. Floorsheet - Any Stock\n  34. Top Broker Holders - Any Stock')
    print('Added option 34 to menu display')
else:
    print('WARNING: menu display not found')

open('nepse_scanner.py', 'w', encoding='utf-8').write(content)

try:
    ast.parse(content)
    print('Syntax OK — all wires connected')
except SyntaxError as e:
    print(f'ERROR: {e}')
    shutil.copy('nepse_scanner_pre_holders_wire.py', 'nepse_scanner.py')
    print('Backup restored')
