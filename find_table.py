import sqlite3
conn = sqlite3.connect("nepse_market_data.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
for t in tables:
    try:
        c.execute(f"SELECT symbol, close, date FROM {t} WHERE symbol='NICL' ORDER BY date DESC LIMIT 1")
        row = c.fetchone()
        if row:
            print(f"{t}: {row}")
    except:
        pass
conn.close()
