import sqlite3
conn = sqlite3.connect('nepse_market_data.db')
import pandas as pd

print('=== Tables with broker/floorsheet data ===')
import sqlite3
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
for t in tables:
    cur.execute(f'SELECT COUNT(*) FROM {t}')
    count = cur.fetchone()[0]
    if count > 0:
        cur.execute(f'SELECT * FROM {t} LIMIT 1')
        cols = [d[0] for d in cur.description]
        print(f'\n{t}: {count} rows')
        print(f'  columns: {cols}')

conn.close()
