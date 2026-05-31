import sqlite3, json
from pathlib import Path

db = sqlite3.connect('nepse_market_data.db')
cur = db.cursor()
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('=== DATABASE TABLES ===')
for t in tables:
    count = cur.execute(f'SELECT COUNT(*) FROM {t[0]}').fetchone()[0]
    print(f'  {t[0]:35} {count:10,} rows')

print()
print('=== DATA FILES ===')
for f in Path('_data').iterdir():
    print(f'  {f.name:40} {f.stat().st_size:10,} bytes')

print()
sig = json.load(open('signal_log.json', encoding='utf-8'))
print(f'=== SIGNAL LOG: {len(sig)} signals ===')

print()
print('=== CACHE FILES ===')
for f in sorted(Path('_data').glob('signals_cache*.json')):
    data = json.load(open(f))
    print(f'  {f.name}: {len(data)} signals')

print()
total = sum(f.stat().st_size for f in Path('.').iterdir() if f.is_file())
print(f'=== ROOT FOLDER: {total/1024/1024:.1f} MB total ===')
