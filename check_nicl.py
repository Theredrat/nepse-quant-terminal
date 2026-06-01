import sqlite3
conn = sqlite3.connect("nepse_market_data.db")
c = conn.cursor()
c.execute("SELECT COUNT(*), SUM(hold_vol), MAX(hold_vol) FROM broker_holdings WHERE symbol='NICL'")
print("Count, Sum, Max:", c.fetchone())
c.execute("SELECT broker_id, broker_name, hold_vol FROM broker_holdings WHERE symbol='NICL' ORDER BY hold_vol DESC LIMIT 10")
for r in c.fetchall():
    print(r)
conn.close()
