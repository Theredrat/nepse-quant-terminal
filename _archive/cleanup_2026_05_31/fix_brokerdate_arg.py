import shutil, ast, types

# Back up
shutil.copy('launch_nepse.bat', '_backups/launch_nepse_pre_bdarg.bat')
shutil.copy('nepse_scanner.py', '_backups/nepse_scanner_pre_bdarg.py')

# ── Fix 1: bat file — pass only symbol, scanner handles date prompt ──
bat = open('launch_nepse.bat', encoding='utf-8').read()

# Replace CUSTOM_BROKERDATE to not pass date
old = ':CUSTOM_BROKERDATE\nset /p symbol=  Enter stock symbol (e.g. CHCL):\npython nepse_scanner.py --broker-date %symbol%\ngoto AGAIN'
new = ':CUSTOM_BROKERDATE\nset /p symbol=  Enter stock symbol (e.g. CHCL):\npython nepse_scanner.py --broker-date %symbol% prompt\ngoto AGAIN'
if old in bat:
    bat = bat.replace(old, new)
    print("Fixed bat: passing 'prompt' as date placeholder")
else:
    print(f"WARNING: old pattern not found, current:")
    idx = bat.find('CUSTOM_BROKERDATE')
    print(repr(bat[idx:idx+200]))

open('launch_nepse.bat', 'w', encoding='utf-8').write(bat)

# ── Fix 2: scanner — handle 'prompt' as date_str meaning ask user ──
src = open('nepse_scanner.py', encoding='utf-8').read()

# Find the analyze_broker_date function and fix the date handling
old_fn = "    if not date_str:\n        date_str = input('  Enter date (YYYY-MM-DD or DD/MM/YYYY): ').strip()"
new_fn = "    if not date_str or date_str.lower() == 'prompt':\n        date_str = None"

if old_fn in src:
    src = src.replace(old_fn, new_fn)
    print("Fixed scanner: 'prompt' treated as None → show dates then ask")
else:
    # Try to find the actual text
    idx = src.find('def analyze_broker_date')
    print(f"WARNING: pattern not found. Function start:")
    print(src[idx:idx+600])

open('nepse_scanner.py', 'w', encoding='utf-8').write(src)

# ── Verify ──
src2 = open('nepse_scanner.py', encoding='utf-8').read()
try:
    ast.parse(src2)
    mod = types.ModuleType('t')
    exec(compile(src2[:src2.rfind('\nif __name__')], 'nepse_scanner.py', 'exec'), mod.__dict__)
    fns = [x for x in dir(mod) if callable(getattr(mod,x)) and not x.startswith('__')]
    print(f"Syntax OK — {len(fns)} functions")
except Exception as e:
    print(f"ERROR: {e}")
    import shutil
    shutil.copy('_backups/nepse_scanner_pre_bdarg.py', 'nepse_scanner.py')
    print("Backup restored")
