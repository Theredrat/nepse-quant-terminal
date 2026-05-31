import sys
sys.path.insert(0, '.')
import types, pandas as pd

src = open('nepse_scanner.py', encoding='utf-8').read()
mod = types.ModuleType('t')
exec(compile(src[:src.find('\nif __name__')], 'nepse_scanner.py', 'exec'), mod.__dict__)

n = mod.init_nepse()
print('Fetching small floorsheet sample...')
fs = mod.get_full_floorsheet(n)
if fs is not None and not fs.empty:
    print(f'Columns: {fs.columns.tolist()}')
    print(f'Rows: {len(fs)}')
    print(f'Sample:\n{fs.head(3).to_string()}')
    print(f'\nDtypes:\n{fs.dtypes}')
else:
    print('Empty or None')
