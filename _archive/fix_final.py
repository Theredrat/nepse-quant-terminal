import re, shutil, ast
from pathlib import Path

print("=" * 55)
print("STEP 1 — Diagnose issues")
print("=" * 55)

src = open('nepse_scanner.py', encoding='utf-8').read()
bat = open('launch_nepse.bat', encoding='utf-8').read()

# Check REVERSAL
idx = src.lower().find('reversal')
if idx >= 0:
    print(f"REVERSAL found: {repr(src[idx:idx+60])}")
else:
    print("REVERSAL: NOT FOUND in scanner")

# Check 17c bat handler
idx2 = bat.find('17c')
print(f"\n17c bat context:")
print(repr(bat[idx2-30:idx2+250]) if idx2 >= 0 else "NOT FOUND")

print("\n" + "=" * 55)
print("STEP 2 — Fix CUSTOM_BROKERDATE in bat")
print("=" * 55)

# Back up bat
shutil.copy('launch_nepse.bat', '_backups/launch_nepse_pre_final.bat')
print("Backup created: _backups/launch_nepse_pre_final.bat")

# Find what pattern 17c currently uses
if 'CUSTOM_BROKERDATE' not in bat:
    # Find the 17c block and see what it does
    idx3 = bat.find('"17c"')
    if idx3 < 0:
        idx3 = bat.find("'17c'")
    print(f"17c handler: {repr(bat[idx3:idx3+200]) if idx3 >= 0 else 'NOT FOUND'}")

    # Add CUSTOM_BROKERDATE label using same pattern as CUSTOM_FLOOR
    # Find CUSTOM_FLOOR for reference
    idx4 = bat.find(':CUSTOM_FLOOR')
    print(f"\nCUSTOM_FLOOR pattern: {repr(bat[idx4:idx4+120])}")

    # Build the label — same style as CUSTOM_FLOOR
    new_label = (
        '\n:CUSTOM_BROKERDATE\n'
        'set /p symbol=  Enter stock symbol (e.g. CHCL):\n'
        'python nepse_scanner.py --broker-date %symbol%\n'
        'goto AGAIN\n'
    )

    # Wire 17c to goto CUSTOM_BROKERDATE
    # Find current 17c handler and replace it
    # Try inline block style first
    inline = 'if "%choice%"=="17c"'
    idx5 = bat.find(inline)
    if idx5 >= 0:
        # Find end of this if block
        end = bat.find('\nif "%choice%"', idx5 + 1)
        old_block = bat[idx5:end]
        new_block = 'if "%choice%"=="17c" goto CUSTOM_BROKERDATE'
        bat = bat[:idx5] + new_block + bat[end:]
        print(f"\nReplaced inline 17c handler with goto")
    
    # Add label before :CUSTOM_FLOOR
    bat = bat.replace(':CUSTOM_FLOOR', new_label + ':CUSTOM_FLOOR', 1)
    print("Added :CUSTOM_BROKERDATE label")

    open('launch_nepse.bat', 'w', encoding='utf-8').write(bat)
    print("launch_nepse.bat saved")
else:
    print("CUSTOM_BROKERDATE already present — no change needed")

print("\n" + "=" * 55)
print("STEP 3 — Verify bat")
print("=" * 55)
bat2 = open('launch_nepse.bat', encoding='utf-8').read()
print(f"CUSTOM_BROKERDATE: {'CUSTOM_BROKERDATE' in bat2}")
print(f"17c goto: {'goto CUSTOM_BROKERDATE' in bat2}")

print("\n" + "=" * 55)
print("STEP 4 — Verify scanner syntax")
print("=" * 55)
import ast as ast_mod, types
try:
    ast_mod.parse(src)
    mod = types.ModuleType('t')
    exec(compile(src[:src.rfind('\nif __name__')], 'nepse_scanner.py', 'exec'), mod.__dict__)
    fns = [x for x in dir(mod) if callable(getattr(mod,x)) and not x.startswith('__')]
    print(f"Syntax OK — {len(fns)} functions")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 55)
print("STEP 5 — Clean up leftover files from root")
print("=" * 55)
to_archive = [
    'fix_17c_bat.py', 'fix_17c_order.py', 'fix_menu_17b.py',
    'patch_17c_date_lookup.py', 'patch_17c_show_dates.py',
    'full_health_check.py',
]
to_backups = [
    'launch_nepse_pre_17b.bat', 'launch_nepse_pre_17b2.bat',
    'launch_nepse_pre_17b3.bat', 'launch_nepse_pre_17c.bat',
    'launch_nepse_pre_17c2.bat',
    'nepse_scanner_pre_17c.py', 'nepse_scanner_pre_17c_dates.py',
    'nepse_scanner_pre_17c_order.py',
]
for f in to_archive:
    if Path(f).exists():
        shutil.move(f, f'_archive/{f}')
        print(f"  archived: {f}")
for f in to_backups:
    if Path(f).exists():
        shutil.move(f, f'_backups/{f}')
        print(f"  backed up: {f}")

print("\nRoot files remaining:")
for f in sorted(Path('.').iterdir()):
    if f.is_file():
        print(f"  {f.name}")

print("\n" + "=" * 55)
print("DONE")
print("=" * 55)
