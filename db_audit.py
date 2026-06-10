import sqlite3
conn = sqlite3.connect('nepse_market_data.db')
c = conn.cursor()
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
for t in tables:
    try:
        r = c.execute(f'SELECT COUNT(*), MIN(date), MAX(date) FROM {t}').fetchone()
        print(f'{t}: {r[0]} rows | {r[1]} to {r[2]}')
    except:
        try:
            r = c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()
            print(f'{t}: {r[0]} rows | (no date column)')
        except Exception as e:
            print(f'{t}: ERROR - {e}')
conn.close()
