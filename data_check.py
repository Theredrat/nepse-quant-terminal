# -*- coding: utf-8 -*-
import sqlite3, os, datetime

def data_health_check():
    conn = sqlite3.connect("nepse_market_data.db")
    today = datetime.date.today().isoformat()
    
    print("=" * 55)
    print("  NEPSE DATA HEALTH CHECK")
    print("  " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 55)
    
    # Stock prices
    print("\n[1] STOCK PRICES (OHLCV)")
    rows = conn.execute("SELECT date, COUNT(DISTINCT symbol) FROM stock_prices GROUP BY date ORDER BY date DESC LIMIT 7").fetchall()
    for date, count in rows:
        status = "OK" if count >= 300 else "PARTIAL"
        flag = " <-- TODAY" if date == today else ""
        print(f"  {date}  {count:>4} symbols  [{status}]{flag}")
    total = conn.execute("SELECT COUNT(DISTINCT date) FROM stock_prices").fetchone()[0]
    print(f"  Total: {total} trading days in DB")

    # Broker activity
    print("\n[2] BROKER ACTIVITY")
    rows = conn.execute("SELECT date, COUNT(*) FROM broker_activity GROUP BY date ORDER BY date DESC LIMIT 7").fetchall()
    for date, count in rows:
        status = "OK" if count >= 10000 else "PARTIAL"
        flag = " <-- TODAY" if date == today else ""
        print(f"  {date}  {count:>6} rows  [{status}]{flag}")

    # Last auto_daily run
    print("\n[3] LAST PIPELINE RUN")
    log = r"logs\auto_daily.log"
    if os.path.exists(log):
        lines = open(log, encoding="utf-8", errors="replace").readlines()
        for l in lines[-5:]:
            print(" ", l.strip())
    
    print("\n" + "=" * 55)
    conn.close()

data_health_check()
