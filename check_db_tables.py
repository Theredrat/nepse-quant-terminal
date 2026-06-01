import sqlite3
conn = sqlite3.connect("nepse_market_data.db")
c = conn.cursor()

# List all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in c.fetchall()]
print("All tables:", tables)

# Check which tables have symbol + close columns
for t in tables:
    try:
        c.execute(f"SELECT symbol, close FROM {t} LIMIT 1")
        row = c.fetchone()
        if row:
            print(f"  {t}: symbol={row[0]}, close={row[1]}")
    except:
        pass

conn.close()
