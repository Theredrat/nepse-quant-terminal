import sqlite3
conn = sqlite3.connect('nepse_market_data.db')
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print('=== TABLES ===')
for row in cur.fetchall():
    print(' ', row[0])

for tbl in ['stock_prices', 'companies', 'daily_prices', 'securities']:
    try:
        cur.execute(f'SELECT * FROM {tbl} LIMIT 1')
        cols = [d[0] for d in cur.description]
        cur.execute(f'SELECT COUNT(*) FROM {tbl}')
        count = cur.fetchone()[0]
        print(f'\n{tbl}: {count} rows, columns: {cols}')
    except Exception as e:
        print(f'\n{tbl}: NOT FOUND - {e}')

conn.close()
