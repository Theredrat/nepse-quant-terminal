import sqlite3
conn = sqlite3.connect("nepse_market_data.db")
c = conn.cursor()
c.execute("SELECT * FROM watchlist_items ORDER BY symbol")
for r in c.fetchall():
    print(r)
conn.close()
