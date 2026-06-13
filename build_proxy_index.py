import sqlite3
from datetime import datetime, timezone

db = sqlite3.connect('nepse_market_data.db')
cur = db.cursor()

print('Calculating proxy NEPSE index...')

# Get daily OHLCV aggregates - equity only
cur.execute('''
    SELECT date,
           AVG(open) as o,
           AVG(high) as h,
           AVG(low) as l,
           AVG(close) as c,
           SUM(volume) as v
    FROM stock_prices
    WHERE close > 0
    AND volume > 0
    AND symbol NOT LIKE '%/%'
    GROUP BY date
    ORDER BY date
''')
rows = cur.fetchall()
print('Days to process: ' + str(len(rows)))

# Normalize to start at 1000 (like NEPSE index base)
base_close = rows[0][4]
scale = 1000.0 / base_close

now_utc = datetime.now(timezone.utc).isoformat()

# Clear existing proxy data
cur.execute("DELETE FROM benchmark_index_history WHERE source = 'proxy'")

# Insert normalized index values
insert_count = 0
for row in rows:
    date, o, h, l, c, v = row
    norm_o = round(o * scale, 2)
    norm_h = round(h * scale, 2)
    norm_l = round(l * scale, 2)
    norm_c = round(c * scale, 2)
    cur.execute('''
        INSERT OR REPLACE INTO benchmark_index_history
        (benchmark, date, open, high, low, close, volume, source, fetched_at_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('NEPSE_PROXY', date, norm_o, norm_h, norm_l, norm_c, v, 'proxy', now_utc))
    insert_count += 1

db.commit()
print('Inserted: ' + str(insert_count) + ' rows')

# Verify
cur.execute("SELECT MIN(date), MAX(date), COUNT(*) FROM benchmark_index_history WHERE benchmark = 'NEPSE_PROXY'")
r = cur.fetchone()
print('Verified - range: ' + str(r[0]) + ' to ' + str(r[1]) + ', rows: ' + str(r[2]))

# Show last 5 values
cur.execute("SELECT date, close FROM benchmark_index_history WHERE benchmark = 'NEPSE_PROXY' ORDER BY date DESC LIMIT 5")
print('Last 5 index values:')
for r in cur.fetchall():
    print('  ' + r[0] + ' | ' + str(r[1]))

db.close()
