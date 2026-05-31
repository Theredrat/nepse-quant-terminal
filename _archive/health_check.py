import ast, types
from pathlib import Path

src = open('nepse_scanner.py', encoding='utf-8').read()

try:
    ast.parse(src)
    syntax_ok = True
except SyntaxError as e:
    syntax_ok = False
    print(f'SYNTAX ERROR: {e}')

mod = types.ModuleType('t')
exec(compile(src[:src.rfind('\nif __name__')], 'nepse_scanner.py', 'exec'), mod.__dict__)
fns = [x for x in dir(mod) if callable(getattr(mod, x)) and not x.startswith('__')]

print('=' * 50)
print('  NEPSE SCANNER HEALTH CHECK')
print('=' * 50)
print(f'  Syntax: {"OK" if syntax_ok else "ERROR"}')
print(f'  Functions: {len(fns)}')
print()

print('=== FEATURES ===')
checks = [
    ('RS scan',              'analyze_rs'),
    ('Why engine',           'analyze_why'),
    ('Broker logger',        'log_broker_activity'),
    ('Broker story',         'get_broker_story'),
    ('5d verdict',           'five_day_verdict'),
    ('10d verdict',          'ten_day_verdict'),
    ('20d verdict',          'twenty_day_verdict'),
    ('Reversal alert',       'FIRST BUY after distribution'),
    ('Heatmap',              'analyze_heatmap'),
    ('Week52',               'analyze_week52'),
    ('Sector trend',         'analyze_sector_trend'),
    ('Power sell',           'analyze_power_sell'),
    ('Broker RS',            'analyze_broker_rs'),
    ('Portfolio',            'analyze_portfolio'),
    ('Value screen',         'analyze_value'),
    ('Signal tracker',       'signal_tracker.py'),
    ('Dashboard',            'dashboard_tui.py'),
    ('Alerts',               'nepse_alerts.py'),
    ('DB',                   'nepse_market_data.db'),
    ('Launch menu',          'launch_nepse.bat'),
]
all_ok = True
for name, key in checks:
    found = key in src or Path(key).exists()
    status = 'OK  ' if found else 'MISS'
    if not found:
        all_ok = False
    print(f'  {status}  {name}')

print()
print('=== ROOT FILES ===')
for f in sorted(Path('.').iterdir()):
    if f.is_file():
        size = f.stat().st_size
        print(f'  {f.name:<45} {size:>10,} bytes')

print()
print('=== ARCHIVE FOLDERS ===')
for folder in ['_backups', '_data', '_archive']:
    p = Path(folder)
    if p.exists():
        files = list(p.iterdir())
        print(f'  {folder}/  ({len(files)} files)')
    else:
        print(f'  {folder}/  (not found)')

print()
print('=== SUMMARY ===')
if syntax_ok and all_ok:
    print('  ALL SYSTEMS GO — every feature intact')
else:
    print('  ISSUES FOUND — check MISS items above')
