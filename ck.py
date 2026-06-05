import sqlite3
conn = sqlite3.connect('nepse_market_data.db')
dates = conn.execute('SELECT DISTINCT date FROM broker_activity ORDER BY date DESC LIMIT 5').fetchall()
print('Latest dates in broker_activity:')
for d in dates:
    print(' ', d[0])
conn.close()
