import sqlite3

conn = sqlite3.connect('nepse_market_data.db')

query = """
    SELECT 
        sp.symbol,
        MIN(sp.date) as list_date,
        MAX(sp.date) as last_date,
        COUNT(DISTINCT sp.date) as trading_days,
        (SELECT close FROM stock_prices WHERE symbol=sp.symbol ORDER BY date ASC LIMIT 1) as list_price,
        (SELECT MAX(close) FROM stock_prices WHERE symbol=sp.symbol) as ath,
        (SELECT date FROM stock_prices WHERE symbol=sp.symbol ORDER BY close DESC LIMIT 1) as ath_date,
        (SELECT close FROM stock_prices WHERE symbol=sp.symbol ORDER BY date DESC LIMIT 1) as cur_price
    FROM stock_prices sp
    INNER JOIN companies c ON sp.symbol = c.symbol
    WHERE c.sector IN (
        'Commercial Banks', 'Development Banks', 'Finance',
        'Hotels And Tourism', 'Hydro Power', 'Investment',
        'Life Insurance', 'Manufacturing And Processing',
        'Microfinance', 'Non Life Insurance', 'Others', 'Tradings'
    )
    GROUP BY sp.symbol
    HAVING MIN(sp.date) >= '2022-01-01'
    AND COUNT(DISTINCT sp.date) >= 30
    ORDER BY MIN(sp.date) DESC
"""

rows = conn.execute(query).fetchall()

print(f"Found {len(rows)} IPO stocks with 30+ trading days since 2022")
print()
print(f"{'Symbol':<12} {'Listed':<12} {'Days':<6} {'List Rs':<10} {'ATH Rs':<10} {'ATH Date':<12} {'Now Rs':<10} {'From List%':<12} {'From ATH%':<10}")
print('-'*110)

for r in rows:
    sym, list_date, last_date, days, list_price, ath, ath_date, cur = r
    if not list_price or not cur or list_price == 0:
        continue
    from_list = (cur - list_price) / list_price * 100
    from_ath  = (cur - ath) / ath * 100 if ath else 0
    print(f"{sym:<12} {list_date:<12} {days:<6} {list_price:<10.0f} {ath:<10.0f} {str(ath_date):<12} {cur:<10.0f} {from_list:<+12.1f} {from_ath:<+10.1f}")

conn.close()
