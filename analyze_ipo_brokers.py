import sqlite3

conn = sqlite3.connect('nepse_market_data.db')

# ANALYSIS 2 - Broker behavior in first 60 days after listing
# Which brokers accumulate most in IPO stocks?

print("="*80)
print("ANALYSIS 2 — Which Brokers Accumulate IPO Stocks?")
print("="*80)

# Get recently listed stocks with good runs
targets = ['RSML','SABBL','SYPNL','SAIL','JHAPA','SWASTIK','SAGAR','OMPL','CREST','NMIC','GMLI','KBSH','ANLB','DLBS','MKCL']

for sym in targets:
    # Get listing date
    list_date = conn.execute(
        "SELECT MIN(date) FROM stock_prices WHERE symbol=?", (sym,)
    ).fetchone()[0]
    
    if not list_date:
        continue
    
    # Get broker activity in first 60 days
    brokers = conn.execute("""
        SELECT broker_id, 
               SUM(buy_value) as total_buy,
               SUM(sell_value) as total_sell,
               SUM(buy_value) - SUM(sell_value) as net_buy,
               COUNT(DISTINCT date) as active_days
        FROM broker_activity
        WHERE symbol=? AND date >= ? AND date <= date(?, '+60 days')
        GROUP BY broker_id
        HAVING net_buy > 0
        ORDER BY net_buy DESC
        LIMIT 5
    """, (sym, list_date, list_date)).fetchall()
    
    if not brokers:
        continue
        
    print(f"\n{sym} (listed {list_date}) — Top accumulators in first 60 days:")
    print(f"  {'Broker':<10} {'Net Buy Rs M':<15} {'Buy Days':<10}")
    for b in brokers:
        bid, tbuy, tsell, net, days = b
        print(f"  Broker {bid:<5} {net/1e6:<15.2f} {days:<10}")

conn.close()
