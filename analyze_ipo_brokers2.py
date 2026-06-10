import sqlite3

conn = sqlite3.connect('nepse_market_data.db')

print("="*80)
print("ANALYSIS 2 — Which Brokers Accumulate IPO Stocks in First 60 Days?")
print("="*80)

targets = ['RSML','SABBL','SYPNL','SAIL','JHAPA','SWASTIK','SAGAR',
           'OMPL','CREST','NMIC','GMLI','KBSH','ANLB','DLBS','MKCL']

broker_score = {}  # track which brokers appear most across all IPOs

for sym in targets:
    list_date = conn.execute(
        "SELECT MIN(date) FROM stock_prices WHERE symbol=?", (sym,)
    ).fetchone()[0]
    if not list_date:
        continue

    brokers = conn.execute("""
        SELECT broker_id, broker_name,
               SUM(buy_val) as total_buy,
               SUM(sell_val) as total_sell,
               SUM(net_val) as net_buy,
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

    print(f"\n{sym} (listed {list_date}) — Top accumulators first 60 days:")
    print(f"  {'Broker':<6} {'Name':<40} {'Net Rs M':<12} {'Days':<6}")
    for b in brokers:
        bid, bname, tbuy, tsell, net, days = b
        print(f"  {bid:<6} {bname[:38]:<40} {net/1e6:<12.2f} {days:<6}")
        # count broker appearances
        broker_score[bid] = broker_score.get(bid, 0) + 1

print()
print("="*80)
print("BROKER LEADERBOARD — Most frequent IPO accumulators:")
print("="*80)
sorted_brokers = sorted(broker_score.items(), key=lambda x: x[1], reverse=True)
for bid, count in sorted_brokers[:15]:
    name = conn.execute(
        "SELECT DISTINCT broker_name FROM broker_activity WHERE broker_id=? LIMIT 1", (bid,)
    ).fetchone()
    bname = name[0] if name else 'Unknown'
    print(f"  Broker {bid:<5} {bname[:40]:<42} appeared in {count}/{len(targets)} IPOs")

conn.close()
