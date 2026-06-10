import sqlite3
from datetime import date, timedelta

conn = sqlite3.connect('nepse_market_data.db')

print("="*80)
print("UNLOCK STATUS — All IPO Stocks")
print("="*80)

stocks = conn.execute("""
    SELECT 
        sp.symbol,
        MIN(sp.date) as list_date,
        c.sector,
        f.public_shares,
        f.promoter_pct,
        u.unlock_date
    FROM stock_prices sp
    INNER JOIN companies c ON sp.symbol = c.symbol
    LEFT JOIN fundamentals f ON sp.symbol = f.symbol
    LEFT JOIN unlock_dates u ON sp.symbol = u.symbol
    WHERE c.sector IN (
        'Commercial Banks','Development Banks','Finance',
        'Hotels And Tourism','Hydro Power','Investment',
        'Life Insurance','Manufacturing And Processing',
        'Microfinance','Non Life Insurance','Others','Tradings'
    )
    GROUP BY sp.symbol
    HAVING MIN(sp.date) >= '2022-01-01'
    AND COUNT(DISTINCT sp.date) >= 30
    ORDER BY c.sector, MIN(sp.date)
""").fetchall()

today = date.today()

print(f"{'Symbol':<10} {'Listed':<12} {'Sector':<25} {'Public Shares':<15} {'Unlock Date':<14} {'Status':<20} {'Days Left'}")
print('-'*120)

for sym, list_date, sector, pub_shares, prom_pct, unlock_date in stocks:
    # Calculate unlock if missing
    if unlock_date:
        ud = date.fromisoformat(unlock_date)
        calculated = False
    else:
        # 3 years from listing
        ld = date.fromisoformat(list_date)
        ud = date(ld.year + 3, ld.month, ld.day)
        calculated = True

    days_left = (ud - today).days
    
    if days_left < 0:
        status = "🔓 UNLOCKED"
    elif days_left < 90:
        status = "🔴 DANGER"
    elif days_left < 180:
        status = "🟡 WARNING"
    elif days_left < 365:
        status = "🟠 WATCH"
    else:
        status = "✅ SAFE"

    calc_str = "*" if calculated else ""
    pub_str = f"{pub_shares:,.0f}" if pub_shares else "N/A"
    
    print(f"{sym:<10} {list_date:<12} {sector[:23]:<25} {pub_str:<15} {str(ud)+calc_str:<14} {status:<20} {days_left}")

conn.close()
