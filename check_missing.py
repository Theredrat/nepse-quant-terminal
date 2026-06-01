import sqlite3
conn = sqlite3.connect("nepse_market_data.db")
c = conn.cursor()
c.execute("SELECT DISTINCT date FROM stock_prices ORDER BY date DESC LIMIT 10")
for r in c.fetchall():
    print(r[0])
conn.close()
